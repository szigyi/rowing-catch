import numpy as np
import pandas as pd
from rowing_catch.algo.steps.step4_segmentation import step4_segment_and_average

def test_step4_segment_and_average_basic():
    """Test basic segmentation and averaging with 2 full cycles."""
    # Create 3 catch points at 50, 150, 250
    catches = np.array([50, 150, 250])
    
    # Create data: 300 samples
    # We'll use a simple signal that is different in each cycle to test averaging
    data = {
        'Handle_X': np.zeros(300),
        'Seat_X_Smooth': np.zeros(300),
        'Stroke_Compression': np.zeros(300)
    }
    
    # Cycle 1 (catch 50 to catch 150): 100 samples
    # Cycle 2 (catch 150 to catch 250): 100 samples
    
    # Fill with known values to verify averaging
    # Let's say we have a pre_catch_window of 10.
    # Cycle 1 will start at 40 and end at 150 (length 110).
    # Cycle 2 will start at 140 and end at 250 (length 110).
    
    for i in range(300):
        data['Handle_X'][i] = i % 100 # Periodic signal
        
    df = pd.DataFrame(data)
    
    pre_catch = 10
    window = 5
    result = step4_segment_and_average(df, catches, pre_catch_window=pre_catch, window=window)
    
    assert result is not None
    cycles, avg_cycle, min_length = result
    
    assert len(cycles) == 2
    assert min_length == 110 # (150-50) + 10 = 110
    
    # Verify first cycle boundaries
    # Cycle 1: starts at catch[0] - 10 = 40, ends at catch[1] = 150
    # Original indices 40..149
    np.testing.assert_allclose(cycles[0]['Handle_X'], df['Handle_X'].iloc[40:150])
    
    # Verify averaging
    # Since signals are identical in both cycles relative to catch, avg should match
    np.testing.assert_allclose(avg_cycle['Handle_X'], cycles[0]['Handle_X'])

def test_step4_segment_and_average_filtering():
    """Test that cycles shorter than min_length are filtered out."""
    # catch 10 to 20 (length 10) -> too short (min is 20 or window*3)
    # catch 50 to 100 (length 50) -> OK
    # catch 100 to 150 (length 50) -> OK
    catches = np.array([10, 20, 50, 100, 150])
    
    data = {'Handle_X': np.arange(200)}
    df = pd.DataFrame(data)
    
    window = 10 # min_length = max(20, 30) = 30
    result = step4_segment_and_average(df, catches, window=window)
    
    assert result is not None
    cycles, _, _ = result
    # Only 3 intervals: (10,20), (20,50), (50,100), (100,150)
    # (10,20) length 10 -> FAIL
    # (20,50) length 30 -> PASS (30 >= 30)
    # (50,100) length 50 -> PASS
    # (100,150) length 50 -> PASS
    assert len(cycles) == 3

def test_step4_segment_and_average_none():
    """Test that None is returned if no valid cycles are found."""
    # Only one catch -> no intervals
    catches = np.array([50])
    df = pd.DataFrame({'Handle_X': np.arange(100)})
    
    result = step4_segment_and_average(df, catches)
    assert result is None
    
    # Multiple catches but all too short
    catches_short = np.array([10, 15, 20])
    result_short = step4_segment_and_average(df, catches_short, window=10)
    assert result_short is None

def test_step4_segment_and_average_pre_catch_clipping():
    """Test that pre_catch_window is clipped at 0."""
    catches = np.array([10, 50])
    df = pd.DataFrame({'Handle_X': np.arange(100)})
    
    # pre_catch_window = 20, but catch is at index 10.
    # start = max(0, 10 - 20) = 0.
    # end = 50.
    # Total length 50.
    result = step4_segment_and_average(df, catches, pre_catch_window=20)
    assert result is not None
    cycles, _, min_length = result
    assert min_length == 50
    assert len(cycles[0]) == 50
