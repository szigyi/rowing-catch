#!/usr/bin/env python3
"""Test the smoothing fix to verify row preservation."""

import pandas as pd
import numpy as np
from rowing_catch.algo.analysis import step2_smooth

# Create a small test dataset
np.random.seed(42)
test_data = {
    'Handle_X': np.random.rand(20),
    'Handle_Y': np.random.rand(20),
    'Shoulder_X': np.random.rand(20),
    'Shoulder_Y': np.random.rand(20),
    'Seat_X': np.random.rand(20),
    'Seat_Y': np.random.rand(20),
}
df_input = pd.DataFrame(test_data)

# Test smoothing
result = step2_smooth(df_input, window=5)

print("=" * 60)
print("Smoothing Fix Verification")
print("=" * 60)
print(f"Input rows:  {len(df_input)}")
print(f"Output rows: {len(result)}")
print(f"Rows preserved: {len(df_input) == len(result)}")
print(f"No NaN in Seat_X_Smooth: {result['Seat_X_Smooth'].notna().all()}")
print()

if len(df_input) == len(result) and result['Seat_X_Smooth'].notna().all():
    print("✓ SUCCESS: Smoothing preserves all rows (including edges) with no NaN values")
else:
    print("✗ FAILURE: Something went wrong with the smoothing fix")
    print(f"  Result shape: {result.shape}")
    print(f"  NaN count in Seat_X_Smooth: {result['Seat_X_Smooth'].isna().sum()}")

print()
print("Sample of smoothed values (first 5 rows):")
print(result[['Seat_X', 'Seat_X_Smooth']].head())
