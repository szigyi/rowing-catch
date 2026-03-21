import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def step7_diagnostics(
    df_raw: pd.DataFrame,
    df_processed: pd.DataFrame,
    cycles: list[pd.DataFrame],
    avg_cycle: pd.DataFrame,
    stats: dict,
) -> dict:
    """Compute comprehensive metadata diagnostics for data quality and audit trails.

    Tracks sampling stability, capture length, NaN rates, outliers, and generates
    actionable warnings for coaches/analysts.

    Args:
        df_raw: Original raw input DataFrame (before processing).
        df_processed: Processed DataFrame (after smoothing, detection).
        cycles: List of detected cycles.
        avg_cycle: The averaged cycle DataFrame.
        stats: Performance statistics from :func:`step6_statistics`.

    Returns:
        A dict with metadata including:

        * ``'capture_length'`` – number of stroke cycles detected.
        * ``'sampling_is_stable'`` – boolean (CV of time deltas < 5%).
        * ``'sampling_cv'`` – coefficient of variation of sample rate (%).
        * ``'rows_dropped'`` – count of rows lost during processing.
        * ``'nan_rate'`` – rate of NaN values in position columns (0-1).
        * ``'outlier_count'`` – number of outlier samples detected in average cycle.
        * ``'data_quality_flag'`` – 'OK', 'warning', or 'fail' based on diagnostics.
        * ``'warnings'`` – list of actionable warning messages.
    """
    capture_length = len(cycles)
    sampling_is_stable = True
    sampling_cv = None
    rows_dropped = len(df_raw) - len(df_processed) if df_raw is not None else 0
    warnings = []

    # 1. Sampling stability check
    if 'Time' in df_processed.columns and len(df_processed) > 2:
        t = df_processed['Time'].to_numpy(dtype=float)
        if np.all(np.diff(t) > 0):  # Strictly monotonic
            dt = np.diff(t)
            sampling_cv = (np.std(dt) / np.mean(dt)) * 100 if np.mean(dt) > 0 else None
            if sampling_cv is not None and sampling_cv > 5.0:
                sampling_is_stable = False
                warnings.append(f"Sampling frequency unstable: CV={sampling_cv:.1f}% (expected ~0-2%)")
                logger.warning(f"Sampling frequency unstable: {sampling_cv:.1f}%")

    # 2. NaN rate in position columns (from avg_cycle)
    position_cols = ['Handle_X_Smooth', 'Handle_Y_Smooth', 'Seat_X_Smooth', 'Seat_Y_Smooth',
                     'Shoulder_X_Smooth', 'Shoulder_Y_Smooth']
    total_cells = 0
    nan_cells = 0
    for col in position_cols:
        if col in avg_cycle.columns:
            col_data = avg_cycle[col]
            total_cells += len(col_data)
            nan_cells += col_data.isna().sum()

    nan_rate = float(nan_cells / total_cells) if total_cells > 0 else 0.0

    # 3. Outlier detection
    outlier_count = 0
    if 'Seat_X_Smooth' in avg_cycle.columns:
        seat_x = avg_cycle['Seat_X_Smooth'].to_numpy(dtype=float)
        outliers = _detect_outliers_zscore(seat_x, threshold=3.0)
        outlier_count = int(np.sum(outliers))

    # 4. Data quality flag determination
    cv_length = stats.get('cv_length', 0)
    
    if capture_length < 3:
        data_quality_flag = 'fail'
        warnings.append(f"Capture length too short: {capture_length} cycles detected (expected ≥ 3)")
        logger.warning(f"Capture too short: {capture_length} cycles < 3 minimum")
    elif nan_rate > 0.1:
        data_quality_flag = 'fail'
        warnings.append("Data quality is POOR: high NaN rate (unreliable results)")
        logger.warning(f"High NaN rate: {nan_rate:.1%} > 10%")
    elif nan_rate > 0.05 or outlier_count > len(avg_cycle) * 0.05:
        data_quality_flag = 'warning'
        details = []
        if nan_rate > 0.05: details.append(f"NaN rate {nan_rate:.1%}")
        if outlier_count > 0: details.append(f"{outlier_count} outliers")
        warnings.append(f"Data quality warning: {', '.join(details)}")
        logger.warning(f"Moderate data quality issues: NaN_rate={nan_rate:.1%}, outliers={outlier_count}")
    elif cv_length > 10:
        data_quality_flag = 'warning'
        warnings.append(f"High stroke length variability: CV={cv_length:.1f}% (expected < 10%)")
        logger.warning(f"High stroke length variability: CV={cv_length:.1f}% > 10%")
    else:
        data_quality_flag = 'OK'

    # 5. Row drops during processing
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
        'nan_rate': nan_rate,
        'outlier_count': outlier_count,
        'data_quality_flag': data_quality_flag,
        'warnings': warnings,
    }


def _detect_outliers_zscore(series: np.ndarray, threshold: float = 3.0) -> np.ndarray:
    """Detect outliers using z-score method."""
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
        outliers = np.abs(series - mean) > 1e-6

    return outliers
