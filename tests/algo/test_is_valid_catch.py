"""Unit tests for the _is_valid_catch helper function.

This module verifies the robustness heuristics used to filter candidate catches,
including strict local minimum checks, prominence, signal-to-noise ratio,
global amplitude ratio, and secondary signal cross-validation.
"""
import numpy as np
from rowing_catch.algo.helpers import _is_valid_catch

def test_is_valid_catch_basic():
    """Verify that a clear local minimum in a clean signal is accepted."""
    x = np.array([50, 40, 30, 20, 10, 0, 10, 20, 30, 40, 50])
    assert _is_valid_catch(x, 5, min_separation=2, prominence=None)

def test_is_valid_catch_not_minimum():
    """Verify that points that are not local minima are rejected."""
    x = np.array([10, 5, 0, 1, 2])
    # x[1]=5 is not a local minimum
    assert not _is_valid_catch(x, 1, min_separation=2, prominence=None)

def test_is_valid_catch_shallow_dip():
    """Verify that shallow dips relative to global amplitude are rejected."""
    # Signal with a large global amplitude and a tiny dip
    x = np.zeros(101)
    x[0] = 1000
    x[50] = 0
    x[49] = 1
    x[51] = 1
    # Global amp = 1000. local depth = 1. required = 0.2 * 1000 = 200.
    assert not _is_valid_catch(x, 50, min_separation=10, prominence=None)

def test_is_valid_catch_too_high():
    """Verify that catches located too high in the signal's range are rejected."""
    # Catch must be in the lower third of the signal
    x = np.array([100, 90, 80, 81, 100])
    # Global amp = 20. low = 80. upper bound = 80 + 0.33*20 = 86.6. 
    # But wait, it also checks x[idx] > mean_val.
    # mean = (100+90+80+81+100)/5 = 90.2.
    # 80 < 90.2 and 80 < 86.6. So it should PASS this check.
    assert _is_valid_catch(x, 2, min_separation=1, prominence=None)
    
    # Let's make it fail the "too high" check
    x2 = np.array([20, 19, 18, 19, 20])
    # amp=2, low=18, mean=19.2. x[idx]=18. 18 < 19.2 and 18 < 18 + 0.33*2 = 18.66. PASS.
    assert _is_valid_catch(x2, 2, min_separation=1, prominence=None)
    
    # Actually, if the whole signal is very flat:
    x3 = np.array([10.5, 10.4, 10.3, 10.4, 10.5])
    # amp=0.2, low=10.3, mean=10.42. 10.3 < 10.42 and 10.3 < 10.366. PASS.
    assert _is_valid_catch(x3, 2, min_separation=1, prominence=None)
    
    # To fail: x[idx] > mean_val
    # x = [0, 10, 9, 10, 0]. Mean = 5.8. x[2]=9. 9 > 5.8 -> FAIL.
    # But x[2]=9 is a local minimum? Yes.
    x4 = np.array([0, 10, 9, 10, 0])
    assert not _is_valid_catch(x4, 2, min_separation=1, prominence=None)

def test_is_valid_catch_prominence():
    """Verify that catches with insufficient prominence are rejected."""
    x = np.array([10, 5, 6, 5, 10])
    # local minimum at 1 and 3.
    # neighborhood for idx 1: [10, 6, 5, 10]. min=5. x[1]=5. min-x[1]=0.
    # mean=7.75. x[1]=5. mean-x[1]=2.75.
    # If prominence is 3.0: 0 < 3.0 (T) and 2.75 < 3.0 (T) -> return False.
    assert not _is_valid_catch(x, 1, min_separation=5, prominence=3.0)

def test_is_valid_catch_secondary_signal():
    """Verify that a catch is accepted when confirmed by the secondary signal."""
    x = np.array([10, 5, 0, 5, 10])
    # Secondary signal also has a minimum nearby
    y = np.array([10, 5, 0, 5, 10])
    assert _is_valid_catch(x, 2, min_separation=2, prominence=None, secondary_signal=y)

def test_is_valid_catch_rejected_by_secondary_signal():
    """Verify that a catch is rejected when not confirmed by the secondary signal."""
    x = np.array([10, 5, 0, 5, 10])
    # Secondary signal does NOT have a minimum nearby
    y_bad = np.array([0, 1, 2, 3, 4])
    assert not _is_valid_catch(x, 2, min_separation=2, prominence=None, secondary_signal=y_bad)

def test_is_valid_catch_boundary_leeway():
    """Verify that catches near the start/end of a signal have relaxed depth requirements."""
    # Near boundary, required depth is reduced to 0.1 * global_amp
    # Global amp is 100. low=0, high=100. Normal required = 20. Boundary required = 10.
    x = np.full(100, 100.0) # Start with high values
    x[50] = 0 # global min
    x[1] = 15
    x[2] = 5 # local min near boundary
    x[3] = 15
    # global amp = 100. local depth = 10. 
    # Normal required = 20. 10 < 20.
    # idx=2 <= min_separation=10 -> required = 10. 10 >= 10 -> Pass.
    # Also need to pass x[idx] < mean_val. Mean is approx 97. 5 < 97.
    assert _is_valid_catch(x, 2, min_separation=10, prominence=None)

def test_is_valid_catch_high_snr_threshold():
    """Verify that a catch is rejected if the required SNR threshold is set higher than the signal's SNR."""
    # Clean signal has SNR = 1000
    x = np.array([50, 40, 30, 20, 10, 0, 10, 20, 30, 40, 50])
    # If we require SNR > 2000, it should fail
    assert not _is_valid_catch(x, 5, min_separation=2, prominence=None, snr_threshold=2000)
