import pandas as pd

from rowing_catch.algo.constants import REQUIRED_COLUMN_NAMES


def step1_rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename raw tracker column names to clean internal names.

    Args:
        df: Raw input DataFrame as loaded from CSV.

    Returns:
        A new DataFrame with columns renamed according to the standard mapping.
        Columns not in the mapping are left unchanged.
    """
    return df.rename(columns=REQUIRED_COLUMN_NAMES)