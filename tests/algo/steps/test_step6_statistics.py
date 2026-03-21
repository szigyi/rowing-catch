import numpy as np
import pandas as pd
import pytest
from rowing_catch.algo.steps.step6_statistics import step6_statistics, _compute_phase_volume, _detect_outliers_zscore

def test_step6_statistics_basic():
    """Test statistics computation with 3 identical clean cycles."""
    # Create 3 identical cycles
    # Seat moves from 0 to 100 and back to 0.
    # Catch at 0, Finish at 50, Total length 100.
    t = np.linspace(0, 1.0, 101)
    seat_x = 50 - 50 * np.cos(2 * np.pi * t)
    
    df = pd.DataFrame({
        'Time': t,
        'Seat_X_Smooth': seat_x,
        'Handle_X_Smooth': np.zeros(101),
        'Handle_Y_Smooth': np.zeros(101),
        'Seat_Y_Smooth': np.zeros(101),
        'Shoulder_X_Smooth': np.zeros(101),
        'Shoulder_Y_Smooth': np.zeros(101)
    })
    
    cycles = [df.copy(), df.copy(), df.copy()]
    min_length = 101
    catch_idx = 0
    finish_idx = 50
    
    stats = step6_statistics(cycles, min_length, catch_idx, finish_idx)
    
    assert stats['cv_length'] == 0.0 # Identical cycles
    assert stats['drive_len'] == 50
    assert stats['recovery_len'] == 51 # 101 - 50 = 51
    assert stats['mean_duration'] == 101.0
    assert stats['data_quality_flag'] == 'OK'
    assert stats['outlier_count'] == 0
    assert stats['nan_rate'] == 0.0

def test_step6_statistics_quality_flags_fewer_than_3_cycles():
    """Test data quality flag logic for fewer than 3 cycles."""
    t = np.linspace(0, 1.0, 10)
    df = pd.DataFrame({'Seat_X_Smooth': np.zeros(10)})
    
    # 1. Fewer than 3 cycles -> fail
    stats_few = step6_statistics([df, df], 10, 0, 5)
    assert stats_few['data_quality_flag'] == 'fail'

def test_step6_statistics_quality_flags_high_nan_rate():
    """Test data quality flag logic for high NaN rate."""
    # 2. High NaN rate -> fail
    df_nan = pd.DataFrame({
        'Seat_X_Smooth': [np.nan, 0, 0, 0, 0, 0, 0, 0, 0, 0], # 1/10 = 10%
        'Handle_X_Smooth': [np.nan] * 10 # 100%
    })
    stats_nan = step6_statistics([df_nan, df_nan, df_nan], 10, 0, 5)
    assert stats_nan['data_quality_flag'] == 'fail'

def test_step6_statistics_quality_flags_high_cv():
    """Test data quality flag logic for high coefficient of variation."""
    # 3. High CV -> warning
    df1 = pd.DataFrame({'Seat_X_Smooth': np.array([0, 10, 0])}) # amp 10
    df2 = pd.DataFrame({'Seat_X_Smooth': np.array([0, 20, 0])}) # amp 20
    df3 = pd.DataFrame({'Seat_X_Smooth': np.array([0, 15, 0])}) # amp 15
    # mean=15, std ~ 4.08, CV ~ 27% > 10%
    stats_cv = step6_statistics([df1, df2, df3], 3, 0, 1)
    assert stats_cv['data_quality_flag'] == 'warning'

def test_compute_phase_volume():
    """Test the internal volume integration logic."""
    # positions: 0, 10, 20, 30
    # times: 0, 1, 2, 3
    # diffs: 10, 10, 10. dts: 1, 1, 1.
    # volume = 10*1 + 10*1 + 10*1 = 30.
    pos = np.array([0, 10, 20, 30], dtype=float)
    times = np.array([0, 1, 2, 3], dtype=float)
    
    vol = _compute_phase_volume(pos, times, 0, 4)
    assert vol == 30.0
    
    # Sinusoidal data
    t = np.linspace(0, 2, 101)
    seat_x = 50 + 50 * np.sin(2 * np.pi * t)
    # 0 to 1 second is drive (idx 0-50), 1 to 2 is recovery (50-100)
    # Total points 101.
    # We expect positive volume for both.
    vol_sin = _compute_phase_volume(seat_x, t, 0, 51)
    assert vol_sin > 0
    
    # Without times (defaults to dt=1)
    vol_no_times = _compute_phase_volume(pos, None, 0, 4)
    assert vol_no_times == 30.0

def test_detect_outliers_zscore():
    """Test z-score outlier detection."""
    # Data with one clear outlier
    data = np.array([10, 10.1, 10.2, 9.9, 10.0, 50.0]) # 50 is outlier
    outliers = _detect_outliers_zscore(data, threshold=2.0)
    assert outliers[5] == True
    assert sum(outliers) == 1
    
    # Realistic test with normal distribution + extreme outlier
    np.random.seed(42)
    normal_data = np.random.normal(loc=5.0, scale=1.0, size=100)
    data_with_outlier = np.concatenate([normal_data, [50.0]])
    outliers_robust = _detect_outliers_zscore(data_with_outlier, threshold=3.0)
    assert outliers_robust[-1] == True, "Extreme outlier should be detected"
    assert np.sum(outliers_robust[:-1]) < 5, "Few normal samples should be flagged as outliers"
    
    # No variation
    data_flat = np.array([10, 10, 10])
    outliers_flat = _detect_outliers_zscore(data_flat)
    assert not any(outliers_flat)
