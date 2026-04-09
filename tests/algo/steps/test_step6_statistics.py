import numpy as np
import pandas as pd

from rowing_catch.algo.steps.step6_statistics import _compute_phase_volume, step6_statistics


def test_step6_statistics_basic():
    """Test statistics computation with 3 identical clean cycles."""
    # Create 3 identical cycles
    # 51 samples, dt = 0.02s (50 Hz)
    # Total duration = 50 * 0.02 = 1.0s
    t = np.linspace(0, 1.0, 51)
    # Seat moves from 0 to 100 and back to 0.
    # Catch at 0, Finish at 25, Total length 51 samples.
    seat_x = 50 - 50 * np.cos(2 * np.pi * t)

    df = pd.DataFrame(
        {
            'Time': t,
            'Seat_X_Smooth': seat_x,
            'Handle_X_Smooth': seat_x * 1.5,
            'Shoulder_X_Smooth': seat_x * 1.2,
            'Handle_X_Vel': np.diff(seat_x * 1.5, prepend=seat_x[0] * 1.5),
            'Seat_X_Vel': np.diff(seat_x, prepend=seat_x[0]),
            'Shoulder_X_Vel': np.diff(seat_x * 1.2, prepend=seat_x[0] * 1.2),
        }
    )

    cycles = [df.copy(), df.copy(), df.copy()]
    min_length = 51
    catch_idx = 0
    finish_idx = 25

    stats = step6_statistics(cycles, min_length, catch_idx, finish_idx, df)

    assert stats['cv_length'] == 0.0  # Identical cycles
    assert stats['drive_len'] == 25
    assert stats['recovery_len'] == 26  # 51 - 25 = 26
    assert stats['mean_duration'] == 51.0

    # Temporal checks (from former Step 7)
    assert np.isclose(stats['sample_rate_hz'], 50.0)
    assert np.isclose(stats['cycle_duration_s'], 1.0)
    assert np.isclose(stats['drive_duration_s'], 0.5)
    assert np.isclose(stats['stroke_rate_spm'], 60.0)


def test_step6_statistics_no_time():
    """Test statistics without a Time column."""
    df = pd.DataFrame(
        {
            'Seat_X_Smooth': np.zeros(10),
            'Handle_X_Smooth': np.zeros(10),
            'Shoulder_X_Smooth': np.zeros(10),
        }
    )
    stats = step6_statistics([df, df, df], 10, 0, 5, df)

    assert stats['sample_rate_hz'] is None
    assert stats['stroke_rate_spm'] is None


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
