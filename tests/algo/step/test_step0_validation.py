from typing import Any, cast

import pandas as pd
import pytest

from rowing_catch.algo.constants import REQUIRED_COLUMN_NAMES
from rowing_catch.algo.step.step0_validation import validate_input_df


def test_validate_input_df_success():
    """Test successful validation with a valid DataFrame."""
    data = {col: [1.0, 2.0, 3.0] for col in REQUIRED_COLUMN_NAMES.keys()}
    df = pd.DataFrame(data)
    validate_input_df(df)


def test_validate_input_df_not_dataframe():
    """Test that TypeError is raised when input is not a DataFrame."""
    with pytest.raises(TypeError, match='Input data must be a pandas DataFrame'):
        validate_input_df(cast(Any, 'not a dataframe'))


def test_validate_input_df_empty():
    """Test that ValueError is raised when DataFrame is empty."""
    df = pd.DataFrame()
    with pytest.raises(ValueError, match='Input DataFrame is empty'):
        validate_input_df(df)


def test_validate_input_df_missing_columns():
    """Test that ValueError is raised when required columns are missing."""
    df = pd.DataFrame({'SomeOtherColumn': [1, 2, 3]})
    with pytest.raises(ValueError, match='Missing required raw input columns'):
        validate_input_df(df)


def test_validate_input_df_non_numeric():
    """Test that ValueError is raised when required columns are not numeric."""
    data = {col: [1.0, 2.0, 3.0] for col in REQUIRED_COLUMN_NAMES.keys()}
    data['Handle/0/X'] = cast(Any, ['one', 'two', 'three'])
    df = pd.DataFrame(data)
    with pytest.raises(ValueError, match='must be numeric or coercible to numeric'):
        validate_input_df(df)


def test_validate_input_df_coercible_to_numeric():
    """Test success when columns are strings but coercible to numeric."""
    data = {col: ['1.0', '2.0', '3.0'] for col in REQUIRED_COLUMN_NAMES.keys()}
    df = pd.DataFrame(data)
    # Should not raise any exception and should convert to numeric
    validate_input_df(df)
    for col in REQUIRED_COLUMN_NAMES.keys():
        assert pd.api.types.is_numeric_dtype(df[col])
