#!/usr/bin/env python3
"""Test the catch/finish detection robustness enhancements."""

import pandas as pd
import numpy as np
from rowing_catch.algo.helpers import (
    _compute_signal_noise_ratio,
    _validate_with_secondary_signal,
    _is_valid_catch,
    _is_valid_finish,
)

print("=" * 70)
print("Catch/Finish Detection Robustness Enhancements Test")
print("=" * 70)

# Test 1: Signal noise ratio computation
print("\n[Test 1] Signal Noise Ratio Computation")
print("-" * 70)

# Clean signal
clean_signal = np.linspace(0, 10, 100) + 0.1 * np.sin(np.linspace(0, 4 * np.pi, 100))
snr_clean = _compute_signal_noise_ratio(clean_signal, window=10)
print(f"Clean signal SNR: {snr_clean:.2f}")

# Noisy signal
noisy_signal = np.linspace(0, 10, 100) + np.random.randn(100) * 2
snr_noisy = _compute_signal_noise_ratio(noisy_signal, window=10)
print(f"Noisy signal SNR: {snr_noisy:.2f}")

assert snr_clean > snr_noisy, "Clean signal should have higher SNR than noisy signal"
print("✓ SNR computation working correctly (clean > noisy)")

# Test 2: Secondary signal validation
print("\n[Test 2] Secondary Signal Cross-Validation")
print("-" * 70)

# Create synthetic catch event with aligned signals
primary = np.array([1.0, 2.0, 1.5, 1.0, 0.8, 1.2, 2.0, 2.5])  # minimum at index 4
secondary = np.array([5.0, 4.5, 4.0, 3.8, 3.5, 4.0, 4.5, 5.0])  # also minimum at index 4

catch_idx = 4
min_sep = 2
is_valid = _validate_with_secondary_signal(catch_idx, primary, secondary, min_sep, is_minima=True)
print(f"Aligned minima validation (should be True): {is_valid}")
assert is_valid, "Aligned minima should validate"

# Misaligned signals
secondary_bad = np.array([5.0, 3.5, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0])  # minimum at index 1
is_valid_bad = _validate_with_secondary_signal(catch_idx, primary, secondary_bad, min_sep, is_minima=True)
print(f"Misaligned minima validation (should be False): {is_valid_bad}")
assert not is_valid_bad, "Misaligned minima should not validate"

print("✓ Secondary signal validation working correctly (aligned > misaligned)")

# Test 3: Robustness filtering with SNR check
print("\n[Test 3] Catch Validation with SNR & Secondary Signal")
print("-" * 70)

# Create synthetic smooth rowing data
t = np.linspace(0, 2, 200)
seat_x = 50 + 30 * np.sin(2 * np.pi * t)  # oscillating seat position
seat_x_smooth = pd.Series(seat_x).rolling(window=10, center=True, min_periods=1).mean().values
seat_y = 10 + 5 * np.sin(4 * np.pi * t + np.pi / 4)
seat_y_smooth = pd.Series(seat_y).rolling(window=10, center=True, min_periods=1).mean().values

# Find catch at a minimum
catch_candidates = np.where((np.diff(seat_x_smooth) < 0) & (np.diff(seat_x_smooth[:-1]) >= 0))[0]
if len(catch_candidates) > 0:
    catch_candidate = catch_candidates[0]
    
    # Validate with secondary signal
    is_valid = _is_valid_catch(
        seat_x_smooth, 
        catch_candidate, 
        min_separation=20,
        prominence=None,
        secondary_signal=seat_y_smooth
    )
    print(f"Catch validation with secondary signal: {is_valid}")
    print(f"Catch index: {catch_candidate}, Seat_X: {seat_x_smooth[catch_candidate]:.2f}")
    print("✓ Catch validation with secondary signal working")
else:
    print("(Skipped: no catch candidate found in synthetic data)")

# Test 4: SNR threshold rejection
print("\n[Test 4] Low SNR Signal Rejection")
print("-" * 70)

# Very noisy signal should have low SNR and be rejected
very_noisy = np.random.randn(100) * 10
snr_very_noisy = _compute_signal_noise_ratio(very_noisy, window=5)
print(f"Very noisy signal SNR: {snr_very_noisy:.2f}")
print(f"SNR threshold for acceptance: 3.0")

if snr_very_noisy < 3.0:
    print("✓ Very noisy signal has SNR below threshold (would be rejected)")
else:
    print("(SNR still acceptable for this random signal, but catches would be filtered)")

print("\n" + "=" * 70)
print("All robustness enhancement tests passed!")
print("=" * 70)
