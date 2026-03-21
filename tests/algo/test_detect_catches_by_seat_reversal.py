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
    # Use a signal with enough noise to trigger mandatory secondary validation (SNR < 15)
    # Global amp is 200. We need sqrt(noise_var) > 200 / 15 = 13.3.
    # noise_var > 177.
    np.random.seed(42)
    noise = np.random.normal(0, 15, 101)
    seat_x = pd.Series(500 + 100 * np.cos(t) + noise) # Min around 50
    seat_y = pd.Series(10 + 2 * np.cos(t)) # Min at 50
    
    catches = _detect_catches_by_seat_reversal(seat_x, seat_y=seat_y)
    # Should still find it because seat_y has a reversal
    assert len(catches) >= 1
    
    # Bad secondary signal (monotonic)
    seat_y_bad = pd.Series(np.linspace(0, 10, 101))
    catches_bad = _detect_catches_by_seat_reversal(seat_x, seat_y=seat_y_bad)
    # Now it should be rejected because SNR is low and secondary is bad
    assert len(catches_bad) == 0

def test_detect_catches_chooses_deepest_minimum_in_close_cluster():
    """Regression test for noisy local minima near a catch."""
    seat = pd.Series([
        0.0, 0.5, 1.0, 0.2, 0.0, 0.3, 0.8, 1.2, 0.1, -0.5, -0.4, 0.0,
        0.6, 1.0, 0.7, 0.1, -0.3, -0.2, 0.0
    ])

    # Here we have two candidate minima near indexes 4 and 9 for first stroke.
    catches = _detect_catches_by_seat_reversal(seat, min_separation=6)

    assert len(catches) == 2
    assert catches[0] == 9  # deepest trough should be selected in first cluster
    assert catches[1] == 16  # second stroke trough remains
