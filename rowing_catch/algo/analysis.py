import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Signal Quality & Robustness Helpers
# ---------------------------------------------------------------------------

def _compute_signal_noise_ratio(signal: np.ndarray, window: int = 10) -> float:
    """Estimate signal-to-noise ratio using local variance.

    Assumes noise is primarily high-frequency. Uses rolling variance to estimate
    high-frequency components and compare to overall signal amplitude.

    Args:
        signal: 1D array of sample values
        window: Rolling window for local variance estimation

    Returns:
        Signal-to-noise ratio (SNR). Higher is better (cleaner signal).
        Returns 0 if signal is constant.
    """
    signal = np.asarray(signal, dtype=float)
    if signal.size < window + 1:
        return 0.0

    # Cap NaN handling but proceed if mostly valid
    valid_mask = ~np.isnan(signal)
    if valid_mask.sum() < window:
        return 0.0

    signal_clean = signal.copy()
    signal_clean[~valid_mask] = np.nanmean(signal)

    # Overall amplitude
    amp = np.nanmax(signal_clean) - np.nanmin(signal_clean)
    if amp < 1e-10:
        return 0.0

    # High-frequency energy (rolling std of differences)
    diff = np.diff(signal_clean)
    rolling_var = pd.Series(diff).rolling(window=window // 2, center=True).var().values
    high_freq_energy = np.nanmean(rolling_var)

    # SNR = signal_amplitude / sqrt(noise_variance)
    if high_freq_energy > 0:
        snr = amp / np.sqrt(high_freq_energy)
    else:
        snr = amp / 1e-10

    return float(np.clip(snr, 0, 1000))


def _validate_with_secondary_signal(primary_idx: int,
                                   primary_signal: np.ndarray,
                                   secondary_signal: np.ndarray,
                                   min_separation: int,
                                   is_minima: bool = True) -> bool:
    """Cross-validate detection using a secondary signal.

    For a catch (primary = Seat_X minimum, secondary = Seat_Y minimum),
    both should show reversal at approximately the same location.

    Args:
        primary_idx: Detection index in primary signal
        primary_signal: Primary signal array (e.g., Seat_X_Smooth)
        secondary_signal: Secondary signal array (e.g., Seat_Y_Smooth)
        min_separation: Min separation between detections
        is_minima: True if detecting minima, False for maxima

    Returns:
        True if secondary signal confirms the detection (nearby reversal),
        False otherwise.
    """
    if len(secondary_signal) <= 1:
        return True  # Can't validate; assume OK

    secondary = np.asarray(secondary_signal, dtype=float)
    search_window = max(min_separation // 2, 5)
    left = max(0, primary_idx - search_window)
    right = min(len(secondary), primary_idx + search_window + 1)

    if right - left < 3:
        return True  # Window too small; can't validate

    segment = secondary[left:right]

    # Find reversal points in segment
    dx = np.diff(segment)
    if is_minima:
        reversals = np.where((dx[:-1] < 0) & (dx[1:] >= 0))[0] + 1
    else:
        reversals = np.where((dx[:-1] > 0) & (dx[1:] <= 0))[0] + 1

    # Any reversal in the segment validates the primary signal
    return len(reversals) > 0


# ---------------------------------------------------------------------------
# Signal Quality & Robustness Helpers (continued)
# ---------------------------------------------------------------------------

def _interpolate_small_gaps(series: np.ndarray, max_gap_size: int = 3) -> np.ndarray:
    """Fill small NaN gaps using linear interpolation.

    Args:
        series: 1D array with potential NaN values
        max_gap_size: Maximum consecutive NaN gap to interpolate

    Returns:
        Array with small gaps interpolated, larger gaps left as NaN
    """
    result = np.copy(series)
    mask = np.isnan(result)

    if not np.any(mask):
        return result

    # Find contiguous NaN regions
    gap_mask = np.concatenate(([0], np.diff(mask.astype(int)), [0]))
    gap_starts = np.where(gap_mask == 1)[0]
    gap_ends = np.where(gap_mask == -1)[0]

    for start, end in zip(gap_starts, gap_ends):
        gap_size = end - start
        if gap_size <= max_gap_size:
            # Interpolate this small gap
            if start > 0 and end < len(result):
                result[start:end] = np.linspace(result[start - 1], result[end], gap_size + 2)[1:-1]
            elif start == 0 and end < len(result):
                result[start:end] = result[end]
            elif start > 0 and end == len(result):
                result[start:end] = result[start - 1]

    return result


def _detect_outliers_zscore(series: np.ndarray, threshold: float = 3.0) -> np.ndarray:
    """Detect outliers using z-score method.

    Args:
        series: 1D array of values
        threshold: Z-score threshold (default: 3.0 = ~0.3% outliers in normal dist)

    Returns:
        Boolean array where True indicates outlier
    """
    series = np.asarray(series, dtype=float)
    valid_mask = ~np.isnan(series)

    if valid_mask.sum() < 2:
        return np.zeros_like(series, dtype=bool)

    valid_data = series[valid_mask]
    mean = np.mean(valid_data)
    std = np.std(valid_data)

    outliers = np.zeros_like(series, dtype=bool)
    if std > 1e-10:
        z_scores = np.abs((series - mean) / std)
        outliers = z_scores > threshold
    else:
        # No variation; mark extreme deviations from mean
        outliers = np.abs(series - mean) > 1e-6

    return outliers


def _compute_phase_volume(positions: np.ndarray,
                          times: np.ndarray | None,
                          phase_start_idx: int,
                          phase_end_idx: int) -> float:
    """Compute integrated distance * time for a phase (drive or recovery).

    Approximates the "volume" of movement during a phase using trapezoidal integration.

    Args:
        positions: Array of position samples (e.g., Seat_X_Smooth)
        times: Array of timestamps (optional; uses sample indices if None)
        phase_start_idx: Start index of phase
        phase_end_idx: End index of phase

    Returns:
        Phase volume in mm*seconds (or mm*samples if times not provided)
    """
    if phase_end_idx <= phase_start_idx or phase_end_idx > len(positions):
        return 0.0

    pos_segment = np.asarray(positions[phase_start_idx:phase_end_idx], dtype=float)
    if len(pos_segment) < 2 or np.all(np.isnan(pos_segment)):
        return 0.0

    if times is not None:
        times = np.asarray(times, dtype=float)
        time_segment = times[phase_start_idx:phase_end_idx]
        dt = np.diff(time_segment)
        # Skip if times are invalid
        if np.any(dt <= 0) or np.any(np.isnan(dt)):
            dt = np.ones(len(time_segment) - 1)
    else:
        dt = np.ones(len(pos_segment) - 1)

    # Integrate absolute displacement over time
    disp = np.abs(np.diff(pos_segment))
    volume = float(np.sum(disp * dt))

    return volume


# ---------------------------------------------------------------------------
# Internal helpers (detection primitives)
# ---------------------------------------------------------------------------

def _detect_catches_by_seat_reversal(seat_x: pd.Series,
                                    min_separation: int = 20,
                                    prominence: float | None = None,
                                    seat_y: pd.Series | None = None) -> np.ndarray:
    """Detect catch indices as local minima of Seat_X.

    We model the catch as the point where the seat reaches its most forward position
    and reverses direction (end of recovery -> start of drive).

    Args:
        seat_x: smoothed Seat_X series (primary signal).
        min_separation: minimum samples between consecutive catches.
        prominence: optional minimum depth vs. local neighborhood to filter noise.
        seat_y: optional smoothed Seat_Y series for secondary validation.

    Returns:
        ndarray of integer indices into the *dataframe* (same index as seat_x).
    """
    x = seat_x.to_numpy(dtype=float)
    y = seat_y.to_numpy(dtype=float) if seat_y is not None else None

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
            if _is_valid_catch(x, best_idx, min_separation, prominence, secondary_signal=y):
                filtered.append(best_idx)
            cluster_start = i

    # Last cluster
    cluster = candidates[cluster_start:]
    if cluster.size > 0:
        best_idx = int(cluster[np.argmin(x[cluster])])
        if _is_valid_catch(x, best_idx, min_separation, prominence, secondary_signal=y):
            filtered.append(best_idx)

    return np.array(filtered, dtype=int)


def _is_valid_catch(x: np.ndarray,
                   idx: int,
                   min_separation: int,
                   prominence: float | None,
                   min_depth_ratio: float = 0.20,
                   secondary_signal: np.ndarray | None = None,
                   snr_threshold: float = 3.0):
    """Auxiliary catch-filter heuristics (robustness guard).

    Args:
        x: Primary signal (Seat_X_Smooth)
        idx: Candidate catch index
        min_separation: Minimum separation between detections
        prominence: Optional prominence threshold
        min_depth_ratio: Minimum depth as ratio of signal amplitude
        secondary_signal: Optional secondary signal (e.g., Seat_Y) for cross-validation
        snr_threshold: Minimum SNR to accept detection (reject if SNR too low)

    Returns:
        True if candidate passes all robustness checks
    """
    if idx <= 0 or idx >= len(x) - 1:
        return False

    # Check signal quality: reject if signal is too noisy
    snr = _compute_signal_noise_ratio(x, window=max(3, len(x) // 10))
    if snr < snr_threshold:
        logger.warning(f"Low SNR in primary signal for catch detection: SNR={snr:.2f} < {snr_threshold}")
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

    # Cross-validate with secondary signal if provided
    if secondary_signal is not None:
        if not _validate_with_secondary_signal(idx, x, secondary_signal, min_separation, is_minima=True):
            logger.warning(f"Secondary signal validation failed for catch at idx={idx}")
            return False

    return True



def _is_valid_finish(x: np.ndarray,
                     idx: int,
                     min_separation: int,
                     prominence: float | None,
                     min_depth_ratio: float = 0.20,
                     secondary_signal: np.ndarray | None = None,
                     snr_threshold: float = 3.0):
    """Auxiliary finish-filter heuristics (robustness guard).

    Args:
        x: Primary signal (Seat_X_Smooth)
        idx: Candidate finish index
        min_separation: Minimum separation between detections
        prominence: Optional prominence threshold
        min_depth_ratio: Minimum depth as ratio of signal amplitude
        secondary_signal: Optional secondary signal (e.g., Seat_Y) for cross-validation
        snr_threshold: Minimum SNR to accept detection (reject if SNR too low)

    Returns:
        True if candidate passes all robustness checks
    """
    if idx <= 0 or idx >= len(x) - 1:
        return False

    # Check signal quality: reject if signal is too noisy
    snr = _compute_signal_noise_ratio(x, window=max(3, len(x) // 10))
    if snr < snr_threshold:
        logger.warning(f"Low SNR in primary signal for finish detection: SNR={snr:.2f} < {snr_threshold}")
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

    # Cross-validate with secondary signal if provided
    if secondary_signal is not None:
        if not _validate_with_secondary_signal(idx, x, secondary_signal, min_separation, is_minima=False):
            logger.warning(f"Secondary signal validation failed for finish at idx={idx}")
            return False

    return True



def _detect_finishes_by_seat_reversal(seat_x: pd.Series,
                                     min_separation: int = 20,
                                     prominence: float | None = None,
                                     seat_y: pd.Series | None = None) -> np.ndarray:
    """Detect finish indices as local maxima of Seat_X.

    We model the finish as the point where the seat reaches its most rearward position
    and reverses direction (end of drive -> start of recovery).

    Args:
        seat_x: smoothed Seat_X series (primary signal).
        min_separation: minimum samples between consecutive finishes.
        prominence: optional minimum height vs. neighborhood to filter noise.
        seat_y: optional smoothed Seat_Y series for secondary validation.

    Returns:
        ndarray of integer indices into the dataframe (same index as seat_x).
    """
    x = seat_x.to_numpy(dtype=float)
    y = seat_y.to_numpy(dtype=float) if seat_y is not None else None

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
            if _is_valid_finish(x, best_idx, min_separation, prominence, secondary_signal=y):
                filtered.append(best_idx)
            cluster_start = i

    cluster = candidates[cluster_start:]
    if cluster.size > 0:
        best_idx = int(cluster[np.argmax(x[cluster])])
        if _is_valid_finish(x, best_idx, min_separation, prominence, secondary_signal=y):
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


def validate_input_df(df: pd.DataFrame) -> None:
    """Validate raw input before processing.

    Raises:
        TypeError: if df is not a pandas DataFrame.
        ValueError: if required columns are missing or non-numeric.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input data must be a pandas DataFrame")
    if df.empty:
        raise ValueError("Input DataFrame is empty")

    required_cols = set(_COLUMN_MAP.keys())
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(
            "Missing required raw input columns: {}".format(
                ", ".join(missing)
            )
        )

    # Ensure required columns can be parsed to numeric
    for col in required_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            try:
                df[col] = pd.to_numeric(df[col], errors='raise')
            except Exception as exc:
                raise ValueError(
                    f"Column '{col}' must be numeric or coercible to numeric"
                ) from exc


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
    Uses ``min_periods=1`` to preserve all rows, including boundaries, by
    computing partial means at edges where fewer than ``window`` samples are available.

    Args:
        df: DataFrame with renamed columns (output of :func:`step1_rename_columns`).
        window: Rolling window width in samples.

    Returns:
        DataFrame with ``*_Smooth`` columns added. Row count is preserved.
    """
    df = df.copy()
    for col in _COLS_TO_SMOOTH:
        if col in df.columns:
            df[f'{col}_Smooth'] = df[col].rolling(window, center=True, min_periods=1).mean()

    return df


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
    # Pass Seat_Y_Smooth as secondary signal for robust validation.
    catch_indices = _detect_catches_by_seat_reversal(
        df['Seat_X_Smooth'],
        min_separation=min_separation,
        seat_y=df.get('Seat_Y_Smooth', None),
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


def _compute_temporal_metrics(
    avg_cycle: pd.DataFrame,
    catch_idx: int,
    finish_idx: int,
) -> dict:
    """Calculate temporal metrics and standard units for the averaged cycle."""
    metrics = {
        'sample_rate_hz': None,
        'cycle_duration_s': None,
        'drive_duration_s': None,
        'recovery_duration_s': None,
        'stroke_rate_spm': None,
    }

    if 'Time' not in avg_cycle.columns or len(avg_cycle) < 2:
        return metrics

    t = avg_cycle['Time'].to_numpy(dtype=float)
    if np.any(np.isnan(t)) or not np.all(np.diff(t) > 0):
        # Time column is not strictly increasing; skip temporal-derived metrics.
        return metrics

    dt = np.diff(t)
    if np.any(dt <= 0):
        return metrics

    sample_rate_hz = float(1.0 / np.median(dt))
    cycle_duration_s = float(t[-1] - t[0])

    if 0 <= int(catch_idx) < len(t) and 0 <= int(finish_idx) < len(t):
        drive_duration_s = float(max(0.0, t[int(finish_idx)] - t[int(catch_idx)]))
    else:
        drive_duration_s = None

    if drive_duration_s is not None:
        recovery_duration_s = float(max(0.0, cycle_duration_s - drive_duration_s))
    else:
        recovery_duration_s = None

    stroke_rate_spm = float(60.0 / cycle_duration_s) if cycle_duration_s > 0 else None

    metrics.update({
        'sample_rate_hz': sample_rate_hz,
        'cycle_duration_s': cycle_duration_s,
        'drive_duration_s': drive_duration_s,
        'recovery_duration_s': recovery_duration_s,
        'stroke_rate_spm': stroke_rate_spm,
    })

    return metrics


def _compute_metadata_diagnostics(
    df_raw: pd.DataFrame,
    df_processed: pd.DataFrame,
    cycles: list[pd.DataFrame],
    time_metrics: dict,
    stats: dict,
) -> dict:
    """Compute comprehensive metadata diagnostics for data quality and audit trails.

    Tracks sampling stability, capture length, row drops, and generates
    actionable warnings for coaches/analysts.

    Args:
        df_raw: Original raw input DataFrame (before processing).
        df_processed: Processed DataFrame (after smoothing, detection).
        cycles: List of detected cycles.
        time_metrics: Output from _compute_temporal_metrics().
        stats: Output from step6_statistics().

    Returns:
        A dict with metadata including:

        * ``'capture_length'`` – number of stroker cycles detected.
        * ``'sampling_is_stable'`` – boolean (CV of time deltas < 5%).
        * ``'sampling_cv'`` – coefficient of variation of sample rate (%).
        * ``'rows_dropped'`` – count of rows lost during processing.
        * ``'warnings'`` – list of actionable warning messages.
    """
    capture_length = len(cycles)
    sampling_is_stable = True
    sampling_cv = None
    rows_dropped = len(df_raw) - len(df_processed) if df_raw is not None else 0
    warnings = []

    # Sampling stability check
    if 'Time' in df_processed.columns and len(df_processed) > 2:
        t = df_processed['Time'].to_numpy(dtype=float)
        if np.all(np.diff(t) > 0):  # Strictly monotonic
            dt = np.diff(t)
            sampling_cv = (np.std(dt) / np.mean(dt)) * 100 if np.mean(dt) > 0 else None
            if sampling_cv is not None and sampling_cv > 5.0:
                sampling_is_stable = False
                warnings.append(f"Sampling frequency unstable: CV={sampling_cv:.1f}% (expected ~0-2%)")
                logger.warning(f"Sampling frequency unstable: {sampling_cv:.1f}%")

    # Capture length check
    if capture_length < 3:
        warnings.append(f"Capture length too short: {capture_length} cycles detected (expected ≥ 3)")
        logger.warning(f"Capture too short: {capture_length} cycles < 3 minimum")

    # Data quality warnings from stats
    if stats.get('data_quality_flag') == 'fail':
        warnings.append("Data quality is POOR: analysis results may be unreliable")
    elif stats.get('data_quality_flag') == 'warning':
        details = []
        if stats.get('nan_rate', 0) > 0.05:
            details.append(f"NaN rate {stats.get('nan_rate', 0):.1%}")
        if stats.get('outlier_count', 0) > 0:
            details.append(f"{stats.get('outlier_count')} outliers detected")
        if details:
            warnings.append(f"Data quality warning: {', '.join(details)}")

    # Row drops during processing
    if rows_dropped > 0:
        drop_pct = (rows_dropped / len(df_raw)) * 100 if len(df_raw) > 0 else 0
        if drop_pct > 10:
            warnings.append(f"Significant data loss during processing: {rows_dropped} rows dropped ({drop_pct:.1f}%)")
            logger.warning(f"High row drop rate: {drop_pct:.1f}%")

    return {
        'capture_length': capture_length,
        'sampling_is_stable': sampling_is_stable,
        'sampling_cv': sampling_cv,
        'rows_dropped': rows_dropped,
        'warnings': warnings,
    }


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
        * ``'drive_volume_mm_sec'`` – integrated drive phase displacement (mm*sec).
        * ``'recovery_volume_mm_sec'`` – integrated recovery phase displacement (mm*sec).
        * ``'outlier_count'`` – number of outlier samples detected in average cycle.
        * ``'nan_rate'`` – rate of NaN values in position columns (0-1).
        * ``'data_quality_flag'`` – 'OK', 'warning', or 'fail' based on diagnostics.
    """
    stroke_lengths = [c['Seat_X_Smooth'].max() - c['Seat_X_Smooth'].min() for c in cycles]
    stroke_durations = [len(c) for c in cycles]
    cv_length = (np.std(stroke_lengths) / np.mean(stroke_lengths)) * 100

    drive_len = finish_idx - catch_idx
    recovery_len = min_length - drive_len

    # Compute drive/recovery volume from the average cycle (cycles[0] is the average)
    drive_volume_mm_sec = 0.0
    recovery_volume_mm_sec = 0.0
    outlier_count = 0
    nan_rate = 0.0
    data_quality_flag = 'OK'

    if len(cycles) > 0:
        avg_cycle = cycles[0]

        # Drive/recovery volumes
        if 'Seat_X_Smooth' in avg_cycle.columns:
            seat_x = avg_cycle['Seat_X_Smooth'].to_numpy(dtype=float)
            times = None
            if 'Time' in avg_cycle.columns:
                times = avg_cycle['Time'].to_numpy(dtype=float)

            drive_volume_mm_sec = _compute_phase_volume(seat_x, times, catch_idx, finish_idx)
            recovery_volume_mm_sec = _compute_phase_volume(seat_x, times, finish_idx, min_length)

            # Outlier detection
            outliers = _detect_outliers_zscore(seat_x, threshold=3.0)
            outlier_count = int(np.sum(outliers))

        # NaN rate in position columns
        position_cols = ['Handle_X_Smooth', 'Handle_Y_Smooth', 'Seat_X_Smooth', 'Seat_Y_Smooth',
                         'Shoulder_X_Smooth', 'Shoulder_Y_Smooth']
        total_cells = 0
        nan_cells = 0
        for col in position_cols:
            if col in avg_cycle.columns:
                col_data = avg_cycle[col]
                total_cells += len(col_data)
                nan_cells += col_data.isna().sum()

        if total_cells > 0:
            nan_rate = float(nan_cells / total_cells)
        else:
            nan_rate = 0.0

        # Data quality flag
        if len(cycles) < 3:
            data_quality_flag = 'fail'
            logger.warning(f"Very few cycles detected ({len(cycles)} < 3): data quality may be poor")
        elif nan_rate > 0.1:
            data_quality_flag = 'fail'
            logger.warning(f"High NaN rate: {nan_rate:.1%} > 10%")
        elif nan_rate > 0.05 or outlier_count > len(cycles[0]) * 0.05:
            data_quality_flag = 'warning'
            logger.warning(f"Moderate data quality issues: NaN_rate={nan_rate:.1%}, outliers={outlier_count}")
        elif cv_length > 10:
            data_quality_flag = 'warning'
            logger.warning(f"High stroke length variability: CV={cv_length:.1f}% > 10%")
        else:
            data_quality_flag = 'OK'

    return {
        'cv_length': cv_length,
        'drive_len': drive_len,
        'recovery_len': recovery_len,
        'mean_duration': np.mean(stroke_durations),
        'drive_volume_mm_sec': drive_volume_mm_sec,
        'recovery_volume_mm_sec': recovery_volume_mm_sec,
        'outlier_count': outlier_count,
        'nan_rate': nan_rate,
        'data_quality_flag': data_quality_flag,
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
        ``'min_length'``, ``'mean_duration'``, ``'metadata'``, and temporal metrics.
        The ``'metadata'`` key contains diagnostics: ``'capture_length'``,
        ``'sampling_is_stable'``, ``'sampling_cv'``, ``'rows_dropped'``, ``'warnings'``.
        Returns ``None`` if the data does not contain enough stroke cycles to analyse.
    """
    window = 10

    # Save raw DataFrame for metadata tracking
    df_raw = df.copy()

    # Validate input data
    validate_input_df(df)

    # Step 1
    df = step1_rename_columns(df)

    # Step 2
    df = step2_smooth(df, window=window)

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

    # Temporal and unit-standarized metrics (using Time column if present)
    time_metrics = _compute_temporal_metrics(avg_cycle, catch_idx, finish_idx)

    # Metadata diagnostics (capture length, sampling stability, warnings)
    metadata = _compute_metadata_diagnostics(df_raw, df, cycles, time_metrics, stats)

    return {
        'avg_cycle': avg_cycle,
        'cycles': cycles,
        'catch_idx': catch_idx,
        'finish_idx': finish_idx,
        'min_length': min_length,
        **stats,
        **time_metrics,
        'metadata': metadata,
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
    elif deviation <= yellow_threshold:
        return "Yellow", "⚠️"
    else:
        return "Red", "🚨"
