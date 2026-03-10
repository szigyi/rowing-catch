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

    # Candidates: handle velocity reversal (drive -> recovery) after catch.
    hvel = np.gradient(handle)
    rev = np.where((hvel[:-1] > 0) & (hvel[1:] <= 0))[0] + 1
    rev = rev[rev > catch_idx]

    # Add a small window *before* each reversal (finish happens just before handle moves back).
    # This helps when discrete sampling makes the sign change occur one or two samples late.
    pre = max(1, window // 4)
    if rev.size:
        rev = np.unique(np.clip(np.r_[rev, rev - pre, rev - 2 * pre], catch_idx + 1, n - 1))

    # Fallback candidates: seat reversal maxima after catch.
    seat_rev = _detect_finishes_by_seat_reversal(avg_cycle['Seat_X_Smooth'], min_separation=max(5, window))
    seat_rev = seat_rev[seat_rev > catch_idx]

    candidates = rev if rev.size else seat_rev
    if not candidates.size:
        # Last resort: global maxima after catch
        return int(catch_idx + np.argmax(seat[catch_idx:]))

    # Normalize signals for scoring.
    def _norm(x: np.ndarray) -> np.ndarray:
        lo = float(np.nanmin(x))
        hi = float(np.nanmax(x))
        if not np.isfinite(lo) or not np.isfinite(hi) or hi - lo < 1e-9:
            return np.zeros_like(x)
        return (x - lo) / (hi - lo)

    seat_n = _norm(seat)
    handle_n = _norm(handle)
    trunk_n = _norm(trunk)

    # Index of trunk peak (used as a soft anchor, not hard override).
    trunk_peak = int(np.nanargmax(trunk))

    # Score each candidate.
    best_i = int(candidates[0])
    best_score = -1e18

    # Tolerance scale in samples (handles smoothing drift).
    tol = max(2, window // 2)

    # Prefer candidates at or slightly before trunk peak (finish shouldn't be after max layback).
    for i in map(int, candidates):
        # Primary: being high on all three signals.
        score = 3.0 * seat_n[i] + 3.0 * handle_n[i] + 2.0 * trunk_n[i]

        # Prefer being close to trunk peak.
        dist = abs(i - trunk_peak)
        score += 2.0 * (1.0 - min(dist, 5 * tol) / float(5 * tol))

        # Penalize candidates after trunk peak (finish should be at/just before maximal layback).
        if i > trunk_peak:
            score -= 1.5 * min((i - trunk_peak) / float(tol), 3.0)

        # Prefer sharp handle reversal (strong negative acceleration right after).
        if i + 1 < n:
            score += 1.0 * max(0.0, -float(hvel[i + 1]))

        # Prefer candidates where seat is also near a local maximum (even if not exact reversal).
        if 1 <= i < n - 1:
            if seat[i] >= seat[i - 1] and seat[i] >= seat[i + 1]:
                score += 0.5

        # Penalize very early finishes too close to catch.
        score -= 0.5 * max(0, (catch_idx + tol) - i)

        if score > best_score:
            best_score = score
            best_i = i

    return int(best_i)


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
