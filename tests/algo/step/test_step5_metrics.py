import numpy as np
import pandas as pd

from rowing_catch.algo.step.step5_metrics import step5_compute_metrics


def test_step5_compute_metrics_basic():
    """Test metrics computation on a simple cycle."""
    # Create 101 samples (1 cycle)
    # Assume facing left (Handle_X < Seat_X at catch)
    # Create a cycle of 101 samples plus 10 samples of pre-catch padding
    # Total 111 samples. Catch should be at index 10.
    t_full = np.linspace(-0.1, 1.0, 111)

    seat_x = 550 - 50 * np.cos(2 * np.pi * t_full)
    handle_x = 300 + 100 * np.cos(2 * np.pi * t_full)
    seat_y = np.zeros(111) + 200
    shoulder_y = np.zeros(111) + 600
    shoulder_x = seat_x - 50 * np.cos(np.pi * t_full)

    df = pd.DataFrame(
        {
            'Time': t_full,
            'Seat_X_Smooth': seat_x,
            'Handle_X_Smooth': handle_x,
            'Seat_Y_Smooth': seat_y,
            'Shoulder_X_Smooth': shoulder_x,
            'Shoulder_Y_Smooth': shoulder_y,
        }
    )

    # Run metrics computation
    df_out, catch_idx, finish_idx = step5_compute_metrics(df, window=5)

    # 1. Row count preserved
    assert len(df_out) == len(df)

    # 2. Trunk Angle check
    # dy = 600 - 200 = 400.
    # At catch (t=0.0, idx=10): dx = shoulder_x - seat_x = -50.
    # Facing left: degrees(arctan2(-50, 400)) ~ -7.1 degrees
    expected_catch_angle = np.degrees(np.arctan2(-50, 400))
    assert np.isclose(df_out['Trunk_Angle'].iloc[10], expected_catch_angle)

    # At t=0.5 (idx=60): cos(pi*0.5)=0. dx = 0.
    assert np.isclose(df_out['Trunk_Angle'].iloc[60], 0.0)

    # At t=1.0 (idx=110): cos(pi)=-1. dx = 50.
    # Facing left: degrees(arctan2(50, 400)) ~ 7.1 degrees
    expected_end_angle = np.degrees(np.arctan2(50, 400))
    assert np.isclose(df_out['Trunk_Angle'].iloc[110], expected_end_angle)

    # 3. Velocity check
    # Seat velocity should be positive when moving rearward (t=0 to t=0.5, idx=10 to 60)
    # Give some buffer at the peaks
    assert (df_out['Seat_X_Vel'].iloc[15:55] > 0).all()
    # Handle velocity should be negative when pulling back (t=0 to t=0.5, idx=10 to 60)
    assert (df_out['Handle_X_Vel'].iloc[15:55] < 0).all()

    # 4. Catch/Finish indices
    # Catch should be at or near 10 (first true stroke reversal in padded cycle).
    expected_catch_idx = 10
    catch_tolerance = 1
    assert abs(catch_idx - expected_catch_idx) <= catch_tolerance, (
        f'catch_idx expected around {expected_catch_idx} +/- {catch_tolerance}, got {catch_idx}'
    )

    # Finish should align with the handle peak at index 10 in this synthetic cycle.
    # Tolerance of +/-2 accounts for small detection shift due to smoothing + velocity zero-crossing.
    expected_finish_idx = 10
    finish_tolerance = 2
    assert abs(finish_idx - expected_finish_idx) <= finish_tolerance, (
        f'finish_idx expected around {expected_finish_idx} +/- {finish_tolerance}, got {finish_idx}'
    )


def test_step5_compute_metrics_right_facing():
    """Test metrics computation for a right-facing rower."""
    # Facing right: Handle_X > Seat_X at catch
    t = np.linspace(0, 1.0, 101)
    # Seat at 500, Handle at 600 -> Handle > Seat -> Facing Right
    seat_x = 550 - 50 * np.cos(2 * np.pi * t)
    handle_x = 550 + 50 * np.cos(2 * np.pi * t)

    shoulder_y = np.zeros(101) + 600
    seat_y = np.zeros(101) + 200
    # Leaning forward to the right at catch (t=0): shoulder_x = seat_x + 50 = 550
    shoulder_x = seat_x + 50 * np.cos(np.pi * t)

    df = pd.DataFrame(
        {
            'Seat_X_Smooth': seat_x,
            'Handle_X_Smooth': handle_x,
            'Seat_Y_Smooth': seat_y,
            'Shoulder_X_Smooth': shoulder_x,
            'Shoulder_Y_Smooth': shoulder_y,
        }
    )

    df_out, _, _ = step5_compute_metrics(df, window=5)

    # At t=0 (catch): dx = 550 - 500 = 50.
    # Facing right: angle = degrees(arctan2(-dx, dy_abs)) = degrees(arctan2(-50, 400))
    expected_catch_angle = np.degrees(np.arctan2(-50, 400))
    assert np.isclose(df_out['Trunk_Angle'].iloc[0], expected_catch_angle)


