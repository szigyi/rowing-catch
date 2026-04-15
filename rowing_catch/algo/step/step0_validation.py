import pandas as pd

from rowing_catch.algo.constants import REQUIRED_COLUMN_NAMES


def validate_input_df(df: pd.DataFrame) -> None:
    """Validate raw input before processing.

    Raises:
        TypeError: if df is not a pandas DataFrame.
        ValueError: if required columns are missing or non-numeric.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError('Input data must be a pandas DataFrame')
    if df.empty:
        raise ValueError('Input DataFrame is empty')

    required_cols = set(REQUIRED_COLUMN_NAMES.keys())
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError('Missing required raw input columns: {}'.format(', '.join(missing)))

    # Ensure required columns can be parsed to numeric
    for col in required_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            try:
                df[col] = pd.to_numeric(df[col], errors='raise')
            except Exception as exc:
                raise ValueError(f"Column '{col}' must be numeric or coercible to numeric") from exc
