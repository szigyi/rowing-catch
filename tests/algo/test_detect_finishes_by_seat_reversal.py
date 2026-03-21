"""Unit tests for the _detect_finishes_by_seat_reversal helper function.

This module verifies that finish points (local maxima of Seat_X) are correctly
detected and filtered using minimum separation and secondary signal validation.
"""
import numpy as np
import pandas as pd
from rowing_catch.algo.helpers import _detect_finishes_by_seat_reversal

def test_detect_finishes_by_seat_reversal_basic():
    """Verify that clear finishes in a clean signal are correctly detected."""
    # 3 cycles
    t = np.linspace(0, 6 * np.pi, 301)
    # Maxima at 0, 2pi, 4pi, 6pi (idx 0, 100, 200, 300)
    # But local maxima require idx-1 and idx+1. So 100, 200.
    seat_x = pd.Series(500 + 100 * np.cos(t))
    
    finishes = _detect_finishes_by_seat_reversal(seat_x, min_separation=20)
    
    # 100, 200
    assert len(finishes) == 2
    np.testing.assert_allclose(finishes, [100, 200])

def test_detect_finishes_by_seat_reversal_no_candidates():
    """Verify that monotonic signals return no detections."""
    seat_x = pd.Series([5, 4, 3, 2, 1]) # monotonic
    finishes = _detect_finishes_by_seat_reversal(seat_x)
    assert len(finishes) == 0

def test_detect_finishes_by_seat_reversal_min_separation_clustering():
    """Verify that nearby candidate finishes are clustered and the best one is kept."""
    # Two maxima very close to each other
    x = np.array([0, 10, 20, 30, 40, 50, 40, 45, 40, 30, 20, 10, 0])
    # Maxima at idx 5 (val 50) and idx 7 (val 45)
    # distance is 2. If min_separation=5, they should be clustered.
    # The higher one (idx 5, val 50) should be kept.
    seat_x = pd.Series(x)
    
    finishes = _detect_finishes_by_seat_reversal(seat_x, min_separation=5)
    assert len(finishes) == 1
    assert finishes[0] == 5

def test_detect_finishes_by_seat_reversal_with_secondary():
    """Verify that detections are cross-validated when a secondary signal is provided."""
    t = np.linspace(0, 2 * np.pi, 101)
    # Cos(t) has max at 0 and 2pi (idx 0 and 100).
    # Need local max with neighbors: sin(t) from 0 to 2pi has max at pi/2 (idx 25)
    t = np.linspace(0, 2 * np.pi, 101)
    seat_x = pd.Series(500 + 100 * np.sin(t)) # Max at pi/2 (idx 25)
    seat_y = pd.Series(10 + 2 * np.sin(t)) # Max at pi/2 (idx 25)
    
    finishes = _detect_finishes_by_seat_reversal(seat_x, seat_y=seat_y)
    assert len(finishes) == 1
    assert finishes[0] == 25
    
    # Bad secondary signal
    seat_y_bad = pd.Series(np.linspace(10, 0, 101))
    finishes_bad = _detect_finishes_by_seat_reversal(seat_x, seat_y=seat_y_bad)
    assert len(finishes_bad) == 0

def test_detect_finishes_chooses_highest_peak_in_close_cluster():
    """Regression test for noisy local maxima near a finish."""
    seat = pd.Series([
        -0.2, 0.0, 0.3, 1.0, 0.7, 0.35, 0.2, 0.4, 1.8, 1.1, 0.7, 0.4,
        0.1, 0.5, 2.0, 1.0, 0.0
    ])

    # Here we have two close candidate maxima at 3 and 8 (cluster) then one at 14.
    finishes = _detect_finishes_by_seat_reversal(seat, min_separation=6)

    assert len(finishes) == 2
    assert finishes[0] == 8  # highest peak should be selected in first cluster
    assert finishes[1] == 14  # second stroke peak remains
