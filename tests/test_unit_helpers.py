"""
test_unit_helpers.py  –  UNIT TESTS for pure helper functions in server.py

Functions under test:
    • get_crop_type(label, crop_name)
    • get_class_conf_threshold(class_name)
    • resize_image_for_inference(img, max_size)

Each test is independent and runs in < 10 ms.
"""

import pytest
import numpy as np
import server

# ======================================================================
# Phase 1 — UNIT TESTS
# ======================================================================


# ------------------------------------------------------------------
# TC-U01 to TC-U10:  get_crop_type()
# ------------------------------------------------------------------
class TestGetCropType:
    """Verify weed vs crop classification logic."""

    # --- Weed detection cases ---

    @pytest.mark.unit
    def test_known_weed_waterhemp(self):
        """TC-U01: Known weed label → 'weed'."""
        assert server.get_crop_type("waterhemp", "Wheat") == "weed"

    @pytest.mark.unit
    def test_known_weed_morningglory(self):
        """TC-U02: morningglory → 'weed'."""
        assert server.get_crop_type("morningglory", "Wheat") == "weed"

    @pytest.mark.unit
    def test_known_weed_palmer_amaranth(self):
        """TC-U03: palmer_amaranth → 'weed'."""
        assert server.get_crop_type("palmer_amaranth", "Wheat") == "weed"

    @pytest.mark.unit
    def test_known_weed_ragweed(self):
        """TC-U04: ragweed → 'weed'."""
        assert server.get_crop_type("ragweed", "Corn") == "weed"

    @pytest.mark.unit
    def test_weed_keyword_in_label(self):
        """TC-U05: A label containing 'weed' substring → 'weed'."""
        assert server.get_crop_type("giant ragweed", "Wheat") == "weed"

    # --- Crop detection cases ---

    @pytest.mark.unit
    def test_explicit_crop_wheat(self):
        """TC-U06: Label matching a known crop keyword → 'crop'."""
        assert server.get_crop_type("wheat", "Wheat") == "crop"

    @pytest.mark.unit
    def test_explicit_crop_corn(self):
        """TC-U07: corn → 'crop'."""
        assert server.get_crop_type("corn", "Corn") == "crop"

    @pytest.mark.unit
    def test_roboflow_crop_label(self):
        """TC-U08: Roboflow 'crop' class → always 'crop'."""
        assert server.get_crop_type("crop", "Wheat") == "crop"

    # --- Edge / default cases ---

    @pytest.mark.unit
    def test_unknown_label_with_crop_context(self):
        """TC-U09: Totally unknown label but crop context is set → 'crop'."""
        assert server.get_crop_type("some_random_object", "Wheat") == "crop"

    @pytest.mark.unit
    def test_unknown_label_general_crop(self):
        """TC-U10: Unknown label with generic crop context → 'weed'."""
        assert server.get_crop_type("some_plant", "general crop") == "weed"

    @pytest.mark.unit
    def test_case_insensitive(self):
        """TC-U11: Labels are case-insensitive."""
        assert server.get_crop_type("WATERHEMP", "Wheat") == "weed"
        assert server.get_crop_type("Wheat", "Wheat") == "crop"

    @pytest.mark.unit
    def test_non_plant_objects(self):
        """TC-U12: Non-plant objects like 'person' → 'weed' (filtered out later)."""
        assert server.get_crop_type("person", "Wheat") == "weed"


# ------------------------------------------------------------------
# TC-U13 to TC-U17:  get_class_conf_threshold()
# ------------------------------------------------------------------
class TestGetClassConfThreshold:
    """Verify per-class confidence threshold lookup."""

    @pytest.mark.unit
    def test_waterhemp_threshold(self):
        """TC-U13: Known class returns its configured threshold."""
        assert server.get_class_conf_threshold("waterhemp") == 0.30

    @pytest.mark.unit
    def test_sicklepod_threshold(self):
        """TC-U14: sicklepod has the strictest threshold (0.45)."""
        assert server.get_class_conf_threshold("sicklepod") == 0.45

    @pytest.mark.unit
    def test_velvetleaf_threshold(self):
        """TC-U15: velvetleaf → 0.32."""
        assert server.get_class_conf_threshold("velvetleaf") == 0.32

    @pytest.mark.unit
    def test_unknown_class_default(self):
        """TC-U16: Unknown class → fallback of 0.35."""
        assert server.get_class_conf_threshold("unknown_weed_xyz") == 0.35

    @pytest.mark.unit
    def test_case_insensitive_lookup(self):
        """TC-U17: Threshold lookup is case-insensitive (lowered internally)."""
        assert server.get_class_conf_threshold("WATERHEMP") == 0.30  # matches 'waterhemp' → 0.30


# ------------------------------------------------------------------
# TC-U18 to TC-U22:  resize_image_for_inference()
# ------------------------------------------------------------------
class TestResizeImageForInference:
    """Verify image resizing preserves aspect ratio and respects max_size."""

    @pytest.mark.unit
    def test_no_resize_when_small(self, sample_image_640):
        """TC-U18: Image already ≤ max_size → returned unchanged."""
        result = server.resize_image_for_inference(sample_image_640, max_size=640)
        assert result.shape == (640, 640, 3)

    @pytest.mark.unit
    def test_downscale_large_image(self, sample_image_1920):
        """TC-U19: 1920×1080 image scaled down to max_size=640."""
        result = server.resize_image_for_inference(sample_image_1920, max_size=640)
        h, w = result.shape[:2]
        assert max(h, w) <= 640

    @pytest.mark.unit
    def test_aspect_ratio_preserved(self):
        """TC-U20: Aspect ratio stays the same after resize."""
        img = np.zeros((400, 800, 3), dtype=np.uint8)  # 2:1 ratio
        result = server.resize_image_for_inference(img, max_size=400)
        h, w = result.shape[:2]
        original_ratio = 800 / 400
        resized_ratio = w / h
        assert abs(original_ratio - resized_ratio) < 0.05

    @pytest.mark.unit
    def test_custom_max_size(self):
        """TC-U21: max_size=320 works correctly."""
        img = np.zeros((1000, 1000, 3), dtype=np.uint8)
        result = server.resize_image_for_inference(img, max_size=320)
        h, w = result.shape[:2]
        assert max(h, w) <= 320

    @pytest.mark.unit
    def test_returns_numpy_array(self, sample_image_1920):
        """TC-U22: Return type is always a numpy ndarray."""
        result = server.resize_image_for_inference(sample_image_1920, max_size=640)
        assert isinstance(result, np.ndarray)
