import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def step8_metadata_diagnostics(
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
