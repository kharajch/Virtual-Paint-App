import pytest
import numpy as np
from unittest.mock import MagicMock

# Import the logic functions from main.py
from main import (
    check_fingers_raised,
    check_thumb_raised,
    get_tool_selection,
    check_settings_trigger,
    check_modal_options,
    get_canvas_coords,
    COLORS_INFO,
    SETTINGS_BTN,
    ENGLISH_OPT_BTN,
    BENGALI_OPT_BTN,
    DONE_OPT_BTN
)

# Mock Landmark object for hand landmark checks
class MockLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def test_check_fingers_raised():
    # Case 1: Both index and middle raised (y tip < y joint, note 0 is at top)
    landmarks = [MockLandmark(0, 0)] * 21
    landmarks[8] = MockLandmark(0.5, 0.2)   # Index tip
    landmarks[6] = MockLandmark(0.5, 0.4)   # Index joint
    landmarks[12] = MockLandmark(0.6, 0.2)  # Middle tip
    landmarks[10] = MockLandmark(0.6, 0.4)  # Middle joint
    
    index_raised, middle_raised = check_fingers_raised(landmarks)
    assert index_raised is True
    assert middle_raised is True

    # Case 2: Only index raised
    landmarks[12] = MockLandmark(0.6, 0.5)  # Middle tip lower than joint
    index_raised, middle_raised = check_fingers_raised(landmarks)
    assert index_raised is True
    assert middle_raised is False

    # Case 3: Neither raised
    landmarks[8] = MockLandmark(0.5, 0.5)
    index_raised, middle_raised = check_fingers_raised(landmarks)
    assert index_raised is False
    assert middle_raised is False

def test_check_thumb_raised():
    # Case 1: Thumb raised (tip y < IP joint y)
    landmarks = [MockLandmark(0, 0)] * 21
    landmarks[4] = MockLandmark(0.3, 0.2)  # Thumb tip
    landmarks[3] = MockLandmark(0.3, 0.4)  # Thumb IP joint
    assert check_thumb_raised(landmarks) is True

    # Case 2: Thumb not raised (tip y > IP joint y)
    landmarks[4] = MockLandmark(0.3, 0.5)
    assert check_thumb_raised(landmarks) is False

def test_get_tool_selection():
    # Verify tool matches by coordinate range in header
    for idx, tool in enumerate(COLORS_INFO):
        mid_x = (tool["x_min"] + tool["x_max"]) // 2
        # Hovering at y=50 (within menu_height=145) should select the tool
        assert get_tool_selection(mid_x, 50) == idx

    # Coordinates outside the menu height should return None
    assert get_tool_selection(100, 200) is None

def test_check_settings_trigger():
    # Verify Settings button coordinate trigger
    settings_mid_x = (SETTINGS_BTN["x_min"] + SETTINGS_BTN["x_max"]) // 2
    assert check_settings_trigger(settings_mid_x, 50) is True
    assert check_settings_trigger(100, 50) is False
    assert check_settings_trigger(settings_mid_x, 200) is False

def test_check_modal_options():
    # Verify selecting English
    eng_mid_x = (ENGLISH_OPT_BTN["x_min"] + ENGLISH_OPT_BTN["x_max"]) // 2
    eng_mid_y = (ENGLISH_OPT_BTN["y_min"] + ENGLISH_OPT_BTN["y_max"]) // 2
    assert check_modal_options(eng_mid_x, eng_mid_y) == "ENGLISH"

    # Verify selecting Bengali
    beng_mid_x = (BENGALI_OPT_BTN["x_min"] + BENGALI_OPT_BTN["x_max"]) // 2
    beng_mid_y = (BENGALI_OPT_BTN["y_min"] + BENGALI_OPT_BTN["y_max"]) // 2
    assert check_modal_options(beng_mid_x, beng_mid_y) == "BENGALI"

    # Verify selecting Done
    done_mid_x = (DONE_OPT_BTN["x_min"] + DONE_OPT_BTN["x_max"]) // 2
    done_mid_y = (DONE_OPT_BTN["y_min"] + DONE_OPT_BTN["y_max"]) // 2
    assert check_modal_options(done_mid_x, done_mid_y) == "DONE"

    # Outside bounds
    assert check_modal_options(0, 0) is None

def test_get_canvas_coords():
    assert get_canvas_coords(500, 300) == (500, 300)
