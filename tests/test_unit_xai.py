"""
test_unit_xai.py  –  UNIT TESTS for Explainable AI functions in server.py

Functions under test:
    • extract_xai_features(detections, crop_name)
    • compute_spray_angle(features)
    • evaluate_weather_suitability(weather_data)
    • compute_feature_importance(features, spray, weather)

These are deterministic, pure-logic functions with no I/O.
"""

import pytest
import server


# ======================================================================
# Phase 1 — UNIT TESTS:  XAI Feature Extraction
# ======================================================================


class TestExtractXAIFeatures:
    """Verify feature extraction from detection lists."""

    @pytest.mark.unit
    def test_counts_weeds_correctly(self, sample_weed_detections):
        """TC-X01: Total weed count matches detection list."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        assert features["totalWeedCount"] == 3

    @pytest.mark.unit
    def test_counts_crops_correctly(self, sample_weed_detections):
        """TC-X02: Total crop count matches detection list."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        assert features["totalCropCount"] == 1

    @pytest.mark.unit
    def test_weed_species_list(self, sample_weed_detections):
        """TC-X03: weedSpecies lists each unique species with count and avg confidence."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        species_names = [s["name"] for s in features["weedSpecies"]]
        assert "waterhemp" in species_names
        assert "morningglory" in species_names
        assert "ragweed" in species_names

    @pytest.mark.unit
    def test_avg_confidence_range(self, sample_weed_detections):
        """TC-X04: Average confidence is between 0 and 1."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        assert 0 <= features["avgConfidence"] <= 1

    @pytest.mark.unit
    def test_weed_density_range(self, sample_weed_detections):
        """TC-X05: Weed density is normalized between 0 and 1."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        assert 0 <= features["weedDensity"] <= 1.0

    @pytest.mark.unit
    def test_weed_crop_ratio(self, sample_weed_detections):
        """TC-X06: Weed:crop ratio = 3 weeds / 1 crop = 3.0."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        assert features["weedCropRatio"] == 3.0

    @pytest.mark.unit
    def test_spatial_distribution_valid(self, sample_weed_detections):
        """TC-X07: Spatial distribution is one of the expected values."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        assert features["spatialDistribution"] in [
            "clustered", "inter-row", "edge", "scattered"
        ]

    @pytest.mark.unit
    def test_dominant_region_keys(self, sample_weed_detections):
        """TC-X08: Dominant region has x and y keys between 0 and 1."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        assert "x" in features["dominantRegion"]
        assert "y" in features["dominantRegion"]
        assert 0 <= features["dominantRegion"]["x"] <= 1
        assert 0 <= features["dominantRegion"]["y"] <= 1

    @pytest.mark.unit
    def test_no_weeds_returns_zero_density(self, sample_no_weed_detections):
        """TC-X09: When no weeds detected, density and ratio are 0."""
        features = server.extract_xai_features(sample_no_weed_detections, "Wheat")
        assert features["totalWeedCount"] == 0
        assert features["weedDensity"] == 0
        assert features["weedCropRatio"] == 0

    @pytest.mark.unit
    def test_empty_detections(self):
        """TC-X10: Empty detection list returns safe defaults."""
        features = server.extract_xai_features([], "Wheat")
        assert features["totalWeedCount"] == 0
        assert features["totalCropCount"] == 0
        assert features["avgConfidence"] == 0
        assert features["weedSpecies"] == []


# ======================================================================
# Phase 1 — UNIT TESTS:  Spray Angle Computation
# ======================================================================


