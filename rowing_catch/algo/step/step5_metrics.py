import numpy as np
import pandas as pd

from rowing_catch.algo.helpers import _detect_catches_by_seat_reversal


def step5_compute_metrics(
    avg_cycle: pd.DataFrame,
    window: int = 10,
) -> tuple[pd.DataFrame, int, int]:
    """Compute per-sample metrics on the averaged cycle.

    Adds the following columns to *avg_cycle* (in-place copy):

    * ``'Trunk_Angle'`` – signed degrees from vertical, accounting for rower
      orientation.
    * ``'Handle_X_Vel'`` – numerical gradient of ``Handle_X_Smooth`` (mm/s).
    * ``'Seat_X_Vel'`` – numerical gradient of ``Seat_X_Smooth`` (mm/s).
    * ``'Stroke_Compression'`` – recomputed on the averaged cycle for precise
      catch/finish alignment.

    Args:
        avg_cycle: Averaged cycle DataFrame (output of
            :func:`step4_segment_and_average`).
        window: Smoothing window (used for catch detection on the avg cycle).

    Returns:
        A tuple ``(avg_cycle, catch_idx, finish_idx)`` where *avg_cycle* has
        the new metric columns and the two indices locate the catch and finish
        events within the averaged stroke.
    """
    avg_cycle = avg_cycle.copy()

    # Orientation: is handle left of seat at the catch?
    ref_catch = avg_cycle.iloc[0]
    is_facing_left = ref_catch['Handle_X_Smooth'] < ref_catch['Seat_X_Smooth']

    avg_cycle['Trunk_Angle'] = _compute_trunk_angles(avg_cycle, is_facing_left)

    # Calculate derivatives (Velocity -> Acceleration -> Jerk)
    # Using np.gradient which handles non-uniform time steps if 't' is provided.
    cols_to_derive = ['Handle_X', 'Seat_X', 'Shoulder_X']
    t = avg_cycle['Time'].to_numpy(dtype=float) if 'Time' in avg_cycle.columns else None

    # 1. Base tracked points
    for base in cols_to_derive:
        smooth_col = f'{base}_Smooth'
        if smooth_col not in avg_cycle.columns:
            continue

        # Velocity
        v_col = f'{base}_Vel'
        if t is not None:
            avg_cycle[v_col] = np.gradient(avg_cycle[smooth_col], t)
        else:
            avg_cycle[v_col] = np.gradient(avg_cycle[smooth_col])

        # Acceleration
        a_col = f'{base}_Accel'
        if t is not None:
            avg_cycle[a_col] = np.gradient(avg_cycle[v_col], t)
        else:
            avg_cycle[a_col] = np.gradient(avg_cycle[v_col])

        # Jerk
        j_col = f'{base}_Jerk'
        if t is not None:
            avg_cycle[j_col] = np.gradient(avg_cycle[a_col], t)
        else:
            avg_cycle[j_col] = np.gradient(avg_cycle[a_col])

    # 2. Derived Torso Proxy (Average of Seat and Shoulder)
    if 'Seat_X_Vel' in avg_cycle.columns and 'Shoulder_X_Vel' in avg_cycle.columns:
        avg_cycle['Rower_Vel'] = (avg_cycle['Seat_X_Vel'] + avg_cycle['Shoulder_X_Vel']) / 2
        if t is not None:
            avg_cycle['Rower_Accel'] = np.gradient(avg_cycle['Rower_Vel'], t)
            avg_cycle['Rower_Jerk'] = np.gradient(avg_cycle['Rower_Accel'], t)
        else:
            avg_cycle['Rower_Accel'] = np.gradient(avg_cycle['Rower_Vel'])
            avg_cycle['Rower_Jerk'] = np.gradient(avg_cycle['Rower_Accel'])
    elif 'Seat_X_Vel' in avg_cycle.columns:
        # Fallback if shoulder missing
        avg_cycle['Rower_Vel'] = avg_cycle['Seat_X_Vel']
        avg_cycle['Rower_Accel'] = avg_cycle['Seat_X_Accel']
        avg_cycle['Rower_Jerk'] = avg_cycle['Seat_X_Jerk']

    # --- Advanced Power Proxy (V^3 Model) ---
    avg_cycle = _compute_power_proxies(avg_cycle)

    # Re-detect catch on averaged cycle for precise alignment.
    avg_cycle['Stroke_Compression'] = np.abs(avg_cycle['Seat_X_Smooth'] - avg_cycle['Handle_X_Smooth'])
    catch_candidates_avg = _detect_catches_by_seat_reversal(
        avg_cycle['Seat_X_Smooth'],
        min_separation=max(5, window),
        seat_y=avg_cycle.get('Seat_Y_Smooth', None),
        min_depth_ratio=0.01,
    )
    if catch_candidates_avg.size:
        # The avg cycle includes pre_catch_window data before the main stroke.
        # Choose the last detected catch to align on the true stroke event.
        catch_idx = int(catch_candidates_avg[-1])
    else:
        catch_idx = int(avg_cycle['Seat_X_Smooth'].idxmin())

    finish_idx = _pick_finish_index(avg_cycle, catch_idx=catch_idx)

    return avg_cycle, catch_idx, finish_idx


