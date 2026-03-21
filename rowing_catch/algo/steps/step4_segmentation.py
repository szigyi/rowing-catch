import numpy as np
import pandas as pd


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
