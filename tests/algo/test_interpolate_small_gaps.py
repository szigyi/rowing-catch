"""Unit tests for the _interpolate_small_gaps helper function.

This module verifies that small NaN gaps in a 1D array are correctly identified
and filled using linear interpolation or boundary padding, while larger gaps
are preserved.
"""
import numpy as np
from rowing_catch.algo.helpers import _interpolate_small_gaps

def test_interpolate_small_gaps_no_nans():
    """Verify that an array without NaNs remains unchanged."""
    series = np.array([1.0, 2.0, 3.0])
    result = _interpolate_small_gaps(series)
    np.testing.assert_allclose(result, series)

def test_interpolate_small_gaps_small_gap_middle():
    """Verify that a single NaN in the middle is correctly interpolated."""
    series = np.array([1.0, np.nan, 3.0])
    result = _interpolate_small_gaps(series, max_gap_size=1)
    np.testing.assert_allclose(result, [1.0, 2.0, 3.0])

def test_interpolate_small_gaps_too_large_gap():
    """Verify that a gap larger than max_gap_size is not interpolated."""
    series = np.array([1.0, np.nan, np.nan, 4.0])
    result = _interpolate_small_gaps(series, max_gap_size=1)
    # Should not be interpolated
    np.testing.assert_allclose(result, series)

def test_interpolate_small_gaps_start():
    """Verify that a small gap at the start is filled with the first non-NaN value."""
    series = np.array([np.nan, 2.0, 3.0])
    result = _interpolate_small_gaps(series, max_gap_size=1)
    # If gap is at start, it fills with the first non-NaN value
    np.testing.assert_allclose(result, [2.0, 2.0, 3.0])

def test_interpolate_small_gaps_end():
    """Verify that a small gap at the end is filled with the last non-NaN value."""
    series = np.array([1.0, 2.0, np.nan])
    result = _interpolate_small_gaps(series, max_gap_size=1)
    # If gap is at end, it fills with the last non-NaN value
    np.testing.assert_allclose(result, [1.0, 2.0, 2.0])

def test_interpolate_small_gaps_multiple_gaps():
    """Verify that multiple small gaps are all correctly filled."""
    series = np.array([np.nan, 2.0, np.nan, np.nan, 5.0, np.nan, 7.0])
    # gap sizes: 1, 2, 1
    result = _interpolate_small_gaps(series, max_gap_size=2)
    expected = [2.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    np.testing.assert_allclose(result, expected)

def test_interpolate_small_gaps_max_gap_size_limit():
    """Verify that the max_gap_size limit is strictly enforced."""
    series = np.array([1.0, np.nan, np.nan, np.nan, 5.0]) # gap of 3
    result = _interpolate_small_gaps(series, max_gap_size=2)
    # gap of 3 > max_gap_size 2, so it shouldn't be filled
    np.testing.assert_allclose(result, series)
    
    result2 = _interpolate_small_gaps(series, max_gap_size=3)
    # gap of 3 <= max_gap_size 3, so it should be filled
    expected = [1.0, 2.0, 3.0, 4.0, 5.0]
    np.testing.assert_allclose(result2, expected)
