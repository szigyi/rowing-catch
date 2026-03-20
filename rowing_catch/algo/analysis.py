import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Internal helpers (detection primitives, unchanged)
# ---------------------------------------------------------------------------

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

    # Enforce minimum separation by clustering near-siblings and keeping the deepest trough in each cluster.
    filtered: list[int] = []

    cluster_start = 0
    for i in range(1, len(candidates)):
        if candidates[i] - candidates[i - 1] >= min_separation:
            cluster = candidates[cluster_start:i]
            best_idx = int(cluster[np.argmin(x[cluster])])
            if _is_valid_catch(x, best_idx, min_separation, prominence):
                filtered.append(best_idx)
            cluster_start = i

    # Last cluster
    cluster = candidates[cluster_start:]
    if cluster.size > 0:
        best_idx = int(cluster[np.argmin(x[cluster])])
        if _is_valid_catch(x, best_idx, min_separation, prominence):
            filtered.append(best_idx)

    return np.array(filtered, dtype=int)


def _is_valid_catch(x: np.ndarray,
                   idx: int,
                   min_separation: int,
                   prominence: float | None,
                   min_depth_ratio: float = 0.20):
    """Auxiliary catch-filter heuristics (robustness guard)."""
    if idx <= 0 or idx >= len(x) - 1:
        return False

    # Must be a true reversal point (strict local minimum condition).
    if not (x[idx - 1] > x[idx] < x[idx + 1]):
        return False

    if prominence is not None:
        left = max(0, idx - min_separation)
        right = min(len(x) - 1, idx + min_separation)
        neighborhood = np.r_[x[left:idx], x[idx + 1:right + 1]]
        if neighborhood.size > 0 and (neighborhood.min() - x[idx]) < prominence and (neighborhood.mean() - x[idx]) < prominence:
            return False

    # Reject shallow dips that are not a major cycle catch.
    global_amp = np.nanmax(x) - np.nanmin(x)
    low, high = np.nanmin(x), np.nanmax(x)
    mean_val = np.nanmean(x)

    if global_amp > 1e-8:
        left = max(0, idx - min_separation)
        right = min(len(x) - 1, idx + min_separation)
        neighborhood = np.r_[x[left:idx], x[idx + 1:right + 1]]
        if neighborhood.size > 0:
            local_max = np.nanmax(neighborhood)
            local_depth = local_max - x[idx]
            required_depth = min_depth_ratio * global_amp

            if idx <= min_separation or idx >= len(x) - 1 - min_separation:
                # Allow a bit more leeway near boundaries (avg-cycle pre-catch padding).
                required_depth = min(required_depth, 0.1 * global_amp)

            if local_depth < required_depth:
                return False

        # Reject extremes not consistent with catch location.
        if x[idx] > mean_val or x[idx] > low + 0.33 * global_amp:
            return False

    return True


def _is_valid_finish(x: np.ndarray,
                     idx: int,
                     min_separation: int,
                     prominence: float | None,
                     min_depth_ratio: float = 0.20):
    """Auxiliary finish-filter heuristics (robustness guard)."""
    if idx <= 0 or idx >= len(x) - 1:
        return False

    # Must be a true reversal point (strict local maximum condition).
    if not (x[idx - 1] < x[idx] > x[idx + 1]):
        return False

    if prominence is not None:
        left = max(0, idx - min_separation)
        right = min(len(x) - 1, idx + min_separation)
        neighborhood = np.r_[x[left:idx], x[idx + 1:right + 1]]
        if neighborhood.size > 0 and (x[idx] - neighborhood.max()) < prominence and (x[idx] - neighborhood.mean()) < prominence:
            return False

    # Reject shallow lumps that are not a major finish.
    global_amp = np.nanmax(x) - np.nanmin(x)
    low, high = np.nanmin(x), np.nanmax(x)
    mean_val = np.nanmean(x)

    if global_amp > 1e-8:
        left = max(0, idx - min_separation)
        right = min(len(x) - 1, idx + min_separation)
        neighborhood = np.r_[x[left:idx], x[idx + 1:right + 1]]
        if neighborhood.size > 0:
            local_min = np.nanmin(neighborhood)
            local_depth = x[idx] - local_min
            required_depth = min_depth_ratio * global_amp

            if idx <= min_separation or idx >= len(x) - 1 - min_separation:
                required_depth = min(required_depth, 0.1 * global_amp)

            if local_depth < required_depth:
                return False

        # Reject extremes not consistent with a finish location.
        if x[idx] < mean_val or x[idx] < high - 0.33 * global_amp:
            return False

    return True


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
    cluster_start = 0
    for i in range(1, len(candidates)):
        if candidates[i] - candidates[i - 1] >= min_separation:
            cluster = candidates[cluster_start:i]
            best_idx = int(cluster[np.argmax(x[cluster])])
            if _is_valid_finish(x, best_idx, min_separation, prominence):
                filtered.append(best_idx)
            cluster_start = i

    cluster = candidates[cluster_start:]
    if cluster.size > 0:
        best_idx = int(cluster[np.argmax(x[cluster])])
        if _is_valid_finish(x, best_idx, min_separation, prominence):
            filtered.append(best_idx)

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


