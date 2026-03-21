import numpy as np
import pandas as pd
from rowing_catch.algo.steps.step8_diagnostics import step8_metadata_diagnostics

def test_step8_metadata_diagnostics_basic():
    """Test diagnostics with stable sampling and no issues."""
    df_raw = pd.DataFrame({'Time': np.linspace(0, 10, 100)})
    df_processed = df_raw.copy()
    cycles = [pd.DataFrame()] * 5 # 5 cycles
    time_metrics = {}
    stats = {'data_quality_flag': 'OK'}
    
    diag = step8_metadata_diagnostics(df_raw, df_processed, cycles, time_metrics, stats)
    
    assert diag['capture_length'] == 5
    assert diag['sampling_is_stable'] == True
    assert diag['rows_dropped'] == 0
    assert len(diag['warnings']) == 0

def test_step8_metadata_diagnostics_unstable_sampling():
    """Test detection of unstable sampling frequency."""
    # Jittery time deltas
    t = np.array([0, 0.1, 0.25, 0.3, 0.45, 0.5]) # dts: 0.1, 0.15, 0.05, 0.15, 0.05
    # mean=0.1. std ~ 0.045. CV ~ 45% > 5%.
    df_raw = pd.DataFrame({'Time': t})
    df_processed = df_raw.copy()
    cycles = [pd.DataFrame()] * 5
    stats = {'data_quality_flag': 'OK'}
    
    diag = step8_metadata_diagnostics(df_raw, df_processed, cycles, {}, stats)
    
    assert diag['sampling_is_stable'] == False
    assert any("Sampling frequency unstable" in w for w in diag['warnings'])

def test_step8_metadata_diagnostics_row_drops():
    """Test detection of significant data loss."""
    df_raw = pd.DataFrame({'Time': np.arange(100)})
    df_processed = pd.DataFrame({'Time': np.arange(80)}) # 20% dropped
    cycles = [pd.DataFrame()] * 5
    stats = {'data_quality_flag': 'OK'}
    
    diag = step8_metadata_diagnostics(df_raw, df_processed, cycles, {}, stats)
    
    assert diag['rows_dropped'] == 20
    assert any("Significant data loss" in w for w in diag['warnings'])

def test_step8_metadata_diagnostics_short_capture():
    """Test warning for short capture length."""
    df_raw = pd.DataFrame({'Time': np.arange(10)})
    df_processed = df_raw.copy()
    cycles = [pd.DataFrame()] * 2 # < 3
    stats = {'data_quality_flag': 'OK'}
    
    diag = step8_metadata_diagnostics(df_raw, df_processed, cycles, {}, stats)
    
    assert diag['capture_length'] == 2
    assert any("Capture length too short" in w for w in diag['warnings'])

def test_step8_metadata_diagnostics_quality_integration():
    """Test integration of quality flags from stats."""
    df_raw = pd.DataFrame({'Time': np.arange(10)})
    df_processed = df_raw.copy()
    cycles = [pd.DataFrame()] * 5
    
    # Fail case
    stats_fail = {'data_quality_flag': 'fail'}
    diag_fail = step8_metadata_diagnostics(df_raw, df_processed, cycles, {}, stats_fail)
    assert any("Data quality is POOR" in w for w in diag_fail['warnings'])
    
    # Warning case
    stats_warn = {
        'data_quality_flag': 'warning',
        'nan_rate': 0.06,
        'outlier_count': 3
    }
    diag_warn = step8_metadata_diagnostics(df_raw, df_processed, cycles, {}, stats_warn)
    assert any("Data quality warning" in w for w in diag_warn['warnings'])
    assert "NaN rate 6.0%" in diag_warn['warnings'][0]
    assert "3 outliers detected" in diag_warn['warnings'][0]
