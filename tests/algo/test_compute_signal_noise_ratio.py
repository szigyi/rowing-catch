"""Unit tests for the _compute_signal_noise_ratio helper function.

This module verifies that the SNR estimation works correctly for different
signal types, including constant, clean, noisy, and edge cases like short
signals or those with many NaNs.
"""
import numpy as np
import pytest
from rowing_catch.algo.helpers import _compute_signal_noise_ratio

def test_compute_snr_constant_signal():
    """Verify that a constant signal returns an SNR of 0.0."""
    signal = np.array([500.0] * 100)
    snr = _compute_signal_noise_ratio(signal)
    assert snr == 0.0

def test_compute_snr_clean_signal():
    """Verify that a perfectly clean linear signal returns the maximum clipped SNR."""
    # Linear signal should have low noise (variation of diffs is zero)
    signal = np.linspace(0, 100, 101)
    snr = _compute_signal_noise_ratio(signal)
    # Since high_freq_energy will be 0, snr will be amp / 1e-10 capped at 1000
    assert snr == 1000.0

def test_compute_snr_noisy_signal():
    """Verify that SNR decreases as noise is added to a clean signal."""
    np.random.seed(42)
    t = np.linspace(0, 2 * np.pi, 201)
    signal = 100 * np.sin(t)
    noise = np.random.normal(0, 5, 201)
    noisy_signal = signal + noise
    
    snr_clean = _compute_signal_noise_ratio(signal)
    snr_noisy = _compute_signal_noise_ratio(noisy_signal)
    
    assert snr_noisy < snr_clean
    assert snr_noisy > 0

def test_compute_snr_too_short():
    """Verify that signals shorter than the window return 0.0 SNR."""
    signal = np.array([1.0, 2.0, 3.0])
    snr = _compute_signal_noise_ratio(signal, window=10)
    assert snr == 0.0

def test_compute_snr_mostly_nans():
    """Verify that signals with too many NaNs return 0.0 SNR."""
    signal = np.array([1.0, np.nan, np.nan, np.nan, 5.0])
    snr = _compute_signal_noise_ratio(signal, window=4)
    assert snr == 0.0

def test_compute_snr_clipping():
    """Verify that the SNR result is clipped to a maximum value (e.g., 1000.0)."""
    signal = np.linspace(0, 1000, 100)
    snr = _compute_signal_noise_ratio(signal, window=5)
    assert snr <= 1000.0
