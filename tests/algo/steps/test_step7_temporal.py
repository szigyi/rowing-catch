import numpy as np
import pandas as pd
from rowing_catch.algo.steps.step7_temporal import step7_temporal_metrics

def test_step7_temporal_metrics_basic():
    """Test temporal metrics with a clean, strictly increasing Time column."""
    # 51 samples, dt = 0.02s (50 Hz)
    # Total duration = 50 * 0.02 = 1.0s
    t = np.linspace(0, 1.0, 51)
    df = pd.DataFrame({'Time': t})
    
    # catch at 0, finish at 25 (0.5s)
    catch_idx = 0
    finish_idx = 25
    
    metrics = step7_temporal_metrics(df, catch_idx, finish_idx)
    
    assert np.isclose(metrics['sample_rate_hz'], 50.0)
    assert np.isclose(metrics['cycle_duration_s'], 1.0)
    assert np.isclose(metrics['drive_duration_s'], 0.5)
    assert np.isclose(metrics['recovery_duration_s'], 0.5)
    assert np.isclose(metrics['stroke_rate_spm'], 60.0)

def test_step7_temporal_metrics_missing_time():
    """Test that metrics are None if Time column is missing."""
    df = pd.DataFrame({'Other': np.arange(10)})
    metrics = step7_temporal_metrics(df, 0, 5)
    
    assert metrics['sample_rate_hz'] is None
    assert metrics['stroke_rate_spm'] is None

def test_step7_temporal_metrics_invalid_time():
    """Test that metrics are None if Time is not strictly increasing."""
    # Non-monotonic time
    t = np.array([0, 0.1, 0.05, 0.2])
    df = pd.DataFrame({'Time': t})
    metrics = step7_temporal_metrics(df, 0, 1)
    assert metrics['sample_rate_hz'] is None
    
    # Time with NaNs
    t_nan = np.array([0, 0.1, np.nan, 0.3])
    df_nan = pd.DataFrame({'Time': t_nan})
    metrics_nan = step7_temporal_metrics(df_nan, 0, 1)
    assert metrics_nan['sample_rate_hz'] is None

def test_step7_temporal_metrics_boundary_checks():
    """Test boundary checks for catch and finish indices."""
    t = np.linspace(0, 1.0, 51)
    df = pd.DataFrame({'Time': t})
    
    # Valid indices
    m1 = step7_temporal_metrics(df, 0, 50)
    assert m1['drive_duration_s'] == 1.0
    
    # Invalid indices (out of bounds)
    m2 = step7_temporal_metrics(df, -1, 20)
    assert m2['drive_duration_s'] is None
    
    m3 = step7_temporal_metrics(df, 0, 100)
    assert m3['drive_duration_s'] is None
