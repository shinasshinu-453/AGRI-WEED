"""
conftest.py  –  Shared fixtures & mocks used by all test modules.

Because server.py performs heavy initialization at import time
(YOLO model loading, torch device detection, Gemini API setup)
we mock those heavy dependencies here BEFORE importing server.
"""

import sys
import os
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# 1) Ensure project root is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# 2) Create lightweight mocks for heavy third-party libraries
#    so that importing server.py doesn't actually load a GPU model.
# ---------------------------------------------------------------------------

# Fake YOLO model
class _FakeYOLO:
    """Minimal stand-in for ultralytics.YOLO."""
    names = {
        0: 'waterhemp', 1: 'morningglory', 2: 'ragweed', 3: 'cocklebur',
        4: 'spurred_anteria', 5: 'prickly_sida', 6: 'velvetleaf',
        7: 'palmer_amaranth', 8: 'redroot_pigweed', 9: 'johnsongrass',
        10: 'tall_morningglory', 11: 'sicklepod',
    }

    def __init__(self, *a, **kw):
        pass

    def to(self, device):
        return self

    def fuse(self):
        return self

    def __call__(self, *args, **kwargs):
        """Return an empty results list (no detections)."""
        return [MagicMock(boxes=None)]


# Patch ultralytics YOLO class
_ultralytics_mock = MagicMock()
_ultralytics_mock.YOLO = _FakeYOLO
sys.modules.setdefault("ultralytics", _ultralytics_mock)

# Patch google.genai (new SDK)
_google_mock = MagicMock()
_genai_mock = MagicMock()
_google_mock.genai = _genai_mock
sys.modules.setdefault("google", _google_mock)
sys.modules.setdefault("google.genai", _genai_mock)

# Patch pyngrok
sys.modules.setdefault("pyngrok", MagicMock())
sys.modules.setdefault("pyngrok.ngrok", MagicMock())

# Ensure torch is available but cuda reports False (CPU mode)
try:
    import torch
    torch.cuda.is_available = lambda: False
except ImportError:
    _torch_mock = MagicMock()
    _torch_mock.cuda.is_available.return_value = False
    sys.modules["torch"] = _torch_mock

# Now it is safe to import server
import server  # noqa: E402


# ---------------------------------------------------------------------------
# 3) Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def app():
    """Return the Flask application with testing mode enabled."""
    server.app.config["TESTING"] = True
    return server.app


@pytest.fixture
def client(app):
    """Flask test client for integration tests."""
    with app.test_client() as c:
        yield c


@pytest.fixture
def sample_weed_detections():
    """A list of mock YOLO detection dicts (3 weeds, 1 crop)."""
    return [
        {
            "label": "waterhemp",
            "confidence": 0.87,
            "box": {"xmin": 0.1, "ymin": 0.2, "xmax": 0.3, "ymax": 0.4},
            "type": "weed",
            "description": "waterhemp (87.0%)",
            "raw_class": "waterhemp",
        },
        {
            "label": "morningglory",
            "confidence": 0.72,
            "box": {"xmin": 0.5, "ymin": 0.5, "xmax": 0.7, "ymax": 0.7},
            "type": "weed",
            "description": "morningglory (72.0%)",
            "raw_class": "morningglory",
        },
        {
            "label": "ragweed",
            "confidence": 0.65,
            "box": {"xmin": 0.6, "ymin": 0.1, "xmax": 0.8, "ymax": 0.3},
            "type": "weed",
            "description": "ragweed (65.0%)",
            "raw_class": "ragweed",
        },
        {
            "label": "wheat",
            "confidence": 0.92,
            "box": {"xmin": 0.2, "ymin": 0.3, "xmax": 0.5, "ymax": 0.6},
            "type": "crop",
            "description": "wheat (92.0%)",
            "raw_class": "wheat",
        },
    ]


@pytest.fixture
def sample_no_weed_detections():
    """A list of mock detections with no weeds – only crops."""
    return [
        {
            "label": "wheat",
            "confidence": 0.95,
            "box": {"xmin": 0.1, "ymin": 0.1, "xmax": 0.9, "ymax": 0.9},
            "type": "crop",
            "description": "wheat (95.0%)",
            "raw_class": "wheat",
        }
    ]


@pytest.fixture
def sample_image_640():
    """A 640×640 blank numpy image (3-channel, uint8)."""
    return np.zeros((640, 640, 3), dtype=np.uint8)


@pytest.fixture
def sample_image_1920():
    """A 1920×1080 blank numpy image (3-channel, uint8)."""
    return np.zeros((1080, 1920, 3), dtype=np.uint8)


@pytest.fixture
def sample_weather_good():
    """Weather data that is ideal for spraying."""
    return {
        "temperature": 22,
        "windSpeed": 5,
        "windDirection": 180,
        "humidity": 60,
        "precipitation": 5,
    }


@pytest.fixture
def sample_weather_bad():
    """Weather data that is NOT suitable for spraying."""
    return {
        "temperature": 40,
        "windSpeed": 30,
        "windDirection": 90,
        "humidity": 25,
        "precipitation": 75,
    }