def test_step5_compute_metrics_no_time():
    """Test that it works without a 'Time' column using default sample spacing."""
    data = {
        'Seat_X_Smooth': np.sin(np.linspace(0, 2 * np.pi, 100)),
        'Handle_X_Smooth': np.cos(np.linspace(0, 2 * np.pi, 100)),
        'Shoulder_X_Smooth': np.zeros(100),
        'Shoulder_Y_Smooth': np.zeros(100) + 1,
        'Seat_Y_Smooth': np.zeros(100),
    }
    df = pd.DataFrame(data)

    # Should not raise error
    df_out, _, _ = step5_compute_metrics(df)
    assert 'Handle_X_Vel' in df_out.columns


def test_step5_catch_recalculation():
    """Test that the catch index is recalculated (refined) on the averaged cycle.

    The averaged cycle typically includes pre-catch padding. The refinement
    should pick the actual reversal point near the end of that padding.
    """
    # Create a signal with two minima:
    # 1. A global minimum in the "padding" area (idx 5)
    # 2. A "true" catch reversal at idx 20
    # Seat_X: starts at 500, dips to 400 at t=5, returns to 500, dips to 410 at t=20, moves to 600
    seat_x = np.full(101, 500.0)
    seat_x[0:11] = 500 - 100 * np.sin(np.linspace(0, np.pi, 11))  # global min 400 at idx 5
    seat_x[15:26] = 500 - 90 * np.sin(np.linspace(0, np.pi, 11))  # local min 410 at idx 20
    seat_x[26:] = np.linspace(500, 600, 101 - 26)

    # Simple handle, shoulder, seat_y to satisfy step5
    handle_x = np.linspace(300, 400, 101)
    seat_y = np.zeros(101) + 200
    shoulder_y = np.zeros(101) + 600
    shoulder_x = np.zeros(101) + 500

    df = pd.DataFrame(
        {
            'Seat_X_Smooth': seat_x,
            'Handle_X_Smooth': handle_x,
            'Seat_Y_Smooth': seat_y,
            'Shoulder_X_Smooth': shoulder_x,
            'Shoulder_Y_Smooth': shoulder_y,
        }
    )

    # Run metrics computation with a window that allows both to be candidates
    # min_separation = max(5, window). If window=10, min_sep=10.
    # idx 5 and 20 are 15 apart, so both are detected as candidates.
    # step5_compute_metrics picks the LAST candidate: catch_idx = catch_candidates_avg[-1]
    df_out, catch_idx, finish_idx = step5_compute_metrics(df, window=10)

    # Refinement should pick the LAST catch candidate (idx 20)
    # instead of the global minimum (idx 5).
    assert catch_idx == 20
    assert catch_idx != df['Seat_X_Smooth'].idxmin()


def test_step5_finish_selection_with_multiple_candidates():
    """Test that _pick_finish_index selects the handle peak."""
    # Create 101 samples. Catch at 10.
    # Handle peaks at 80.
    seat_x = np.full(101, 300.0)
    # Peak at 40 (artifact)
    seat_x[30:51] = 300 + 100 * np.sin(np.linspace(0, np.pi, 21))
    # Peak at 70 (artifact)
    seat_x[60:81] = 300 + 90 * np.sin(np.linspace(0, np.pi, 21))

    handle_x = np.full(101, 100.0)
    # Handle peak at 80
    handle_x[70:91] = 100 + 100 * np.sin(np.linspace(0, np.pi, 21))

    trunk_angle = np.full(101, 0.0)
    # Trunk peak at 90
    trunk_angle[80:101] = 20 * np.sin(np.linspace(0, np.pi, 21))

    df = pd.DataFrame(
        {
            'Seat_X_Smooth': seat_x,
            'Handle_X_Smooth': handle_x,
            'Trunk_Angle': trunk_angle,
            'Seat_Y_Smooth': np.zeros(101),
            'Shoulder_X_Smooth': np.zeros(101) + 300,  # Start at 300
            'Shoulder_Y_Smooth': np.zeros(101) + 400,
        }
    )

    # Make Shoulder_X peak at 90 to get Trunk_Angle peak there
    df.loc[80:101, 'Shoulder_X_Smooth'] = 300 + 100 * np.sin(np.linspace(0, np.pi, 21))

    # Catch at index 10 (manually specify to avoid detection logic interference)
    df.loc[10, 'Seat_X_Smooth'] = 250.0  # Catch at 10

    # Run metrics computation
    df_out, catch_idx, finish_idx = step5_compute_metrics(df, window=5)

    # It should have picked the handle peak at 80
    assert finish_idx == 80