class TestComputeSprayAngle:
    """Verify spray angle, pattern, and nozzle recommendation logic."""

    @pytest.mark.unit
    def test_no_weeds_returns_spot_pattern(self):
        """TC-S01: No weeds → spot pattern, angle 0, no nozzle needed."""
        features = {
            "totalWeedCount": 0,
            "spatialDistribution": "scattered",
            "dominantRegion": {"x": 0.5, "y": 0.5},
        }
        result = server.compute_spray_angle(features)
        assert result["angle"] == 0
        assert result["pattern"] == "spot"
        assert result["confidence"] == 1.0

    @pytest.mark.unit
    def test_clustered_returns_directional(self):
        """TC-S02: Clustered weeds → directional pattern."""
        features = {
            "totalWeedCount": 5,
            "spatialDistribution": "clustered",
            "dominantRegion": {"x": 0.7, "y": 0.3},
        }
        result = server.compute_spray_angle(features)
        assert result["pattern"] == "directional"
        assert result["confidence"] == 0.85

    @pytest.mark.unit
    def test_interrow_returns_90_degrees(self):
        """TC-S03: Inter-row weeds → 90° perpendicular spray."""
        features = {
            "totalWeedCount": 4,
            "spatialDistribution": "inter-row",
            "dominantRegion": {"x": 0.5, "y": 0.5},
        }
        result = server.compute_spray_angle(features)
        assert result["angle"] == 90
        assert result["pattern"] == "inter-row"

    @pytest.mark.unit
    def test_edge_returns_directional(self):
        """TC-S04: Edge weeds → directional pattern."""
        features = {
            "totalWeedCount": 2,
            "spatialDistribution": "edge",
            "dominantRegion": {"x": 0.9, "y": 0.1},
        }
        result = server.compute_spray_angle(features)
        assert result["pattern"] == "directional"

    @pytest.mark.unit
    def test_scattered_returns_broadcast(self):
        """TC-S05: Scattered weeds → broadcast (360°) pattern."""
        features = {
            "totalWeedCount": 10,
            "spatialDistribution": "scattered",
            "dominantRegion": {"x": 0.5, "y": 0.5},
        }
        result = server.compute_spray_angle(features)
        assert result["angle"] == 360
        assert result["pattern"] == "broadcast"

    @pytest.mark.unit
    def test_nozzle_type_always_present(self):
        """TC-S06: Every result includes a nozzle type string."""
        features = {
            "totalWeedCount": 3,
            "spatialDistribution": "scattered",
            "dominantRegion": {"x": 0.4, "y": 0.6},
        }
        result = server.compute_spray_angle(features)
        assert isinstance(result["nozzleType"], str)
        assert len(result["nozzleType"]) > 0

    @pytest.mark.unit
    def test_reasoning_always_present(self):
        """TC-S07: Every result includes a reasoning explanation."""
        features = {
            "totalWeedCount": 1,
            "spatialDistribution": "clustered",
            "dominantRegion": {"x": 0.3, "y": 0.7},
        }
        result = server.compute_spray_angle(features)
        assert isinstance(result["reasoning"], str)
        assert len(result["reasoning"]) > 10


# ======================================================================
# Phase 1 — UNIT TESTS:  Weather Suitability Evaluation
# ======================================================================