# ---------------------------------------------------------------------------
# Pipeline step functions
# ---------------------------------------------------------------------------

# Column mapping used by step 1.
_COLUMN_MAP = {
    'Handle/0/X': 'Handle_X', 'Handle/0/Y': 'Handle_Y',
    'Shoulder/0/X': 'Shoulder_X', 'Shoulder/0/Y': 'Shoulder_Y',
    'Seat/0/X': 'Seat_X', 'Seat/0/Y': 'Seat_Y',
}

_COLS_TO_SMOOTH = ['Handle_X', 'Handle_Y', 'Shoulder_X', 'Shoulder_Y', 'Seat_X', 'Seat_Y']


def step1_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw tracker column names to clean internal names.

    Args:
        df: Raw input DataFrame as loaded from CSV.

    Returns:
        A new DataFrame with columns renamed according to the standard mapping.
        Columns not in the mapping are left unchanged.
    """
    return df.rename(columns=_COLUMN_MAP)


def step2_smooth(df: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """Apply a centred rolling-mean smoother to the six position columns.

    A centred window (``center=True``) is used so that detected peaks align
    with the actual event rather than being delayed by a half-window lag.
    Rows at the leading/trailing edges that contain NaN smoothed values are
    dropped.

    Args:
        df: DataFrame with renamed columns (output of :func:`step1_rename_columns`).
        window: Rolling window width in samples.

    Returns:
        DataFrame with ``*_Smooth`` columns added and NaN edge rows removed.
        Returns ``None`` if the result is empty after dropping NaN rows.
    """
    df = df.copy()
    for col in _COLS_TO_SMOOTH:
        if col in df.columns:
            df[f'{col}_Smooth'] = df[col].rolling(window, center=True).mean()

    smooth_cols = [f'{col}_Smooth' for col in _COLS_TO_SMOOTH if col in df.columns]
    df = df.dropna(subset=smooth_cols)
    return df if not df.empty else None


def step3_detect_catches(df: pd.DataFrame,
                         min_separation: int | None = None,
                         window: int = 10) -> tuple[pd.DataFrame, np.ndarray]:
    """Detect catch indices as local minima of Seat_X_Smooth.

    The catch is the point where the seat reaches its most forward position
    (minimum X) and reverses direction — the standard rowing catch definition.
    ``Seat_X_Smooth`` has exactly **one** local minimum per stroke, so this
    produces one catch detection per stroke cycle.

    ``Stroke_Compression`` (|Seat_X − Handle_X|) is also computed and stored
    on the DataFrame for diagnostic / visualisation purposes, but is **not**
    used for detection.  It was previously used for detection, which caused
    spurious double-detections because the compression is near-zero at both
    the catch *and* the finish (handle drawn back to seat level), yielding
    two minima per stroke.

    Args:
        df: Smoothed DataFrame (output of :func:`step2_smooth`).
        min_separation: Minimum number of samples between consecutive catches.
            Defaults to ``max(40, window * 4)``.
        window: Smoothing window used previously (needed to compute the default
            ``min_separation``).

    Returns:
        A tuple ``(df, catch_indices)`` where *df* has a new
        ``'Stroke_Compression'`` column (diagnostic only) and *catch_indices*
        is an integer ndarray of row positions within *df*.
    """
    if min_separation is None:
        min_separation = max(40, window * 4)

    df = df.copy()
    # Keep Stroke_Compression for diagnostic visualisation only.
    df['Stroke_Compression'] = np.abs(df['Seat_X_Smooth'] - df['Handle_X_Smooth'])

    # Use Seat_X_Smooth for detection: one minimum per stroke, exactly at the catch.
    catch_indices = _detect_catches_by_seat_reversal(
        df['Seat_X_Smooth'],
        min_separation=min_separation,
    )
    return df, catch_indices


def step4_segment_and_average(
    df: pd.DataFrame,
    catch_indices: np.ndarray,
    pre_catch_window: int = 10,
    window: int = 10,
) -> tuple[list[pd.DataFrame], pd.DataFrame, int] | None:
    """Split the data into per-stroke cycles and compute the average cycle.

    Each cycle runs from one catch to the next.  An optional
    ``pre_catch_window`` samples of data *before* the catch are prepended so
    that the catch event does not appear flush against the left edge of the
    chart.

    Args:
        df: Smoothed DataFrame with ``'Stroke_Compression'`` column (output of
            :func:`step3_detect_catches`).
        catch_indices: Integer ndarray of catch positions (output of
            :func:`step3_detect_catches`).
        pre_catch_window: Number of samples to include before each catch.
        window: Smoothing window (used to enforce a minimum cycle length).

    Returns:
        A tuple ``(cycles, avg_cycle, min_length)`` or ``None`` if fewer than
        one valid cycle could be extracted.

        * *cycles* – list of per-stroke DataFrames.
        * *avg_cycle* – element-wise mean DataFrame, indexed 0..min_length-1.
        * *min_length* – length of the shortest cycle (= length of avg_cycle).
    """
    pre_catch_window = int(max(0, pre_catch_window))
    cycles: list[pd.DataFrame] = []

    for i in range(len(catch_indices) - 1):
        catch_i = int(catch_indices[i])
        catch_next = int(catch_indices[i + 1])

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

    min_length = min(c.shape[0] for c in cycles)
    avg_cycle = (
        pd.concat([c.iloc[:min_length] for c in cycles])
        .groupby('Cycle_Index')
        .mean()
    )

    return cycles, avg_cycle, min_length


def step5_compute_metrics(
    avg_cycle: pd.DataFrame,
    window: int = 10,
) -> tuple[pd.DataFrame, int, int]:
    """Compute per-sample metrics on the averaged cycle.

    Adds the following columns to *avg_cycle* (in-place copy):

    * ``'Trunk_Angle'`` – signed degrees from vertical, accounting for rower
      orientation.
    * ``'Handle_X_Vel'`` – numerical gradient of ``Handle_X_Smooth``.
    * ``'Seat_X_Vel'`` – numerical gradient of ``Seat_X_Smooth``.
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

    avg_cycle['Handle_X_Vel'] = np.gradient(avg_cycle['Handle_X_Smooth'])
    avg_cycle['Seat_X_Vel'] = np.gradient(avg_cycle['Seat_X_Smooth'])

    # Re-detect catch on averaged cycle for precise alignment.
    avg_cycle['Stroke_Compression'] = np.abs(
        avg_cycle['Seat_X_Smooth'] - avg_cycle['Handle_X_Smooth']
    )
    catch_candidates_avg = _detect_catches_by_seat_reversal(
        avg_cycle['Seat_X_Smooth'],
        min_separation=max(5, window),
    )
    if catch_candidates_avg.size:
        # The avg cycle includes pre_catch_window data before the main stroke.
        # Choose the last detected catch to align on the true stroke event.
        catch_idx = int(catch_candidates_avg[-1])
    else:
        catch_idx = int(avg_cycle['Seat_X_Smooth'].idxmin())

    finish_idx = _pick_finish_index(avg_cycle, catch_idx=catch_idx, window=window)

    return avg_cycle, catch_idx, finish_idx


