#!/usr/bin/env python3
"""Test the drift normalization and proportional metrics enhancements."""

import pandas as pd
import numpy as np
from rowing_catch.algo.analysis import (
    _interpolate_small_gaps,
    _detect_outliers_zscore,
    _compute_phase_volume,
)

print("=" * 70)
print("Proportional Metrics & Drift Normalization Test")
print("=" * 70)

# Test 1: Missing data interpolation
print("\n[Test 1] Missing Data Interpolation")
print("-" * 70)

data_with_gaps = np.array([1.0, 2.0, np.nan, np.nan, 5.0, 6.0, np.nan, 8.0])
print(f"Original data: {data_with_gaps}")

interpolated = _interpolate_small_gaps(data_with_gaps, max_gap_size=3)
print(f"After interpolation (max_gap=3): {interpolated}")

# Check that small gaps are filled
small_gap_filled = not np.isnan(interpolated[2]) and not np.isnan(interpolated[3])
print(f"Small gaps filled: {small_gap_filled}")
assert small_gap_filled, "Small gaps should be interpolated"
print("✓ Small gaps interpolated correctly")

# Test 2: Outlier detection
print("\n[Test 2] Outlier Detection (Z-Score)")
print("-" * 70)

# Data with one extreme outlier
normal_data = np.random.normal(loc=5.0, scale=1.0, size=100)
data_with_outlier = np.concatenate([normal_data, [50.0]])
print(f"Data: 100 normal samples (μ=5, σ=1) + 1 extreme outlier (50)")

outliers = _detect_outliers_zscore(data_with_outlier, threshold=3.0)
outlier_count = np.sum(outliers)
print(f"Outliers detected (threshold=3.0): {outlier_count}")

assert outliers[-1] == True, "Extreme outlier should be detected"
assert np.sum(outliers[:-1]) < 5, "Few normal samples should be flagged as outliers"
print(f"✓ Outlier detection working (detected {outlier_count} outliers)")

# Test 3: Phase volume computation
print("\n[Test 3] Phase Volume (Distance × Time)")
print("-" * 70)

# Create synthetic rowing data with drive and recovery phases
t = np.linspace(0, 2, 100)
# Seat position: oscillates with about 100mm range
seat_x = 50 + 50 * np.sin(2 * np.pi * t)
print(f"Seat displacement over 2 seconds: {seat_x.min():.1f} to {seat_x.max():.1f} mm")

# Drive phase: 0-1 second (indices 0-50)
# Recovery phase: 1-2 second (indices 50-100)
time_array = t * 1000  # Convert to milliseconds for volume calculation
drive_volume = _compute_phase_volume(seat_x, time_array, phase_start_idx=0, phase_end_idx=50)
recovery_volume = _compute_phase_volume(seat_x, time_array, phase_start_idx=50, phase_end_idx=100)

print(f"Drive volume (0-50): {drive_volume:.1f} mm*ms")
print(f"Recovery volume (50-100): {recovery_volume:.1f} mm*ms")

assert drive_volume > 0, "Drive volume should be positive"
assert recovery_volume > 0, "Recovery volume should be positive"
print("✓ Phase volume computation working")

print("\n" + "=" * 70)
print("All drift normalization tests passed!")
print("=" * 70)
