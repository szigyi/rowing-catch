import numpy as np
import pandas as pd

from rowing_catch.algo.steps.step3_detection import step3_detect_catches


def test_step3_detect_catches_basic():
    """Test catch detection on a simple sinusoidal seat movement."""
    # Create 3 cycles of seat movement (sinusoidal)
    # Using 301 points instead of 300 to avoid perfectly symmetric minima
    # that could lead to non-strict local minima (x[i] == x[i+1]).
    t = np.linspace(0, 6 * np.pi, 301)
    seat_x = 500 + 100 * np.cos(t)  # Minima at pi, 3pi, 5pi
    # Indices: 300 * (1/6) = 50, 300 * (3/6) = 150, 300 * (5/6) = 250

    handle_x = 500 + 150 * np.cos(t - 0.2)  # Handles slightly offset

    df = pd.DataFrame({'Seat_X_Smooth': seat_x, 'Handle_X_Smooth': handle_x})

    df_out, catches = step3_detect_catches(df, window=10)

    # Expected catches exactly at 50, 150, 250
    assert len(catches) == 3
    np.testing.assert_allclose(catches, [50, 150, 250])

    # Stroke_Compression should be added
    assert 'Stroke_Compression' in df_out.columns
    np.testing.assert_allclose(df_out['Stroke_Compression'], np.abs(seat_x - handle_x))


def test_step3_detect_catches_with_gaps():
    """Test that small gaps are interpolated before detection."""
    t = np.linspace(0, 6 * np.pi, 301)
    seat_x = 500 + 100 * np.cos(t)

    # Introduce a small gap (2 NaNs) near a catch
    seat_x[49:51] = np.nan

    df = pd.DataFrame(
        {
            'Seat_X_Smooth': seat_x,
            'Handle_X_Smooth': seat_x,  # handle same as seat for simplicity
        }
    )

    df_out, catches = step3_detect_catches(df, window=10)

    # Gaps should be filled in Seat_X_Smooth
    assert not np.isnan(df_out['Seat_X_Smooth'].iloc[49:51]).any()
    # Detection should still work correctly despite the initial gap,
    # though interpolation might shift the index slightly.
    assert len(catches) == 3
    assert any(abs(c - 50) <= 2 for c in catches)


def test_step3_detect_catches_min_separation():
    """Test that min_separation avoids double-detections for noisy signals."""
    t = np.linspace(0, 2 * np.pi, 101)
    # A single cycle with some noise creating a "double-dip" at the minimum
    seat_x = 500 + 100 * np.cos(t)
    # Ensure it's a valid cycle overall
    # With 101 points, minimum at pi is index 50.
    seat_x[49:52] = [400.1, 400.0, 400.0]  # Flat bottom
    # Wait, strictness requires x[idx-1] > x[idx] < x[idx+1]
    # Let's make it more realistic for double-detection: 400.2, 400.0, 400.1, 400.0, 400.2
    seat_x[48:53] = [400.2, 400.0, 400.1, 400.0, 400.2]

    df = pd.DataFrame({'Seat_X_Smooth': seat_x, 'Handle_X_Smooth': seat_x})

    # With reasonable min_separation (default), we should get only one
    _, catches_default = step3_detect_catches(df, window=10)  # default min_sep = 40
    assert len(catches_default) == 1
