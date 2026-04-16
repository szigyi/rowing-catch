import logging
from collections.abc import Sequence
from typing import overload

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def compute_trunk_angle_series(df: pd.DataFrame, is_facing_left: bool) -> pd.Series:
    """Compute trunk angle (degrees from vertical) for every row in *df*.

    This is the single source of truth for trunk angle geometry, shared by the
    pipeline (step5_metrics) and the per-cycle overlay computation
    (plot_transformer/trunk/cycle_utils).

    The angle is measured from the vertical through the seat, positive when the
    trunk leans in the direction the rower faces.  At the catch the rower leans
    forward so the value is negative.

    Args:
        df: DataFrame with columns ``Shoulder_X_Smooth``, ``Shoulder_Y_Smooth``,
            ``Seat_X_Smooth``, ``Seat_Y_Smooth``.
        is_facing_left: ``True`` when the handle is to the left of the seat at
            the catch (i.e. the rower faces left on screen).  Derived from
            ``results['is_facing_left']`` which is set by ``step5_compute_metrics``.

    Returns:
        A float Series of trunk angles, one per row, with the same index as *df*.
    """
    dx = df['Shoulder_X_Smooth'].to_numpy(dtype=float) - df['Seat_X_Smooth'].to_numpy(dtype=float)
    dy_abs = np.abs(df['Shoulder_Y_Smooth'].to_numpy(dtype=float) - df['Seat_Y_Smooth'].to_numpy(dtype=float))
    angles = np.degrees(np.arctan2(dx, dy_abs) if is_facing_left else np.arctan2(-dx, dy_abs))
    return pd.Series(angles, index=df.index, dtype=float)


def _detect_catches_by_seat_reversal(
    seat_x: pd.Series,
    min_separation: int = 20,
    prominence: float | None = None,
    seat_y: pd.Series | None = None,
    min_depth_ratio: float = 0.05,
) -> np.ndarray:
    """Detect catch indices as local minima of Seat_X.

    We model the catch as the point where the seat reaches its most forward position
    and reverses direction (end of recovery -> start of drive).

    Args:
        seat_x: smoothed Seat_X series (primary signal).
        min_separation: minimum samples between consecutive catches.
        prominence: optional minimum depth vs. local neighborhood to filter noise.
        seat_y: optional smoothed Seat_Y series for secondary validation.
        min_depth_ratio: minimum depth as ratio of signal amplitude (default 0.05).

    Returns:
        ndarray of integer indices into the *dataframe* (same index as seat_x).
    """
    x = seat_x.to_numpy(dtype=float)
    y = seat_y.to_numpy(dtype=float) if seat_y is not None else None

    # Local minima where derivative changes from negative to positive.
    dx = np.diff(x)
    # Indices i where dx[i-1] < 0 and dx[i] >= 0. This corresponds to a minimum at i.
    candidates = np.where((dx[:-1] < 0) & (dx[1:] >= 0))[0] + 1

    if candidates.size == 0:
        return np.array([], dtype=int)

    # Enforce minimum separation by clustering near-siblings and keeping the deepest trough in each cluster.
    filtered: list[int] = []

    cluster_start = 0
    for i in range(1, len(candidates)):
        if candidates[i] - candidates[i - 1] >= min_separation:
            cluster = candidates[cluster_start:i]
            best_idx = int(cluster[np.argmin(x[cluster])])
            if _is_valid_catch(x, best_idx, min_separation, prominence, min_depth_ratio=min_depth_ratio, secondary_signal=y):
                filtered.append(best_idx)
            cluster_start = i

    # Last cluster
    cluster = candidates[cluster_start:]
    if cluster.size > 0:
        best_idx = int(cluster[np.argmin(x[cluster])])
        if _is_valid_catch(x, best_idx, min_separation, prominence, min_depth_ratio=min_depth_ratio, secondary_signal=y):
            filtered.append(best_idx)

    return np.array(filtered, dtype=int)


