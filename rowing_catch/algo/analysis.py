import numpy as np
import pandas as pd


def _detect_catches_by_seat_reversal(seat_x: pd.Series,
                                    min_separation: int = 20,
                                    prominence: float | None = None) -> np.ndarray:
    """Detect catch indices as local minima of Seat_X.

    We model the catch as the point where the seat reaches its most forward position
    and reverses direction (end of recovery -> start of drive).

    Args:
        seat_x: smoothed Seat_X series.
        min_separation: minimum samples between consecutive catches.
        prominence: optional minimum depth vs. local neighborhood to filter noise.

    Returns:
        ndarray of integer indices into the *dataframe* (same index as seat_x).
    """
    x = seat_x.to_numpy(dtype=float)

    # Local minima where derivative changes from negative to positive.
    dx = np.diff(x)
    # Indices i where dx[i-1] < 0 and dx[i] >= 0. This corresponds to a minimum at i.
    candidates = np.where((dx[:-1] < 0) & (dx[1:] >= 0))[0] + 1

    if candidates.size == 0:
        return np.array([], dtype=int)

    # Enforce minimum separation by greedily taking earliest minima and skipping nearby ones.
    filtered: list[int] = []
    last = -10**9
    for idx in candidates:
        if idx - last < min_separation:
            continue
        if prominence is not None:
            # Simple prominence check: must be lower than neighbors by >= prominence.
            left = max(0, idx - min_separation)
            right = min(len(x) - 1, idx + min_separation)
            neighborhood = np.r_[x[left:idx], x[idx + 1:right + 1]]
            if neighborhood.size > 0:
                if (neighborhood.min() - x[idx]) < prominence and (neighborhood.mean() - x[idx]) < prominence:
                    continue
        filtered.append(int(idx))
        last = idx

    return np.array(filtered, dtype=int)


def _detect_finishes_by_seat_reversal(seat_x: pd.Series,
                                     min_separation: int = 20,
                                     prominence: float | None = None) -> np.ndarray:
    """Detect finish indices as local maxima of Seat_X.

    We model the finish as the point where the seat reaches its most rearward position
    and reverses direction (end of drive -> start of recovery).

    Args:
        seat_x: smoothed Seat_X series.
        min_separation: minimum samples between consecutive finishes.
        prominence: optional minimum height vs. neighborhood to filter noise.

    Returns:
        ndarray of integer indices into the dataframe (same index as seat_x).
    """
    x = seat_x.to_numpy(dtype=float)

    dx = np.diff(x)
    # Indices i where dx[i-1] > 0 and dx[i] <= 0. This corresponds to a maximum at i.
    candidates = np.where((dx[:-1] > 0) & (dx[1:] <= 0))[0] + 1

    if candidates.size == 0:
        return np.array([], dtype=int)

    filtered: list[int] = []
    last = -10**9
    for idx in candidates:
        if idx - last < min_separation:
            continue
        if prominence is not None:
            left = max(0, idx - min_separation)
            right = min(len(x) - 1, idx + min_separation)
            neighborhood = np.r_[x[left:idx], x[idx + 1:right + 1]]
            if neighborhood.size > 0:
                if (x[idx] - neighborhood.max()) < prominence and (x[idx] - neighborhood.mean()) < prominence:
                    continue
        filtered.append(int(idx))
        last = idx

    return np.array(filtered, dtype=int)


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

    n = len(avg_cycle)
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


