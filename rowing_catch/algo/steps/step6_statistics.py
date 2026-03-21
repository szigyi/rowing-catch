import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

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