def step6_statistics(
    cycles: list[pd.DataFrame],
    min_length: int,
    catch_idx: int,
    finish_idx: int,
) -> dict:
    """Compute stroke-level statistics from the individual cycles.

    Args:
        cycles: List of per-stroke DataFrames (output of
            :func:`step4_segment_and_average`).
        min_length: Shortest cycle length, used as the total stroke length for
            ratio calculations.
        catch_idx: Catch position within the averaged stroke.
        finish_idx: Finish position within the averaged stroke.

    Returns:
        A dict with keys:

        * ``'cv_length'`` – coefficient of variation of stroke lengths (%).
        * ``'drive_len'`` – samples from catch to finish.
        * ``'recovery_len'`` – samples from finish to next catch.
        * ``'mean_duration'`` – average cycle length in samples.
    """
    stroke_lengths = [c['Seat_X_Smooth'].max() - c['Seat_X_Smooth'].min() for c in cycles]
    stroke_durations = [len(c) for c in cycles]
    cv_length = (np.std(stroke_lengths) / np.mean(stroke_lengths)) * 100

    drive_len = finish_idx - catch_idx
    recovery_len = min_length - drive_len

    return {
        'cv_length': cv_length,
        'drive_len': drive_len,
        'recovery_len': recovery_len,
        'mean_duration': np.mean(stroke_durations),
    }


