"""Unit tests for the _is_valid_finish helper function.

This module verifies the robustness heuristics used to filter candidate finishes,
including strict local maximum checks, prominence, signal-to-noise ratio,
global amplitude ratio, and secondary signal cross-validation.
"""

import numpy as np

from rowing_catch.algo.helpers import _is_valid_finish


def test_is_valid_finish_basic():
    """Verify that a clear local maximum in a clean signal is accepted."""
    # Simple parabola with maximum at 5
    x = np.array([0, 10, 20, 30, 40, 50, 40, 30, 20, 10, 0])
    # global amp = 50. local_depth = 10. required = 0.2 * 50 = 10.
    # mean = 22.7. x[5] = 50. 50 > 22.7 and 50 > 50 - 0.33 * 50 = 33.5. Passes.
    assert _is_valid_finish(x, 5, min_separation=2, prominence=None, snr_threshold=0)


def test_is_valid_finish_not_maximum():
    """Verify that points that are not local maxima are rejected."""
    x = np.array([0, 5, 10, 5, 0])
    # x[1]=5 is not a local maximum
    assert not _is_valid_finish(x, 1, min_separation=2, prominence=None, snr_threshold=0)


def test_is_valid_finish_shallow_lump():
    """Verify that shallow lumps relative to global amplitude are rejected."""
    # Signal with a large global amplitude and a tiny lump
    x = np.zeros(101)
    x[0] = -1000
    x[50] = 0
    x[49] = -1
    x[51] = -1
    # Global amp = 1000. local depth = 1. required = 0.2 * 1000 = 200.
    assert not _is_valid_finish(x, 50, min_separation=10, prominence=None, snr_threshold=0)


def test_is_valid_finish_too_low():
    """Verify that finishes located too low in the signal's range are rejected."""
    # Finish must be in the upper third of the signal
    # x = [10, 0, 1, 0, 10]. Mean = 4.2. x[2]=1. 1 < 4.2 -> FAIL.
    x = np.array([10, 0, 1, 0, 10])
    assert not _is_valid_finish(x, 2, min_separation=1, prominence=None, snr_threshold=0)


def test_is_valid_finish_prominence():
    """Verify that finishes with insufficient prominence are rejected."""
    x = np.array([0, 5, 4, 5, 0])
    # local maximum at 1 and 3.
    # neighborhood for idx 1: [0, 4, 5, 0]. max=5. x[1]=5. x[1]-max=0.
    # mean=2.25. x[1]=5. x[1]-mean=2.75.
    # If prominence is 3.0: 0 < 3.0 (T) and 2.75 < 3.0 (T) -> return False.
    assert not _is_valid_finish(x, 1, min_separation=5, prominence=3.0, snr_threshold=0)


def test_is_valid_finish_secondary_signal():
    """Verify that a finish is accepted when confirmed by the secondary signal."""
    x = np.array([0, 5, 10, 5, 0])
    # Secondary signal also has a maximum nearby
    y = np.array([0, 5, 10, 5, 0])
    assert _is_valid_finish(x, 2, min_separation=2, prominence=None, secondary_signal=y, snr_threshold=0)


def test_is_valid_finish_rejected_by_secondary_signal():
    """Verify that a finish is rejected when not confirmed by the secondary signal."""
    x = np.array([0, 5, 10, 5, 0])
    # Secondary signal does NOT have a maximum nearby
    y_bad = np.array([10, 9, 8, 7, 6])
    # Use high snr_threshold to force mandatory secondary validation
    assert not _is_valid_finish(x, 2, min_separation=2, prominence=None, secondary_signal=y_bad, snr_threshold=1000)


def test_is_valid_finish_boundary_leeway():
    """Verify that finishes near the start/end of a signal have relaxed depth requirements."""
    # Near boundary, required depth is reduced to 0.1 * global_amp
    # Global amp is 100. low=0, high=100. Normal required = 20. Boundary required = 10.
    x = np.full(100, 0.0)
    x[50] = 100  # global max
    x[1] = 85
    x[2] = 95  # local max
    x[3] = 85
    # global amp = 100. local depth = 10.
    # Normal required = 20. 10 < 20.
    # idx=2 <= min_separation=10 -> required = 10. 10 >= 10 -> Pass.
    # Also need to pass x[idx] > mean_val. Mean is approx 3.7. 95 > 3.7.
    assert _is_valid_finish(x, 2, min_separation=10, prominence=None, snr_threshold=0)


def test_is_valid_finish_high_snr_threshold():
    """Verify that a finish is rejected if the required SNR threshold is set higher than the signal's SNR."""
    # Clean signal has SNR = 1000
    x = np.array([50, 40, 30, 20, 10, 0, 10, 20, 30, 40, 50])
    # If we require SNR > 2000, it should fail
    assert not _is_valid_finish(x, 5, min_separation=2, prominence=None, snr_threshold=2000)
