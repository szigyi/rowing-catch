"""Unit tests for the _validate_with_secondary_signal helper function.

This module verifies that detection points in a primary signal can be
cross-validated using a secondary signal by checking for a nearby reversal
point (minimum or maximum) in that secondary signal.
"""
import numpy as np
from rowing_catch.algo.helpers import _validate_with_secondary_signal

def test_validate_with_secondary_signal_minima():
    """Verify that a primary minimum is validated by a nearby secondary minimum."""
    # Primary signal minimum at index 5
    primary_idx = 5
    # Secondary signal should also have a minimum near index 5
    secondary = np.array([10, 8, 6, 4, 3, 4, 6, 8, 10]) # min at 4
    
    # Valid with is_minima=True
    assert _validate_with_secondary_signal(primary_idx, secondary, min_separation=10, is_minima=True)

def test_validate_with_secondary_signal_maxima():
    """Verify that a primary maximum is validated by a nearby secondary maximum."""
    # Primary signal maximum at index 5
    primary_idx = 5
    # Secondary signal should also have a maximum near index 5
    secondary = np.array([0, 2, 4, 6, 7, 6, 4, 2, 0]) # max at 4
    
    # Valid with is_minima=False
    assert _validate_with_secondary_signal(primary_idx, secondary, min_separation=10, is_minima=False)

def test_validate_with_secondary_signal_fail_no_reversal():
    """Verify that monotonic secondary signals fail to validate a detection."""
    primary_idx = 5
    secondary = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9]) # monotonic
    
    assert not _validate_with_secondary_signal(primary_idx, secondary, min_separation=10, is_minima=True)
    assert not _validate_with_secondary_signal(primary_idx, secondary, min_separation=10, is_minima=False)

def test_validate_with_secondary_signal_small_window():
    """Verify that very small secondary signals return True by default (can't invalidate)."""
    # Search window too small returns True by default
    primary_idx = 1
    secondary = np.array([1, 2, 3])
    # search_window = max(min_separation // 2, 5). 
    # If we pass min_separation=4, search_window = 5.
    # left = max(0, 1 - 5) = 0. right = min(3, 1 + 5 + 1) = 3.
    # right - left = 3. Not < 3.
    
    # If secondary is [1, 2]
    assert _validate_with_secondary_signal(1, np.array([1, 2]), min_separation=10) == True

def test_validate_with_secondary_signal_window_bounds():
    """Verify that secondary reversals are only found within the search window."""
    # Primary at 50
    primary_idx = 50
    # Secondary has minimum at 55
    t = np.linspace(0, 100, 101)
    secondary = (t - 55)**2
    
    # search_window = max(20//2, 5) = 10.
    # search is [50-10, 50+10+1] = [40, 61]. Minimum at 55 is included.
    assert _validate_with_secondary_signal(primary_idx, secondary, min_separation=20, is_minima=True)
    
    # If min_separation is 4, search_window = 5.
    # search is [50-5, 50+5+1] = [45, 56]. Minimum at 55 is at index 10 in segment.
    # Reversal requires index strictly within [1, 9]. So 55 is at the edge.
    # To pass, let's move it to 54.
    secondary3 = (t - 54)**2
    assert _validate_with_secondary_signal(primary_idx, secondary3, min_separation=4, is_minima=True)
    
    # Still if minimum is at 60 it should fail.
    secondary2 = (t - 60)**2
    # search [45, 56] doesn't include 60.
    assert not _validate_with_secondary_signal(primary_idx, secondary2, min_separation=4, is_minima=True)
