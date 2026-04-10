import numpy as np
import pandas as pd

from rowing_catch.algo.constants import PROCESSED_COLUMN_NAMES
from rowing_catch.algo.step.step2_smoothing import step2_smooth


def test_step2_smooth_adds_columns():
    """Test that *_Smooth columns are created for each processed column."""
    # Create data with some processed columns
    data = {col: [1.0, 2.0, 3.0, 4.0, 5.0] for col in PROCESSED_COLUMN_NAMES}
    df = pd.DataFrame(data)

    # Run the smoothing step
    df_smoothed = step2_smooth(df, window=3)

    # Check that expected columns exist
    for col in PROCESSED_COLUMN_NAMES:
        assert f'{col}_Smooth' in df_smoothed.columns

    # Check that original columns still exist
    for col in PROCESSED_COLUMN_NAMES:
        assert col in df_smoothed.columns


def test_step2_smooth_preserves_row_count():
    """Test that the number of rows is preserved."""
    data = {'Handle_X': np.arange(10)}
    df = pd.DataFrame(data)

    df_smoothed = step2_smooth(df, window=5)

    assert len(df_smoothed) == len(df)
    # Check for NaNs at boundaries - min_periods=1 should handle them
    assert not df_smoothed['Handle_X_Smooth'].isna().any()


def test_step2_smooth_linear_trend():
    """Test smoothing on a linear trend (rolling mean should preserve linear trends if centered)."""
    # For a linear sequence [0, 1, 2, 3, 4], a centered window of 3:
    # row 0: mean([0, 1]) = 0.5 (only 2 elements)
    # row 1: mean([0, 1, 2]) = 1.0
    # row 2: mean([1, 2, 3]) = 2.0
    # row 3: mean([2, 3, 4]) = 3.0
    # row 4: mean([3, 4]) = 3.5

    data = {'Handle_X': [0.0, 1.0, 2.0, 3.0, 4.0]}
    df = pd.DataFrame(data)

    df_smoothed = step2_smooth(df, window=3)

    expected_smooth = [0.5, 1.0, 2.0, 3.0, 3.5]
    np.testing.assert_allclose(df_smoothed['Handle_X_Smooth'], expected_smooth)


def test_step2_smooth_sinusoidal():
    """Test smoothing on a sinusoidal signal with multiple peaks and valleys."""
    # Create a sine wave: 2 full cycles (4 peaks/valleys total)
    t = np.linspace(0, 4 * np.pi, 100)
    clean_signal = np.sin(t)

    # Add some random noise
    np.random.seed(42)
    noise = np.random.normal(0, 0.2, size=len(t))
    noisy_signal = clean_signal + noise

    data = {'Handle_X': noisy_signal}
    df = pd.DataFrame(data)

    # Run smoothing with a window of 10
    window = 10
    df_smoothed = step2_smooth(df, window=window)
    smoothed_signal = df_smoothed['Handle_X_Smooth'].values

    # Verification:
    # 1. Row count preserved
    assert len(smoothed_signal) == len(noisy_signal)

    # 2. Noise reduction: the variance of the difference between
    # consecutive points should be lower in the smoothed signal.
    noisy_diff_var = float(np.var(np.diff(noisy_signal)))
    smoothed_diff_var = float(np.var(np.diff(np.asarray(smoothed_signal, dtype=float))))

    print(f'\nNoisy diff variance: {noisy_diff_var:.4f}')
    print(f'Smoothed diff variance: {smoothed_diff_var:.4f}')

    assert smoothed_diff_var < noisy_diff_var, 'Smoothed signal should be less jittery'

    # 3. Check that it still follows the general shape of the clean signal
    # (correlation should be high)
    correlation = float(np.corrcoef(clean_signal, np.asarray(smoothed_signal, dtype=float))[0, 1])
    print(f'Correlation with clean signal: {correlation:.4f}')
    assert correlation > 0.9, 'Smoothed signal should still follow the sine wave'


def test_step2_smooth_copy():
    """Test that the smoothing step returns a copy and doesn't modify input."""
    data = {'Handle_X': [1.0, 2.0, 3.0]}
    df = pd.DataFrame(data)

    df_smoothed = step2_smooth(df, window=3)

    # Input should not have smooth column
    assert 'Handle_X_Smooth' not in df.columns
    # Modifying output shouldn't affect input
    df_smoothed.iloc[0, 0] = 99.0
    assert df.iloc[0, 0] == 1.0


def test_step2_smooth_partial_columns():
    """Test that it only smoothes columns that are present."""
    # Only one of the processed columns is present
    data = {'Handle_X': [1.0, 2.0, 3.0], 'Other': [10, 20, 30]}
    df = pd.DataFrame(data)

    df_smoothed = step2_smooth(df, window=3)

    assert 'Handle_X_Smooth' in df_smoothed.columns
    # Shoulder_X_Smooth should NOT be created if Shoulder_X is missing
    assert 'Shoulder_X_Smooth' not in df_smoothed.columns
