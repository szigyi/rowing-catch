import pandas as pd

from rowing_catch.algo.constants import COLS_TO_SMOOTH


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
    for col in COLS_TO_SMOOTH:
        if col in df.columns:
            df[f'{col}_Smooth'] = df[col].rolling(window, center=True, min_periods=1).mean()

    return df