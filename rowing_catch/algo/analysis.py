import logging
import numpy as np
import pandas as pd

from rowing_catch.algo.helpers import _compute_signal_noise_ratio, _validate_with_secondary_signal
from rowing_catch.algo.steps.step0_validation import validate_input_df
from rowing_catch.algo.steps.step1_rename import step1_rename_columns
from rowing_catch.algo.steps.step2_smoothing import step2_smooth
from rowing_catch.algo.steps.step3_detection import step3_detect_catches
from rowing_catch.algo.steps.step4_segmentation import step4_segment_and_average
from rowing_catch.algo.steps.step5_metrics import step5_compute_metrics
from rowing_catch.algo.steps.step6_statistics import step6_statistics
from rowing_catch.algo.steps.step7_temporal import step7_temporal_metrics
from rowing_catch.algo.steps.step8_diagnostics import step8_metadata_diagnostics

logger = logging.getLogger(__name__)


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


# ---------------------------------------------------------------------------
# Internal helpers (detection primitives)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Public entry point
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
    time_metrics = step7_temporal_metrics(avg_cycle, catch_idx, finish_idx)

    # Metadata diagnostics (capture length, sampling stability, warnings)
    metadata = step8_metadata_diagnostics(df_raw, df, cycles, time_metrics, stats)

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