def _is_valid_catch(
    x: np.ndarray,
    idx: int,
    min_separation: int,
    prominence: float | None,
    min_depth_ratio: float = 0.05,
    secondary_signal: np.ndarray | None = None,
    snr_threshold: float = 3.0,
):
    """Auxiliary catch-filter heuristics (robustness guard).

    Args:
        x: Primary signal (Seat_X_Smooth)
        idx: Candidate catch index
        min_separation: Minimum separation between detections
        prominence: Optional prominence threshold
        min_depth_ratio: Minimum depth as ratio of signal amplitude
        secondary_signal: Optional secondary signal (e.g., Seat_Y) for cross-validation
        snr_threshold: Minimum SNR to accept detection (reject if SNR too low)

    Returns:
        True if candidate passes all robustness checks
    """
    if idx <= 0 or idx >= len(x) - 1:
        logger.debug(f'Candidate catch at idx={idx} rejected: out of bounds.')
        return False

    # Check signal quality: reject if signal is too noisy
    snr = _compute_signal_noise_ratio(x, window=max(3, len(x) // 10))
    if snr < snr_threshold:
        logger.warning(f'Low SNR in primary signal for catch detection: SNR={snr:.2f} < {snr_threshold}')
        return False

    low, high = np.nanmin(x), np.nanmax(x)
    global_amp = high - low

    # 1. Basic properties check
    if not _is_basic_reversal_valid(x, idx, low, high, global_amp, is_minima=True):
        return False

    if global_amp > 1e-8:
        # 1. Basic shallow dip filter (Loose check vs max neighbor)
        if _is_shallow_peak(x, idx, min_separation, min_depth_ratio * global_amp, is_minima=True):
            logger.debug(f'Candidate catch at idx={idx} rejected: shallow dip.')
            return False

        # 2. Strict prominence/mean check (only if explicitly provided)
        if prominence is not None:
            left = max(0, idx - min_separation)
            right = min(len(x) - 1, idx + min_separation)
            neighborhood = np.r_[x[left:idx], x[idx + 1 : right + 1]]
            if neighborhood.size > 0:
                p_depth = float(np.nanmin(neighborhood) - x[idx])
                m_depth = float(np.nanmean(neighborhood) - x[idx])
                if p_depth < prominence and m_depth < prominence:
                    logger.debug(f'Candidate catch at idx={idx} rejected: insufficient prominence.')
                    return False

    # 3. Secondary signal validation
    return _validate_secondary_for_reversal(idx, secondary_signal, min_separation, snr, is_minima=True)


def _compute_signal_noise_ratio(signal: np.ndarray, window: int = 10) -> float:
    """Estimate signal-to-noise ratio using local variance.

    Assumes noise is primarily high-frequency. Uses rolling variance to estimate
    high-frequency components and compare to overall signal amplitude.

    Args:
        signal: 1D array of sample values
        window: Rolling window for local variance estimation

    Returns:
        Signal-to-noise ratio (SNR). Higher is better (cleaner signal).
        Returns 0 if signal is constant.
    """
    signal = np.asarray(signal, dtype=float)
    if signal.size < window + 1:
        return 0.0

    # Cap NaN handling but proceed if mostly valid
    valid_mask = ~np.isnan(signal)
    if valid_mask.sum() < window:
        return 0.0

    signal_clean = signal.copy()
    signal_clean[~valid_mask] = np.nanmean(signal)

    # Overall amplitude
    amp = np.nanmax(signal_clean) - np.nanmin(signal_clean)
    if amp < 1e-10:
        return 0.0

    # High-frequency energy (rolling std of differences)
    diff = np.diff(signal_clean)
    if len(diff) < 2:
        return 1000.0  # Effectively infinite for very short signals

    rolling_var = pd.Series(diff).rolling(window=max(2, window // 2), center=True).var().values
    if len(rolling_var) > 0 and not np.all(np.isnan(rolling_var)):
        high_freq_energy = float(np.nanmean(np.asarray(rolling_var, dtype=float)))
    else:
        # Fallback for very short signals: just use global variance of differences
        high_freq_energy = float(np.var(diff))

    # SNR = signal_amplitude / sqrt(noise_variance)
    if high_freq_energy > 0:
        snr = amp / np.sqrt(high_freq_energy)
    else:
        snr = amp / 1e-10

    return float(np.clip(snr, 0, 1000))


def _validate_with_secondary_signal(
    primary_idx: int, secondary_signal: np.ndarray, min_separation: int, is_minima: bool = True
) -> bool:
    """Cross-validate detection using a secondary signal.

    For a catch (primary = Seat_X minimum, secondary = Seat_Y minimum),
    both should show reversal at approximately the same location.

    Args:
        primary_idx: Detection index in primary signal
        secondary_signal: Secondary signal array (e.g., Seat_Y_Smooth)
        min_separation: Min separation between detections
        is_minima: True if detecting minima, False for maxima

    Returns:
        True if secondary signal confirms the detection (nearby reversal),
        False otherwise.
    """
    if len(secondary_signal) <= 1:
        logger.debug('Secondary signal too short for validation; assuming OK.')
        return True  # Can't validate; assume OK

    secondary = np.asarray(secondary_signal, dtype=float)
    search_window = max(min_separation // 2, 5)
    left = max(0, primary_idx - search_window)
    right = min(len(secondary), primary_idx + search_window + 1)

    if right - left < 3:
        logger.debug(f'Search window too small ({right - left} samples) for validation at idx={primary_idx}; assuming OK.')
        return True  # Window too small; can't validate

    segment = secondary[left:right]
    if np.nanmax(segment) - np.nanmin(segment) < 1e-8:
        logger.debug(f'Secondary signal is constant in search window at idx={primary_idx}; assuming OK.')
        return True  # Constant signal cannot validate; assume OK

    # Find reversal points in segment
    dx = np.diff(segment)
    if is_minima:
        reversals = np.where((dx[:-1] < 0) & (dx[1:] >= 0))[0] + 1
    else:
        reversals = np.where((dx[:-1] > 0) & (dx[1:] <= 0))[0] + 1

    # Any reversal in the segment validates the primary signal
    if len(reversals) > 0:
        logger.debug(f'Secondary signal confirms detection at idx={primary_idx} with reversals at local indices {reversals}.')
        return True

    return False


def _interpolate_small_gaps(series: np.ndarray, max_gap_size: int = 3) -> np.ndarray:
    """Fill small NaN gaps using linear interpolation.

    Args:
        series: 1D array with potential NaN values
        max_gap_size: Maximum consecutive NaN gap to interpolate

    Returns:
        Array with small gaps interpolated, larger gaps left as NaN
    """
    result = np.copy(series)
    mask = np.isnan(result)

    if not np.any(mask):
        return result

    # Find contiguous NaN regions
    diff = np.diff(np.concatenate(([False], mask, [False])).astype(int))
    gap_starts = np.where(diff == 1)[0]
    gap_ends = np.where(diff == -1)[0]

    for start, end in zip(gap_starts, gap_ends, strict=False):
        gap_size = end - start
        if gap_size <= max_gap_size:
            # Interpolate this small gap
            if start > 0 and end < len(result):
                result[start:end] = np.linspace(result[start - 1], result[end], gap_size + 2)[1:-1]
            elif start == 0 and end < len(result):
                result[start:end] = result[end]
            elif start > 0 and end == len(result):
                result[start:end] = result[start - 1]

    return result


def _is_valid_finish(
    x: np.ndarray,
    idx: int,
    min_separation: int,
    prominence: float | None,
    min_depth_ratio: float = 0.05,
    secondary_signal: np.ndarray | None = None,
    snr_threshold: float = 3.0,
):
    """Auxiliary finish-filter heuristics (robustness guard).

    Args:
        x: Primary signal (Seat_X_Smooth)
        idx: Candidate finish index
        min_separation: Minimum separation between detections
        prominence: Optional prominence threshold
        min_depth_ratio: Minimum depth as ratio of signal amplitude
        secondary_signal: Optional secondary signal (e.g., Seat_Y) for cross-validation
        snr_threshold: Minimum SNR to accept detection (reject if SNR too low)

    Returns:
        True if candidate passes all robustness checks
    """
    if idx <= 0 or idx >= len(x) - 1:
        logger.debug(f'Candidate finish at idx={idx} rejected: out of bounds.')
        return False

    # Check signal quality: reject if signal is too noisy
    snr = _compute_signal_noise_ratio(x, window=max(3, len(x) // 10))
    if snr < snr_threshold:
        logger.warning(f'Low SNR in primary signal for finish detection: SNR={snr:.2f} < {snr_threshold}')
        return False

    low, high = np.nanmin(x), np.nanmax(x)
    global_amp = high - low

    # 1. Basic properties check
    if not _is_basic_reversal_valid(x, idx, low, high, global_amp, is_minima=False):
        return False

    if global_amp > 1e-8:
        # 1. Basic shallow lump filter (Loose check vs min neighbor)
        if _is_shallow_peak(x, idx, min_separation, min_depth_ratio * global_amp, is_minima=False):
            logger.debug(f'Candidate finish at idx={idx} rejected: shallow lump.')
            return False

        # 2. Strict prominence/mean check (only if explicitly provided)
        if prominence is not None:
            left = max(0, idx - min_separation)
            right = min(len(x) - 1, idx + min_separation)
            neighborhood = np.r_[x[left:idx], x[idx + 1 : right + 1]]
            if neighborhood.size > 0:
                p_depth = float(x[idx] - np.nanmax(neighborhood))
                m_depth = float(x[idx] - np.nanmean(neighborhood))
                if p_depth < prominence and m_depth < prominence:
                    logger.debug(f'Candidate finish at idx={idx} rejected: insufficient prominence.')
                    return False

    # 3. Secondary signal validation
    return _validate_secondary_for_reversal(idx, secondary_signal, min_separation, snr, is_minima=False)


def _is_shallow_peak(x: np.ndarray, idx: int, min_separation: int, required_depth: float, is_minima: bool = True) -> bool:
    """Helper to check if a peak/trough is deep enough compared to its neighbors.

    Args:
        x: 1D signal array.
        idx: Index of the candidate reversal point.
        min_separation: Minimum samples to look for neighbors.
        required_depth: Minimum required depth for the peak/trough.
        is_minima: True if checking for a trough, False for a peak.

    Returns:
        True if the peak/trough is shallower than required_depth.
    """
    left = max(0, idx - min_separation)
    right = min(len(x) - 1, idx + min_separation)
    neighborhood = np.r_[x[left:idx], x[idx + 1 : right + 1]]

    if neighborhood.size == 0:
        return False

    if is_minima:
        # For a minimum, depth is how much higher the MOST distant neighbor is
        local_ref = np.nanmax(neighborhood)
        depth = local_ref - x[idx]
    else:
        # For a maximum, depth is how much lower the LEAST distant neighbor is
        local_ref = np.nanmin(neighborhood)
        depth = x[idx] - local_ref

    # Allow more leeway near boundaries (padding areas)
    if idx <= min_separation or idx >= len(x) - 1 - min_separation:
        global_amp = np.nanmax(x) - np.nanmin(x)
        required_depth = min(required_depth, 0.1 * global_amp)
    return bool(depth < required_depth)


def _is_basic_reversal_valid(x: np.ndarray, idx: int, low: float, high: float, global_amp: float, is_minima: bool) -> bool:
    """Check basic local extremum and range properties."""
    mean_val = np.nanmean(x)
    if is_minima:
        if not (x[idx - 1] > x[idx] < x[idx + 1]):
            return False
        # Catch must be in the lower portion of the global signal range
        if x[idx] > mean_val or x[idx] > low + 0.33 * global_amp:
            return False
    else:
        if not (x[idx - 1] < x[idx] > x[idx + 1]):
            return False
        # Finish must be in the upper portion of the global signal range
        if x[idx] < mean_val or x[idx] < high - 0.33 * global_amp:
            return False
    return True


def _validate_secondary_for_reversal(idx: int, secondary: np.ndarray | None, min_sep: int, snr: float, is_minima: bool) -> bool:
    """Cross-validate with secondary signal if provided."""
    if secondary is None:
        return True

    if not _validate_with_secondary_signal(idx, secondary, min_sep, is_minima):
        if snr < 15.0:
            logger.warning(f'Validation failed for idx={idx} (SNR={snr:.2f})')
            return False
        msg = f'Validation failed for idx={idx}, but primary SNR is high ({snr:.2f}). Proceeding.'
        logger.debug(msg)

    return True


@overload
def calculate_ideal_drive_rhythm(spm: float) -> float: ...


@overload
def calculate_ideal_drive_rhythm(spm: np.ndarray) -> np.ndarray: ...


@overload
def calculate_ideal_drive_rhythm(spm: Sequence[float]) -> np.ndarray: ...


def calculate_ideal_drive_rhythm(spm: float | np.ndarray | Sequence[float]) -> float | np.ndarray:
    """Calculate the ideal drive phase percentage for a given stroke rate (SPM).

    Based on "The Biomechanics of Rowing" (2nd revision), page 17, Figure 2.6.
    Returns the drive phase as a percentage of the total stroke cycle — i.e.
    how much of each stroke should be spent in the drive phase at this rate.

    Args:
        spm: Strokes per minute (scalar float, numpy array, or list).
             Typical range: 14-50 SPM for recreational to competitive rowing.

    Returns:
        Drive phase as a percentage (0–100) of the total stroke cycle.
        - If input is float, returns float
        - If input is array or list, returns np.ndarray
        At 15 SPM: ~32.6%
        At 30 SPM: ~48.3%
        At 40 SPM: ~53.6%

    Formula:
        drive_pct = (-0.000202 * spm² + 0.0195 * spm + 0.0793) * 100

    References:
        Coker, J. (2012). The Biomechanics of Rowing (2nd Revised Edition).
        Figure 2.6, page 17.
    """
    spm_arr = np.asarray(spm)  # type: ignore[no-untyped-call]

    # Quadratic coefficients from biomechanics literature (Figure 2.6)
    a = -0.000202
    b = 0.0195
    c = 0.0793

    pct: float | np.ndarray = (a * spm_arr**2 + b * spm_arr + c) * 100

    return pct.item() if np.ndim(pct) == 0 else pct  # type: ignore[union-attr]
