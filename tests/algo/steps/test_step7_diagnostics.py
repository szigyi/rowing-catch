import numpy as np
import pandas as pd

from rowing_catch.algo.steps.step7_diagnostics import step7_diagnostics, _detect_outliers_zscore

def test_step7_diagnostics_basic():
    """Test diagnostics with stable sampling and no issues."""
    df_raw = pd.DataFrame({'Time': np.linspace(0, 10, 101)})
    df_processed = df_raw.copy()
    avg_cycle = pd.DataFrame({
        'Seat_X_Smooth': np.linspace(0, 100, 10)
    })
    cycles = [pd.DataFrame()] * 5 # 5 cycles
    stats = {'cv_length': 2.0} # CV < 10%
    
    diag = step7_diagnostics(df_raw, df_processed, cycles, avg_cycle, stats)
    
    assert diag['capture_length'] == 5
    assert diag['sampling_is_stable'] == True
    assert diag['rows_dropped'] == 0
    assert diag['data_quality_flag'] == 'OK'
    assert len(diag['warnings']) == 0

def test_step7_diagnostics_unstable_sampling():
    """Test detection of unstable sampling frequency."""
    # Jittery time deltas
    t = np.array([0, 0.1, 0.25, 0.3, 0.45, 0.5]) # dts: 0.1, 0.15, 0.05, 0.15, 0.05
    # mean=0.1. std ~ 0.045. CV ~ 45% > 5%.
    df_raw = pd.DataFrame({'Time': t})
    df_processed = df_raw.copy()
    avg_cycle = pd.DataFrame({'Seat_X_Smooth': np.zeros(5)})
    cycles = [pd.DataFrame()] * 5
    stats = {'cv_length': 2.0}
    
    diag = step7_diagnostics(df_raw, df_processed, cycles, avg_cycle, stats)
    
    assert diag['sampling_is_stable'] == False
    assert any("Sampling frequency unstable" in w for w in diag['warnings'])

def test_step7_diagnostics_row_drops():
    """Test detection of significant data loss."""
    df_raw = pd.DataFrame({'Time': np.arange(100)})
    df_processed = pd.DataFrame({'Time': np.arange(80)}) # 20% dropped
    avg_cycle = pd.DataFrame({'Seat_X_Smooth': np.zeros(10)})
    cycles = [pd.DataFrame()] * 5
    stats = {'cv_length': 2.0}
    
    diag = step7_diagnostics(df_raw, df_processed, cycles, avg_cycle, stats)
    
    assert diag['rows_dropped'] == 20
    assert any("Significant data loss" in w for w in diag['warnings'])

def test_step7_diagnostics_short_capture():
    """Test warning for short capture length."""
    df_raw = pd.DataFrame({'Time': np.arange(10)})
    df_processed = df_raw.copy()
    avg_cycle = pd.DataFrame({'Seat_X_Smooth': np.zeros(10)})
    cycles = [pd.DataFrame()] * 2 # < 3
    stats = {'cv_length': 2.0}
    
    diag = step7_diagnostics(df_raw, df_processed, cycles, avg_cycle, stats)
    
    assert diag['capture_length'] == 2
    assert diag['data_quality_flag'] == 'fail'
    assert any("Capture length too short" in w for w in diag['warnings'])

def test_step7_diagnostics_nan_rate_and_outliers():
    """Test high NaN rate and outlier detection."""
    df_raw = pd.DataFrame({'Time': np.arange(10)})
    df_processed = df_raw.copy()
    cycles = [pd.DataFrame()] * 5
    stats = {'cv_length': 2.0}
    
    # 1. Moderate NaN rate -> warning
    avg_nan_warn = pd.DataFrame({
        'Seat_X_Smooth': [0, 1, 2, 3, 4, 5, 6, 7, 8, np.nan], # 1/10 = 10%
    })
    diag_nan_warn = step7_diagnostics(df_raw, df_processed, cycles, avg_nan_warn, stats)
    assert diag_nan_warn['data_quality_flag'] == 'warning'
    assert any("NaN rate 10.0%" in w for w in diag_nan_warn['warnings'])
    
    # 2. Extreme NaN rate -> fail
    avg_nan_fail = pd.DataFrame({
        'Seat_X_Smooth': [0, np.nan, np.nan, np.nan, np.nan], # 80% > 10%
    })
    diag_nan_fail = step7_diagnostics(df_raw, df_processed, cycles, avg_nan_fail, stats)
    assert diag_nan_fail['data_quality_flag'] == 'fail'
    
    # 3. Outliers -> warning
    avg_outlier = pd.DataFrame({
        'Seat_X_Smooth': [10.0] * 10 + [100.0], # 1 outlier in 11 samples
    })
    diag_outlier = step7_diagnostics(df_raw, df_processed, cycles, avg_outlier, stats)
    assert diag_outlier['outlier_count'] == 1
    assert diag_outlier['data_quality_flag'] == 'warning'
    assert any("1 outliers" in w for w in diag_outlier['warnings'])

def test_step7_diagnostics_high_cv_variability():
    """Test high CV variability detection."""
    df_raw = pd.DataFrame({'Time': np.arange(10)})
    df_processed = df_raw.copy()
    avg_cycle = pd.DataFrame({'Seat_X_Smooth': np.zeros(10)})
    cycles = [pd.DataFrame()] * 5
    
    # CV > 10%
    stats_high_cv = {'cv_length': 15.0}
    diag_cv = step7_diagnostics(df_raw, df_processed, cycles, avg_cycle, stats_high_cv)
    assert diag_cv['data_quality_flag'] == 'warning'
    assert any("High stroke length variability" in w for w in diag_cv['warnings'])

def test_detect_outliers_zscore():
    """Test z-score outlier detection."""
    # Data with one clear outlier
    data = np.array([10, 10.1, 10.2, 9.9, 10.0, 10.1, 50.0]) # 50 is outlier
    outliers = _detect_outliers_zscore(data, threshold=2.0)
    assert outliers[6] == True
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