# ---------------------------------------------------------------------------
# Public entry point (thin wrapper — interface unchanged)
# ---------------------------------------------------------------------------

def process_rowing_data(df: pd.DataFrame, pre_catch_window: int = 10) -> dict | None:
    """Run the full rowing-data processing pipeline and return analysis results.

    This is a convenience wrapper that chains the six pipeline step functions:

    1. :func:`step1_rename_columns`
    2. :func:`step2_smooth`
    3. :func:`step3_detect_catches`
    4. :func:`step4_segment_and_average`
    5. :func:`step5_compute_metrics`
    6. :func:`step6_statistics`

    Args:
        df: Raw input DataFrame loaded from the tracker CSV.
        pre_catch_window: Number of samples to include before each detected
            catch when forming individual stroke cycles.

    Returns:
        A results dict with keys ``'avg_cycle'``, ``'cycles'``, ``'catch_idx'``,
        ``'finish_idx'``, ``'cv_length'``, ``'drive_len'``, ``'recovery_len'``,
        ``'min_length'``, and ``'mean_duration'``.  Returns ``None`` if the data
        does not contain enough stroke cycles to analyse.
    """
    window = 10

    # Step 1
    df = step1_rename_columns(df)

    # Step 2
    df = step2_smooth(df, window=window)
    if df is None:
        return None

    # Step 3
    df, catch_indices = step3_detect_catches(df, window=window)
    if len(catch_indices) < 2:
        return None

    # Step 4
    result = step4_segment_and_average(df, catch_indices, pre_catch_window=pre_catch_window, window=window)
    if result is None:
        return None
    cycles, avg_cycle, min_length = result

    # Step 5
    avg_cycle, catch_idx, finish_idx = step5_compute_metrics(avg_cycle, window=window)

    # Step 6
    stats = step6_statistics(cycles, min_length, catch_idx, finish_idx)

    return {
        'avg_cycle': avg_cycle,
        'cycles': cycles,
        'catch_idx': catch_idx,
        'finish_idx': finish_idx,
        'min_length': min_length,
        **stats,
    }


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def get_traffic_light(value, ideal, yellow_threshold=15, green_threshold=5):
    """Return a (status, icon) tuple based on deviation from the ideal value.

    Args:
        value: Observed value.
        ideal: Target / ideal value.
        yellow_threshold: Max % deviation still considered Yellow.
        green_threshold: Max % deviation considered Green.

    Returns:
        Tuple of (status_string, emoji_icon).
    """
    deviation = abs(value - ideal) / ideal * 100
    if deviation <= green_threshold:
        return "Green", "✅"
    elif deviation <= yellow_threshold:
        return "Yellow", "⚠️"
    else:
        return "Red", "🚨"