class TestEvaluateWeatherSuitability:
    """Verify weather scoring logic for spray recommendations."""

    @pytest.mark.unit
    def test_ideal_weather_high_score(self, sample_weather_good):
        """TC-W01: Ideal weather (22°C, 5 km/h wind, 60% humidity) → score ≥ 80."""
        result = server.evaluate_weather_suitability(sample_weather_good)
        assert result["score"] >= 80
        assert result["canSpray"] is True

    @pytest.mark.unit
    def test_bad_weather_low_score(self, sample_weather_bad):
        """TC-W02: Bad weather (40°C, 30 km/h, 25% humidity, 75% rain) → score < 50."""
        result = server.evaluate_weather_suitability(sample_weather_bad)
        assert result["score"] < 50
        assert result["canSpray"] is False

    @pytest.mark.unit
    def test_none_weather_returns_defaults(self):
        """TC-W03: None weather data → default score of 50, canSpray True."""
        result = server.evaluate_weather_suitability(None)
        assert result["score"] == 50
        assert result["canSpray"] is True

    @pytest.mark.unit
    def test_extreme_cold(self):
        """TC-W04: Temperature < 5°C → significant penalty."""
        result = server.evaluate_weather_suitability({
            "temperature": 2, "windSpeed": 5, "windDirection": 0,
            "humidity": 60, "precipitation": 0,
        })
        assert result["temperature"]["suitable"] is False
        assert result["score"] < 80

    @pytest.mark.unit
    def test_extreme_wind(self):
        """TC-W05: Wind > 25 km/h → DO NOT SPRAY."""
        result = server.evaluate_weather_suitability({
            "temperature": 22, "windSpeed": 30, "windDirection": 0,
            "humidity": 60, "precipitation": 0,
        })
        assert result["wind"]["suitable"] is False
        assert result["score"] < 70

    @pytest.mark.unit
    def test_high_precipitation(self):
        """TC-W06: Rain probability > 60% → major penalty."""
        result = server.evaluate_weather_suitability({
            "temperature": 22, "windSpeed": 5, "windDirection": 0,
            "humidity": 60, "precipitation": 80,
        })
        assert result["precipitation"]["suitable"] is False
        assert result["score"] < 70

    @pytest.mark.unit
    def test_low_humidity(self):
        """TC-W07: Humidity < 30% → evaporation penalty."""
        result = server.evaluate_weather_suitability({
            "temperature": 22, "windSpeed": 5, "windDirection": 0,
            "humidity": 20, "precipitation": 0,
        })
        assert result["humidity"]["suitable"] is False

    @pytest.mark.unit
    def test_response_structure(self, sample_weather_good):
        """TC-W08: Response dict has all required keys."""
        result = server.evaluate_weather_suitability(sample_weather_good)
        required_keys = [
            "canSpray", "score", "temperature", "wind",
            "humidity", "precipitation", "overallReason"
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    @pytest.mark.unit
    def test_score_never_negative(self):
        """TC-W09: Score is clamped at 0 (never negative)."""
        result = server.evaluate_weather_suitability({
            "temperature": 50, "windSpeed": 40, "windDirection": 0,
            "humidity": 10, "precipitation": 100,
        })
        assert result["score"] >= 0


# ======================================================================
# Phase 1 — UNIT TESTS:  Feature Importance Computation
# ======================================================================


class TestComputeFeatureImportance:
    """Verify that feature importance scores are valid."""

    @pytest.mark.unit
    def test_returns_list(self, sample_weed_detections):
        """TC-FI01: compute_feature_importance returns a list."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        spray = server.compute_spray_angle(features)
        weather = server.evaluate_weather_suitability(None)
        importance = server.compute_feature_importance(features, spray, weather)
        assert isinstance(importance, list)
        assert len(importance) > 0

    @pytest.mark.unit
    def test_importance_scores_in_range(self, sample_weed_detections):
        """TC-FI02: Every importance score is between 0 and 1."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        spray = server.compute_spray_angle(features)
        weather = server.evaluate_weather_suitability(None)
        importance = server.compute_feature_importance(features, spray, weather)
        for item in importance:
            assert 0 <= item["importance"] <= 1.0, f"{item['feature']} out of range"

    @pytest.mark.unit
    def test_sorted_by_importance_descending(self, sample_weed_detections):
        """TC-FI03: Importance list is sorted descending."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        spray = server.compute_spray_angle(features)
        weather = server.evaluate_weather_suitability(None)
        importance = server.compute_feature_importance(features, spray, weather)
        scores = [item["importance"] for item in importance]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.unit
    def test_expected_feature_names(self, sample_weed_detections):
        """TC-FI04: All six expected feature names are present."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        spray = server.compute_spray_angle(features)
        weather = server.evaluate_weather_suitability(None)
        importance = server.compute_feature_importance(features, spray, weather)
        names = {item["feature"] for item in importance}
        expected = {
            "Weed Count", "Detection Confidence", "Spatial Distribution",
            "Weed Density", "Species Diversity", "Weather Risk"
        }
        assert names == expected

    @pytest.mark.unit
    def test_each_has_description(self, sample_weed_detections):
        """TC-FI05: Every importance item has a non-empty description."""
        features = server.extract_xai_features(sample_weed_detections, "Wheat")
        spray = server.compute_spray_angle(features)
        weather = server.evaluate_weather_suitability(None)
        importance = server.compute_feature_importance(features, spray, weather)
        for item in importance:
            assert isinstance(item["description"], str)
            assert len(item["description"]) > 5
