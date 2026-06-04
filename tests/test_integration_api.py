"""
test_integration_api.py  –  INTEGRATION TESTS for Flask API endpoints

These tests use Flask's built-in test client to verify that
multiple components (routing → validation → logic → JSON response)
work correctly together.

Endpoints under test:
    GET  /health
    GET  /status
    POST /analyze
    POST /xai-explain
    POST /identify-crop
    POST /get-treatment
"""

import json
import base64
import pytest
import numpy as np
import cv2
from unittest.mock import patch, MagicMock
import server


# ======================================================================
# Phase 2 — INTEGRATION TESTS
# ======================================================================


# ------------------------------------------------------------------
# TC-I01 to TC-I03:  /health  and  /status  endpoints
# ------------------------------------------------------------------
class TestHealthAndStatus:
    """Verify the basic health-check and status endpoints."""

    @pytest.mark.integration
    def test_health_returns_ok(self, client):
        """TC-I01: GET /health → 200, {"status": "ok"}."""
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"

    @pytest.mark.integration
    def test_status_returns_running(self, client):
        """TC-I02: GET /status → 200, includes device and model info."""
        resp = client.get("/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "running"
        assert "device" in data
        assert "model" in data

    @pytest.mark.integration
    def test_status_version_field(self, client):
        """TC-I03: /status response includes version."""
        resp = client.get("/status")
        data = resp.get_json()
        assert "version" in data


# ------------------------------------------------------------------
# TC-I04 to TC-I12:  /analyze  endpoint
# ------------------------------------------------------------------
class TestAnalyzeEndpoint:
    """Integration tests for the main /analyze endpoint."""

    def _make_test_image_base64(self):
        """Create a small base64-encoded test image."""
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        # Draw a green rectangle (simulates a plant)
        cv2.rectangle(img, (20, 20), (80, 80), (0, 255, 0), -1)
        _, buffer = cv2.imencode(".jpg", img)
        return base64.b64encode(buffer).decode("utf-8")

    @pytest.mark.integration
    def test_analyze_no_body(self, client):
        """TC-I04: POST /analyze with no body → 400 error."""
        resp = client.post("/analyze", content_type="application/json")
        assert resp.status_code == 400 or resp.status_code == 500

    @pytest.mark.integration
    def test_analyze_no_image(self, client):
        """TC-I05: POST /analyze with JSON but missing image field → 400."""
        resp = client.post(
            "/analyze",
            data=json.dumps({"cropName": "Wheat"}),
            content_type="application/json",
        )
        assert resp.status_code == 400
        data = resp.get_json()
        assert "error" in data

    @pytest.mark.integration
    def test_analyze_invalid_base64(self, client):
        """TC-I06: POST /analyze with invalid base64 → 400."""
        resp = client.post(
            "/analyze",
            data=json.dumps({"image": "not_valid_base64!!!"}),
            content_type="application/json",
        )
        # Depending on how b64 fails, may be 400 or 500
        assert resp.status_code in (400, 500)

    @pytest.mark.integration
    @patch.object(server, "detect_with_roboflow")
    def test_analyze_valid_image_returns_dual_model(self, mock_roboflow, client):
        """TC-I07: Valid image → dualModel response with YOLO + Roboflow."""
        # Mock Roboflow to return empty results (no API call needed)
        mock_roboflow.return_value = {
            "detections": [],
            "weed_count": 0,
            "crop_count": 0,
            "weed_types": [],
            "identified_crop": None,
        }

        img_b64 = self._make_test_image_base64()
        resp = client.post(
            "/analyze",
            data=json.dumps({"image": img_b64, "cropName": "Wheat"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["dualModel"] is True
        assert "yolo" in data
        assert "roboflow" in data

    @pytest.mark.integration
    @patch.object(server, "detect_with_roboflow")
    def test_analyze_returns_yolo_fields(self, mock_roboflow, client):
        """TC-I08: YOLO section contains required fields."""
        mock_roboflow.return_value = {
            "detections": [], "weed_count": 0,
            "crop_count": 0, "weed_types": [], "identified_crop": None,
        }
        img_b64 = self._make_test_image_base64()
        resp = client.post(
            "/analyze",
            data=json.dumps({"image": img_b64, "cropName": "Wheat"}),
            content_type="application/json",
        )
        data = resp.get_json()
        yolo = data["yolo"]
        assert "detections" in yolo
        assert "count" in yolo
        assert "weedCount" in yolo
        assert "cropCount" in yolo
        assert "inferenceTime" in yolo

    @pytest.mark.integration
    @patch.object(server, "detect_with_roboflow")
    def test_analyze_default_crop_is_wheat(self, mock_roboflow, client):
        """TC-I09: When cropName is omitted, defaults to 'Wheat'."""
        mock_roboflow.return_value = {
            "detections": [], "weed_count": 0,
            "crop_count": 0, "weed_types": [], "identified_crop": None,
        }
        img_b64 = self._make_test_image_base64()
        resp = client.post(
            "/analyze",
            data=json.dumps({"image": img_b64}),
            content_type="application/json",
        )
        data = resp.get_json()
        assert data["cropType"] == "Wheat"

    @pytest.mark.integration
    @patch.object(server, "detect_with_roboflow")
    def test_analyze_roboflow_error_handled(self, mock_roboflow, client):
        """TC-I10: Roboflow API error is gracefully handled in response."""
        mock_roboflow.return_value = {"error": "API key not configured"}
        img_b64 = self._make_test_image_base64()
        resp = client.post(
            "/analyze",
            data=json.dumps({"image": img_b64, "cropName": "Wheat"}),
            content_type="application/json",
        )
        assert resp.status_code == 200  # Still succeeds with YOLO-only
        data = resp.get_json()
        assert data["roboflow"]["error"] is not None

    @pytest.mark.integration
    @patch.object(server, "detect_with_roboflow")
    def test_analyze_includes_total_inference_time(self, mock_roboflow, client):
        """TC-I11: Response includes totalInferenceTime."""
        mock_roboflow.return_value = {
            "detections": [], "weed_count": 0,
            "crop_count": 0, "weed_types": [], "identified_crop": None,
        }
        img_b64 = self._make_test_image_base64()
        resp = client.post(
            "/analyze",
            data=json.dumps({"image": img_b64}),
            content_type="application/json",
        )
        data = resp.get_json()
        assert "totalInferenceTime" in data
        assert isinstance(data["totalInferenceTime"], (int, float))

    @pytest.mark.integration
    @patch.object(server, "detect_with_roboflow")
    def test_analyze_crop_name_trim(self, mock_roboflow, client):
        """TC-I12: cropName is whitespace-trimmed."""
        mock_roboflow.return_value = {
            "detections": [], "weed_count": 0,
            "crop_count": 0, "weed_types": [], "identified_crop": None,
        }
        img_b64 = self._make_test_image_base64()
        resp = client.post(
            "/analyze",
            data=json.dumps({"image": img_b64, "cropName": "  Corn  "}),
            content_type="application/json",
        )
        data = resp.get_json()
        assert data["cropType"] == "Corn"


# ------------------------------------------------------------------
# TC-I13 to TC-I18:  /xai-explain  endpoint
# ------------------------------------------------------------------
class TestXAIExplainEndpoint:
    """Integration tests for the XAI explainability endpoint."""

    @pytest.mark.integration
    def test_xai_no_body(self, client):
        """TC-I13: POST /xai-explain with no body → 400."""
        resp = client.post("/xai-explain", content_type="application/json")
        assert resp.status_code == 400 or resp.status_code == 500

    @pytest.mark.integration
    @patch.object(server, "fetch_openmeteo_weather", return_value=None)
    @patch.object(server, "generate_herbicide_recommendations", return_value=[])
    def test_xai_with_detections(self, mock_herb, mock_weather, client, sample_weed_detections):
        """TC-I14: Valid detections → full XAI response."""
        resp = client.post(
            "/xai-explain",
            data=json.dumps({
                "detections": sample_weed_detections,
                "cropName": "Wheat",
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "features" in data
        assert "sprayingAngle" in data
        assert "weatherSuitability" in data
        assert "featureImportance" in data
        assert "overallConfidence" in data

    @pytest.mark.integration
    @patch.object(server, "fetch_openmeteo_weather", return_value=None)
    @patch.object(server, "generate_herbicide_recommendations", return_value=[])
    def test_xai_empty_detections(self, mock_herb, mock_weather, client):
        """TC-I15: Empty detections → safe defaults."""
        resp = client.post(
            "/xai-explain",
            data=json.dumps({"detections": [], "cropName": "Wheat"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["features"]["totalWeedCount"] == 0
        assert data["sprayingAngle"]["pattern"] == "spot"

    @pytest.mark.integration
    @patch.object(server, "fetch_openmeteo_weather")
    @patch.object(server, "generate_herbicide_recommendations", return_value=[])
    def test_xai_with_location(self, mock_herb, mock_weather, client, sample_weed_detections):
        """TC-I16: Location triggers weather fetch."""
        mock_weather.return_value = {
            "temperature": 25, "windSpeed": 8,
            "windDirection": 180, "humidity": 55, "precipitation": 10,
        }
        resp = client.post(
            "/xai-explain",
            data=json.dumps({
                "detections": sample_weed_detections,
                "cropName": "Wheat",
                "latitude": 10.46,
                "longitude": 76.56,
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["weatherSuitability"]["score"] > 50
        mock_weather.assert_called_once_with(10.46, 76.56)

    @pytest.mark.integration
    @patch.object(server, "fetch_openmeteo_weather", return_value=None)
    @patch.object(server, "generate_herbicide_recommendations", return_value=[])
    def test_xai_overall_confidence_range(self, mock_herb, mock_weather, client, sample_weed_detections):
        """TC-I17: overallConfidence is between 0 and 1."""
        resp = client.post(
            "/xai-explain",
            data=json.dumps({
                "detections": sample_weed_detections,
                "cropName": "Wheat",
            }),
            content_type="application/json",
        )
        data = resp.get_json()
        assert 0 <= data["overallConfidence"] <= 1.0

    @pytest.mark.integration
    @patch.object(server, "fetch_openmeteo_weather", return_value=None)
    @patch.object(server, "generate_herbicide_recommendations", return_value=[])
    def test_xai_generated_at_timestamp(self, mock_herb, mock_weather, client, sample_weed_detections):
        """TC-I18: Response includes a generatedAt ISO timestamp."""
        resp = client.post(
            "/xai-explain",
            data=json.dumps({
                "detections": sample_weed_detections,
                "cropName": "Wheat",
            }),
            content_type="application/json",
        )
        data = resp.get_json()
        assert "generatedAt" in data
        assert "T" in data["generatedAt"]  # ISO format contains 'T'


# ------------------------------------------------------------------
# TC-I19 to TC-I22:  /get-treatment  endpoint
# ------------------------------------------------------------------
class TestGetTreatmentEndpoint:
    """Integration tests for the weed removal technique endpoint."""

    @pytest.mark.integration
    def test_treatment_no_body(self, client):
        """TC-I19: POST /get-treatment with no body → 400."""
        resp = client.post("/get-treatment", content_type="application/json")
        assert resp.status_code == 400 or resp.status_code == 500

    @pytest.mark.integration
    @patch.object(server, "generate_removal_techniques")
    def test_treatment_with_weeds(self, mock_tech, client):
        """TC-I20: Valid weed list → returns technique JSON."""
        mock_tech.return_value = {
            "manual": "Hand-pull weeds at seedling stage.",
            "chemical": "Apply 2,4-D selective herbicide at 1L/ha.",
            "organic": "Mulch with straw between rows.",
            "mechanical": "Use rotary hoe for inter-row cultivation.",
            "priority": "chemical",
            "timing": "Apply 2-3 weeks after crop emergence.",
        }
        resp = client.post(
            "/get-treatment",
            data=json.dumps({
                "cropName": "Wheat",
                "weedTypes": ["waterhemp", "ragweed"],
                "weedCount": 5,
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "manual" in data
        assert "chemical" in data

    @pytest.mark.integration
    @patch.object(server, "generate_removal_techniques")
    def test_treatment_error_propagated(self, mock_tech, client):
        """TC-I21: If Gemini fails, error is returned."""
        mock_tech.return_value = {"error": "Gemini API key not configured"}
        resp = client.post(
            "/get-treatment",
            data=json.dumps({
                "cropName": "Wheat",
                "weedTypes": ["ragweed"],
            }),
            content_type="application/json",
        )
        assert resp.status_code == 500
        data = resp.get_json()
        assert "error" in data

    @pytest.mark.integration
    @patch.object(server, "generate_removal_techniques")
    def test_treatment_default_crop(self, mock_tech, client):
        """TC-I22: Crop defaults to 'Wheat' if omitted."""
        mock_tech.return_value = {
            "manual": "Pull", "chemical": "Spray",
            "organic": "Mulch", "mechanical": "Hoe",
            "priority": "manual", "timing": "Early",
        }
        resp = client.post(
            "/get-treatment",
            data=json.dumps({"weedTypes": ["waterhemp"]}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        mock_tech.assert_called_once()
        call_args = mock_tech.call_args[0]
        assert call_args[0] == "Wheat"


# ------------------------------------------------------------------
# TC-I23 to TC-I24:  /identify-crop  endpoint
# ------------------------------------------------------------------
class TestIdentifyCropEndpoint:
    """Integration tests for crop identification."""

    @pytest.mark.integration
    def test_identify_crop_no_image(self, client):
        """TC-I23: No image → 400."""
        resp = client.post(
            "/identify-crop",
            data=json.dumps({"other": "data"}),
            content_type="application/json",
        )
        assert resp.status_code == 400

    @pytest.mark.integration
    @patch.object(server, "identify_crop_with_roboflow")
    def test_identify_crop_success(self, mock_identify, client):
        """TC-I24: Valid image → returns crop identification."""
        mock_identify.return_value = {
            "cropName": "Wheat",
            "confidence": 0.93,
            "characteristics": "Detected 3 instance(s)",
        }
        img = np.zeros((50, 50, 3), dtype=np.uint8)
        _, buf = cv2.imencode(".jpg", img)
        b64 = base64.b64encode(buf).decode("utf-8")

        resp = client.post(
            "/identify-crop",
            data=json.dumps({"image": b64}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["cropName"] == "Wheat"
        assert data["confidence"] == 0.93


# ------------------------------------------------------------------
# TC-I25:  Error handler
# ------------------------------------------------------------------
class TestErrorHandlers:
    """Verify custom error handlers are registered."""

    @pytest.mark.integration
    def test_404_returns_frontend(self, client):
        """TC-I25: Unknown route may try to serve index.html or 404."""
        resp = client.get("/nonexistent-page")
        # Should not crash — either returns 200 (serving SPA) or 404
        assert resp.status_code in (200, 404)
