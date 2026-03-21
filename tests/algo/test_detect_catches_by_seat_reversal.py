"""Unit tests for the _detect_catches_by_seat_reversal helper function.

This module verifies that catch points (local minima of Seat_X) are correctly
detected and filtered using minimum separation and secondary signal validation.
"""
import numpy as np
import pandas as pd
from rowing_catch.algo.helpers import _detect_catches_by_seat_reversal

def test_detect_catches_by_seat_reversal_basic():
    """Verify that clear catches in a clean signal are correctly detected."""
    # 3 cycles
    t = np.linspace(0, 6 * np.pi, 301)
    seat_x = pd.Series(500 + 100 * np.cos(t)) # Minima at pi, 3pi, 5pi (idx 50, 150, 250)
    
    catches = _detect_catches_by_seat_reversal(seat_x, min_separation=20)
    
    assert len(catches) == 3
    np.testing.assert_allclose(catches, [50, 150, 250])

def test_detect_catches_by_seat_reversal_no_candidates():
    """Verify that monotonic signals return no detections."""
    seat_x = pd.Series([1, 2, 3, 4, 5]) # monotonic
    catches = _detect_catches_by_seat_reversal(seat_x)
    assert len(catches) == 0

def test_detect_catches_by_seat_reversal_min_separation_clustering():
    """Verify that nearby candidate catches are clustered and the best one is kept."""
    # Two minima very close to each other
    x = np.array([50, 40, 30, 20, 10, 0, 10, 5, 10, 20, 30, 40, 50])
    # Minima at idx 5 (val 0) and idx 7 (val 5)
    # distance is 2. If min_separation=5, they should be clustered.
    # The deeper one (idx 5, val 0) should be kept.
    seat_x = pd.Series(x)
    
    catches = _detect_catches_by_seat_reversal(seat_x, min_separation=5)
    assert len(catches) == 1
    assert catches[0] == 5

def test_detect_catches_by_seat_reversal_with_secondary():
    """Verify that detections are cross-validated when a secondary signal is provided."""
    t = np.linspace(0, 2 * np.pi, 101)
    seat_x = pd.Series(500 + 100 * np.cos(t)) # Min at 50
    seat_y = pd.Series(10 + 2 * np.cos(t)) # Min at 50
    
    catches = _detect_catches_by_seat_reversal(seat_x, seat_y=seat_y)
    assert len(catches) == 1
    assert catches[0] == 50
    
    # Bad secondary signal
    seat_y_bad = pd.Series(np.linspace(0, 10, 101))
    catches_bad = _detect_catches_by_seat_reversal(seat_x, seat_y=seat_y_bad)
    assert len(catches_bad) == 0
