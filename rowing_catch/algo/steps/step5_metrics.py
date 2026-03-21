import numpy as np
import pandas as pd

from rowing_catch.algo.helpers import _detect_catches_by_seat_reversal, _detect_finishes_by_seat_reversal


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

    def _calc_trunk_angle(row):
        dx = row['Shoulder_X_Smooth'] - row['Seat_X_Smooth']
        dy = row['Shoulder_Y_Smooth'] - row['Seat_Y_Smooth']
        dy_abs = abs(dy)

        if is_facing_left:
            return np.degrees(np.arctan2(dx, dy_abs))
        else:
            return np.degrees(np.arctan2(-dx, dy_abs))

    avg_cycle['Trunk_Angle'] = avg_cycle.apply(_calc_trunk_angle, axis=1)

    if 'Time' in avg_cycle.columns:
        t = avg_cycle['Time'].to_numpy(dtype=float)
        if len(t) > 1 and np.all(np.diff(t) > 0):
            avg_cycle['Handle_X_Vel'] = np.gradient(avg_cycle['Handle_X_Smooth'], t)
            avg_cycle['Seat_X_Vel'] = np.gradient(avg_cycle['Seat_X_Smooth'], t)
        else:
            avg_cycle['Handle_X_Vel'] = np.gradient(avg_cycle['Handle_X_Smooth'])
            avg_cycle['Seat_X_Vel'] = np.gradient(avg_cycle['Seat_X_Smooth'])
    else:
        avg_cycle['Handle_X_Vel'] = np.gradient(avg_cycle['Handle_X_Smooth'])
        avg_cycle['Seat_X_Vel'] = np.gradient(avg_cycle['Seat_X_Smooth'])

    # Re-detect catch on averaged cycle for precise alignment.
    avg_cycle['Stroke_Compression'] = np.abs(
        avg_cycle['Seat_X_Smooth'] - avg_cycle['Handle_X_Smooth']
    )
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

    finish_idx = _pick_finish_index(avg_cycle, catch_idx=catch_idx, window=window)

    return avg_cycle, catch_idx, finish_idx


def _pick_finish_index(avg_cycle: pd.DataFrame,
                       catch_idx: int,
                       window: int = 10) -> int:
    """Pick finish index using multiple signals.

    Desired finish definition (coaching oriented):
    - Seat is at/near its maximum (rearward)
    - Handle is at/near its maximum (end of draw)
    - Trunk is at/near its maximum layback
    - And it's right around the time the handle starts moving backwards
      (Handle_X velocity changes from positive to non-positive).

    Returns an integer index into avg_cycle.
    """
    seat = avg_cycle['Seat_X_Smooth'].to_numpy(dtype=float)
    handle = avg_cycle['Handle_X_Smooth'].to_numpy(dtype=float)
    trunk = avg_cycle['Trunk_Angle'].to_numpy(dtype=float)

    # --- Refined detection using Seat_X reversal ---
    # Look for the finish on the avg_cycle (one major peak expected).
    # Use a lower depth ratio (0.01) for the averaged cycle since it is cleaner.
    fin_candidates = _detect_finishes_by_seat_reversal(
        avg_cycle['Seat_X_Smooth'],
        min_separation=max(10, window),
        seat_y=avg_cycle.get('Seat_Y_Smooth', None),
        min_depth_ratio=0.01
    )

    n = len(avg_cycle)
    catch_idx = int(np.clip(int(catch_idx), 0, n - 1))
    post = slice(catch_idx, n)

    if fin_candidates.size:
        after_catch = fin_candidates[fin_candidates > catch_idx]
        if after_catch.size:
            # If we have multiple candidates, pick the one that best matches
            # the handle and trunk peaks. Technical artifacts (humps) often
            # occur early in the drive.
            handle_peak = catch_idx + int(np.nanargmax(handle[post]))
            trunk_peak = catch_idx + int(np.nanargmax(trunk[post]))
            expected_finish = (handle_peak + trunk_peak) // 2

            # Pick the candidate closest to our expected finish zone.
            best_idx = after_catch[np.argmin(np.abs(after_catch - expected_finish))]
            return int(best_idx)

    # --- Fallback to Gradient-based approach ---
    if n == 0:
        return int(catch_idx)

    catch_idx = int(np.clip(int(catch_idx), 0, n - 1))

    post = slice(catch_idx, n)

    hvel = np.gradient(handle)

    handle_peak = catch_idx + int(np.nanargmax(handle[post]))

    rev = np.where((hvel[:-1] > 0) & (hvel[1:] <= 0))[0] + 1
    rev = rev[rev > catch_idx]
    rev_after_peak = rev[rev >= handle_peak]

    if rev_after_peak.size:
        fin = int(rev_after_peak[0])
        # Often the sign-change is detected one sample late; if previous sample is
        # closer to the peak, use that.
        if fin - 1 > catch_idx and handle[fin - 1] >= handle[fin]:
            fin = fin - 1
    else:
        # If we don't have an explicit reversal (very smooth data), start from handle peak.
        fin = int(np.clip(handle_peak, catch_idx + 1, n - 1))

    # Enforce "not still accelerating" expectation: hvel should be flat/decreasing.
    # Step back a few samples if needed.
    back_limit = max(catch_idx + 1, fin - max(3, window // 2))
    i = fin
    while i - 1 >= back_limit and hvel[i] > hvel[i - 1]:
        i -= 1

    fin = int(i)

    # Very small safeguard: keep finish near trunk peak after catch.
    trunk_peak = catch_idx + int(np.nanargmax(trunk[post]))
    if fin > trunk_peak + max(3, window // 2):
        fin = int(np.clip(trunk_peak, catch_idx + 1, n - 1))

    return int(fin)