def _pick_finish_index(avg_cycle: pd.DataFrame, catch_idx: int) -> int:
    """Desired finish definition (coaching oriented):
    - Handle is at/near its maximum (end of draw)
    - And it's right around the time the handle starts moving backwards
      (Handle_X velocity changes from positive to non-positive).

    Returns an integer index into avg_cycle.
    """
    handle = avg_cycle['Handle_X_Smooth'].to_numpy(dtype=float)
    n = len(avg_cycle)
    catch_idx = int(np.clip(int(catch_idx), 0, n - 1))
    # The finish is defined by the end of the pull, which is the peak of Handle_X.
    if n == 0:
        return int(catch_idx)

    # Compute the gradient only on the post-catch slice so that Handle_X values
    # from any pre-catch window (tail of the previous draw) do not pollute the
    # velocity signal and produce spurious zero-crossings before the true finish.
    post_handle = handle[catch_idx:]
    hvel_post = np.gradient(post_handle)

    handle_peak = catch_idx + int(np.nanargmax(post_handle))

    # Look for the velocity zero-crossing (positive to negative) in post-catch region
    rev_local = np.where((hvel_post[:-1] > 0) & (hvel_post[1:] <= 0))[0] + 1
    # Convert local (post-catch) indices back to full-array indices
    rev = rev_local + catch_idx
    rev_after_peak = rev[rev >= handle_peak - 5]  # Allow slightly before peak for edge cases

    handle_target = handle_peak
    if rev_after_peak.size:
        handle_target = int(rev_after_peak[0])
        # Refine to the actual peak sample if it's adjacent
        if handle_target - 1 > catch_idx and handle[handle_target - 1] > handle[handle_target]:
            handle_target = handle_target - 1

    return int(np.clip(handle_target, catch_idx + 1, n - 1))


def _compute_trunk_angles(df: pd.DataFrame, is_facing_left: bool) -> pd.Series:
    """Compute trunk angles for each row in the dataframe."""

    def _calc_angle(row):
        dx = row['Shoulder_X_Smooth'] - row['Seat_X_Smooth']
        # dy = Shoulder_Y - Seat_Y (Shoulder is higher, so dy is usually positive)
        dy = row['Shoulder_Y_Smooth'] - row['Seat_Y_Smooth']
        dy_abs = abs(dy)

        if is_facing_left:
            return np.degrees(np.arctan2(dx, dy_abs))
        else:
            return np.degrees(np.arctan2(-dx, dy_abs))

    return pd.Series(df.apply(_calc_angle, axis=1), dtype=float)


def _compute_power_proxies(df: pd.DataFrame) -> pd.DataFrame:
    """Compute segmental power proxies using a V^3 model.

    Power = Force * Velocity. For rowing, Force ~ Velocity^2 (drag).
    Thus, Technical Power Proxy = V_handle^2 * V_component.
    """
    v_h = df['Handle_X_Vel'].to_numpy()
    v_s = df['Seat_X_Vel'].to_numpy()

    # Drag Force Proxy is proportional to speed squared, maintaining direction of pull
    force_proxy = v_h * np.abs(v_h)

    df['Power_Total'] = force_proxy * v_h
    df['Power_Legs'] = force_proxy * v_s

    if 'Shoulder_X_Vel' in df.columns:
        v_sh = df['Shoulder_X_Vel'].to_numpy()
        df['Power_Trunk'] = force_proxy * (v_sh - v_s)
        df['Power_Arms'] = force_proxy * (v_h - v_sh)
    else:
        # Fallback if shoulder tracking is missing: assume non-leg power is "upper body"
        df['Power_Trunk'] = force_proxy * (v_h - v_s)
        df['Power_Arms'] = 0.0

    return df
