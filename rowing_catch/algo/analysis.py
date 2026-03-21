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
