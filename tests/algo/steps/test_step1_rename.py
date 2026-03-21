import pandas as pd
from rowing_catch.algo.steps.step1_rename import step1_rename_columns
from rowing_catch.algo.constants import REQUIRED_COLUMN_NAMES

def test_step1_rename_columns():
    """Test that columns are correctly renamed according to REQUIRED_COLUMN_NAMES."""
    # Create raw data with original tracker names
    raw_data = {col: [1.0, 2.0, 3.0] for col in REQUIRED_COLUMN_NAMES.keys()}
    # Add an extra column that shouldn't be touched
    raw_data['Extra'] = [10, 20, 30]
    
    df_raw = pd.DataFrame(raw_data)
    
    # Run the rename step
    df_renamed = step1_rename_columns(df_raw)
    
    # Check that expected columns exist in df_renamed
    for raw_col, clean_col in REQUIRED_COLUMN_NAMES.items():
        assert clean_col in df_renamed.columns
        assert (df_renamed[clean_col] == df_raw[raw_col]).all()
        
    # Check that the extra column is still there
    assert 'Extra' in df_renamed.columns
    assert (df_renamed['Extra'] == df_raw['Extra']).all()
    
    # Check that original tracker names are gone
    for raw_col in REQUIRED_COLUMN_NAMES.keys():
        if raw_col != REQUIRED_COLUMN_NAMES[raw_col]: # Handles self-mapping if any
            assert raw_col not in df_renamed.columns

def test_step1_rename_columns_input_unaffected():
    """Test that the input DataFrame is not modified in place."""
    raw_data = {col: [1.0] for col in REQUIRED_COLUMN_NAMES.keys()}
    df_raw = pd.DataFrame(raw_data)
    
    _ = step1_rename_columns(df_raw)
    
    # Original should still have original columns
    for col in REQUIRED_COLUMN_NAMES.keys():
        assert col in df_raw.columns