def process_rowing_data(df, pre_catch_window: int = 10):
    # Column mapping
    column_map = {
        'Handle/0/X': 'Handle_X', 'Handle/0/Y': 'Handle_Y',
        'Shoulder/0/X': 'Shoulder_X', 'Shoulder/0/Y': 'Shoulder_Y',
        'Seat/0/X': 'Seat_X', 'Seat/0/Y': 'Seat_Y'
    }
    df = df.rename(columns=column_map)

    # Preprocessing & Smoothing
    window = 10
    cols_to_smooth = ['Handle_X', 'Handle_Y', 'Shoulder_X', 'Shoulder_Y', 'Seat_X', 'Seat_Y']
    for col in cols_to_smooth:
        if col in df.columns:
            df[f'{col}_Smooth'] = df[col].rolling(window).mean()

    # Drop rows with NaN from smoothing
    df = df.dropna(subset=[f'{col}_Smooth' for col in cols_to_smooth])

    # --- Stroke Detection (Seat reversal / catch detection) ---
    # Catch is approximated by the seat reaching a local minimum.
    # We pick minima that are sufficiently separated to represent consecutive strokes.
    seat = df['Seat_X_Smooth']
    # Min separation: based on smoothing window and typical sampling. Keep it permissive.
    catch_candidates = _detect_catches_by_seat_reversal(seat, min_separation=max(10, window * 2))

    if len(catch_candidates) < 2:
        return None  # Not enough data for cycles

    # Split into individual cycles between consecutive catches.
    # Optionally include a small lookback window before each catch to avoid plotting
    # strokes that start exactly at the catch (which visually pushes the catch line to
    # the left edge). This doesn't change catch/finish detection logic; it only affects
    # what segment is averaged/plotted.
    pre_catch_window = int(max(0, pre_catch_window))
    cycles = []
    for i in range(len(catch_candidates) - 1):
        catch_i = int(catch_candidates[i])
        catch_next = int(catch_candidates[i + 1])

        start = max(0, catch_i - pre_catch_window)
        end = catch_next
        if end - start < max(20, window * 3):
            continue

        cycle = df.iloc[start:end].copy()
        cycle.reset_index(drop=True, inplace=True)
        cycle.index.name = 'Cycle_Index'
        cycles.append(cycle)

    if len(cycles) < 1:
        return None

    # Standardize length for average cycle
    min_length = min(c.shape[0] for c in cycles)
    avg_cycle = pd.concat([c.iloc[:min_length] for c in cycles]).groupby('Cycle_Index').mean()

    # Metrics
    # Trunk Angle
    def calc_trunk_angle(row):
        dx = row['Shoulder_X_Smooth'] - row['Seat_X_Smooth']
        dy = row['Shoulder_Y_Smooth'] - row['Seat_Y_Smooth']
        return np.degrees(np.arctan2(dx, dy))

    avg_cycle['Trunk_Angle'] = avg_cycle.apply(calc_trunk_angle, axis=1)

    # Velocities
    avg_cycle['Handle_X_Vel'] = np.gradient(avg_cycle['Handle_X_Smooth'])
    avg_cycle['Seat_X_Vel'] = np.gradient(avg_cycle['Seat_X_Smooth'])

    # Catch and Finish (within the normalized/averaged stroke)
    catch_candidates_avg = _detect_catches_by_seat_reversal(
        avg_cycle['Seat_X_Smooth'],
        min_separation=max(5, window),
    )
    if catch_candidates_avg.size:
        catch_idx = int(catch_candidates_avg[0])
    else:
        catch_idx = int(avg_cycle['Seat_X_Smooth'].idxmin())

    finish_idx = _pick_finish_index(avg_cycle, catch_idx=catch_idx, window=window)

    # Consistency
    stroke_lengths = [c['Seat_X_Smooth'].max() - c['Seat_X_Smooth'].min() for c in cycles]
    stroke_durations = [len(c) for c in cycles]
    cv_length = (np.std(stroke_lengths) / np.mean(stroke_lengths)) * 100

    # Drive/Recovery
    drive_len = finish_idx - catch_idx
    recovery_len = min_length - drive_len

    results = {
        'avg_cycle': avg_cycle,
        'cycles': cycles,
        'catch_idx': catch_idx,
        'finish_idx': finish_idx,
        'cv_length': cv_length,
        'drive_len': drive_len,
        'recovery_len': recovery_len,
        'min_length': min_length,
        'mean_duration': np.mean(stroke_durations)
    }
    return results


def get_traffic_light(value, ideal, yellow_threshold=15, green_threshold=5):
    deviation = abs(value - ideal) / ideal * 100
    if deviation <= green_threshold:
        return "Green", "✅"
    elif deviation <= yellow_threshold:
        return "Yellow", "⚠️"
    else:
        return "Red", "🚨"
