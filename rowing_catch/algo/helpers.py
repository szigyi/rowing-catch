import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def _detect_catches_by_seat_reversal(seat_x: pd.Series,
                                    min_separation: int = 20,
                                    prominence: float | None = None,
                                    seat_y: pd.Series | None = None,
                                    min_depth_ratio: float = 0.05) -> np.ndarray:
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
            if _is_valid_catch(x, best_idx, min_separation, prominence, 
                              min_depth_ratio=min_depth_ratio, secondary_signal=y):
                filtered.append(best_idx)
            cluster_start = i

    # Last cluster
    cluster = candidates[cluster_start:]
    if cluster.size > 0:
        best_idx = int(cluster[np.argmin(x[cluster])])
        if _is_valid_catch(x, best_idx, min_separation, prominence, 
                          min_depth_ratio=min_depth_ratio, secondary_signal=y):
            filtered.append(best_idx)

    return np.array(filtered, dtype=int)


def _is_valid_catch(x: np.ndarray,
                   idx: int,
                   min_separation: int,
                   prominence: float | None,
                   min_depth_ratio: float = 0.05,
                   secondary_signal: np.ndarray | None = None,
                   snr_threshold: float = 3.0):
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
        logger.debug(f"Candidate catch at idx={idx} rejected: out of bounds.")
        return False

    # Check signal quality: reject if signal is too noisy
    snr = _compute_signal_noise_ratio(x, window=max(3, len(x) // 10))
    if snr < snr_threshold:
        logger.warning(f"Low SNR in primary signal for catch detection: SNR={snr:.2f} < {snr_threshold}")
        return False

    # Must be a true reversal point (strict local minimum condition).
    if not (x[idx - 1] > x[idx] < x[idx + 1]):
        logger.debug(f"Candidate catch at idx={idx} rejected: not a strict local minimum (x[idx-1]={x[idx-1]:.2f}, x[idx]={x[idx]:.2f}, x[idx+1]={x[idx+1]:.2f}).")
        return False

    if prominence is not None:
        left = max(0, idx - min_separation)
        right = min(len(x) - 1, idx + min_separation)
        neighborhood = np.r_[x[left:idx], x[idx + 1:right + 1]]
        if neighborhood.size > 0 and (neighborhood.min() - x[idx]) < prominence and (neighborhood.mean() - x[idx]) < prominence:
            logger.debug(f"Candidate catch at idx={idx} rejected: insufficient prominence (neighborhood min diff={neighborhood.min() - x[idx]:.2f}, mean diff={neighborhood.mean() - x[idx]:.2f}, required={prominence}).")
            return False

    # Reject shallow dips that are not a major cycle catch.
    global_amp = np.nanmax(x) - np.nanmin(x)
    low, high = np.nanmin(x), np.nanmax(x)
    mean_val = np.nanmean(x)

    if global_amp > 1e-8:
        left = max(0, idx - min_separation)
        right = min(len(x) - 1, idx + min_separation)
        neighborhood = np.r_[x[left:idx], x[idx + 1:right + 1]]
        if neighborhood.size > 0:
            local_max = np.nanmax(neighborhood)
            local_depth = local_max - x[idx]
            required_depth = min_depth_ratio * global_amp

            if idx <= min_separation or idx >= len(x) - 1 - min_separation:
                # Allow a bit more leeway near boundaries (avg-cycle pre-catch padding).
                required_depth = min(required_depth, 0.1 * global_amp)

            if local_depth < required_depth:
                logger.debug(f"Candidate catch at idx={idx} rejected: shallow dip (depth={local_depth:.2f} < required={required_depth:.2f}).")
                return False

        # Reject extremes not consistent with catch location.
        if x[idx] > mean_val or x[idx] > low + 0.33 * global_amp:
            logger.debug(f"Candidate catch at idx={idx} rejected: too high in signal range (val={x[idx]:.2f}, mean={mean_val:.2f}, limit={low + 0.33 * global_amp:.2f}).")
            return False

    # Cross-validate with secondary signal if provided
    if secondary_signal is not None:
        if not _validate_with_secondary_signal(idx, secondary_signal, min_separation, is_minima=True):
            if snr < 15.0:
                logger.warning(f"Secondary signal validation failed for catch at idx={idx} (SNR={snr:.2f})")
                return False
            else:
                logger.debug(f"Secondary signal validation failed for catch at idx={idx}, but primary SNR is high ({snr:.2f}). Proceeding.")

    return True


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
        return 1000.0 # Effectively infinite for very short signals
        
    rolling_var = pd.Series(diff).rolling(window=max(2, window // 2), center=True).var().values
    if len(rolling_var) > 0 and not np.all(np.isnan(rolling_var)):
        high_freq_energy = np.nanmean(rolling_var)
    else:
        # Fallback for very short signals: just use global variance of differences
        high_freq_energy = np.var(diff)

    # SNR = signal_amplitude / sqrt(noise_variance)
    if high_freq_energy > 0:
        snr = amp / np.sqrt(high_freq_energy)
    else:
        snr = amp / 1e-10

    return float(np.clip(snr, 0, 1000))


def _validate_with_secondary_signal(primary_idx: int,
                                    secondary_signal: np.ndarray,
                                    min_separation: int,
                                    is_minima: bool = True) -> bool:
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
        logger.debug("Secondary signal too short for validation; assuming OK.")
        return True  # Can't validate; assume OK

    secondary = np.asarray(secondary_signal, dtype=float)
    search_window = max(min_separation // 2, 5)
    left = max(0, primary_idx - search_window)
    right = min(len(secondary), primary_idx + search_window + 1)

    if right - left < 3:
        logger.debug(f"Search window too small ({right-left} samples) for validation at idx={primary_idx}; assuming OK.")
        return True  # Window too small; can't validate

    segment = secondary[left:right]
    if np.nanmax(segment) - np.nanmin(segment) < 1e-8:
        logger.debug(f"Secondary signal is constant in search window at idx={primary_idx}; assuming OK.")
        return True  # Constant signal cannot validate; assume OK

    # Find reversal points in segment
    dx = np.diff(segment)
    if is_minima:
        reversals = np.where((dx[:-1] < 0) & (dx[1:] >= 0))[0] + 1
    else:
        reversals = np.where((dx[:-1] > 0) & (dx[1:] <= 0))[0] + 1

    # Any reversal in the segment validates the primary signal
    if len(reversals) > 0:
        logger.debug(f"Secondary signal confirms detection at idx={primary_idx} with reversals at local indices {reversals}.")
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

    for start, end in zip(gap_starts, gap_ends):
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


def _is_valid_finish(x: np.ndarray,
                     idx: int,
                     min_separation: int,
                     prominence: float | None,
                     min_depth_ratio: float = 0.05,
                     secondary_signal: np.ndarray | None = None,
                     snr_threshold: float = 3.0):
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
        logger.debug(f"Candidate finish at idx={idx} rejected: out of bounds.")
        return False

    # Check signal quality: reject if signal is too noisy
    snr = _compute_signal_noise_ratio(x, window=max(3, len(x) // 10))
    if snr < snr_threshold:
        logger.warning(f"Low SNR in primary signal for finish detection: SNR={snr:.2f} < {snr_threshold}")
        return False

    # Must be a true reversal point (strict local maximum condition).
    if not (x[idx - 1] < x[idx] > x[idx + 1]):
        logger.debug(f"Candidate finish at idx={idx} rejected: not a strict local maximum (x[idx-1]={x[idx-1]:.2f}, x[idx]={x[idx]:.2f}, x[idx+1]={x[idx+1]:.2f}).")
        return False

    if prominence is not None:
        left = max(0, idx - min_separation)
        right = min(len(x) - 1, idx + min_separation)
        neighborhood = np.r_[x[left:idx], x[idx + 1:right + 1]]
        if neighborhood.size > 0 and (x[idx] - neighborhood.max()) < prominence and (x[idx] - neighborhood.mean()) < prominence:
            logger.debug(f"Candidate finish at idx={idx} rejected: insufficient prominence (neighborhood max diff={x[idx] - neighborhood.max():.2f}, mean diff={x[idx] - neighborhood.mean():.2f}, required={prominence}).")
            return False

    # Reject shallow lumps that are not a major finish.
    global_amp = np.nanmax(x) - np.nanmin(x)
    high = np.nanmax(x)
    mean_val = np.nanmean(x)

    if global_amp > 1e-8:
        left = max(0, idx - min_separation)
        right = min(len(x) - 1, idx + min_separation)
        neighborhood = np.r_[x[left:idx], x[idx + 1:right + 1]]
        if neighborhood.size > 0:
            local_min = np.nanmin(neighborhood)
            local_depth = x[idx] - local_min
            required_depth = min_depth_ratio * global_amp

            if idx <= min_separation or idx >= len(x) - 1 - min_separation:
                required_depth = min(required_depth, 0.1 * global_amp)

            if local_depth < required_depth:
                logger.debug(f"Candidate finish at idx={idx} rejected: shallow lump (depth={local_depth:.2f} < required={required_depth:.2f}).")
                return False

        # Reject extremes not consistent with a finish location.
        if x[idx] < mean_val or x[idx] < high - 0.33 * global_amp:
            logger.debug(f"Candidate finish at idx={idx} rejected: too low in signal range (val={x[idx]:.2f}, mean={mean_val:.2f}, limit={high - 0.33 * global_amp:.2f}).")
            return False

    # Cross-validate with secondary signal if provided
    if secondary_signal is not None:
        if not _validate_with_secondary_signal(idx, secondary_signal, min_separation, is_minima=False):
            if snr < 15.0:
                logger.warning(f"Secondary signal validation failed for finish at idx={idx} (SNR={snr:.2f})")
                return False
            else:
                logger.debug(f"Secondary signal validation failed for finish at idx={idx}, but primary SNR is high ({snr:.2f}). Proceeding.")

    return True


def _detect_finishes_by_seat_reversal(seat_x: pd.Series,
                                      min_separation: int = 20,
                                      prominence: float | None = None,
                                      seat_y: pd.Series | None = None,
                                      min_depth_ratio: float = 0.05) -> np.ndarray:
    """Detect finish indices as local maxima of Seat_X.

    We model the finish as the point where the seat reaches its most rearward position
    and reverses direction (end of drive -> start of recovery).

    Args:
        seat_x: smoothed Seat_X series (primary signal).
        min_separation: minimum samples between consecutive finishes.
        prominence: optional minimum height vs. neighborhood to filter noise.
        seat_y: optional smoothed Seat_Y series for secondary validation.
        min_depth_ratio: minimum depth as ratio of signal amplitude (default 0.05).

    Returns:
        ndarray of integer indices into the dataframe (same index as seat_x).
    """
    x = seat_x.to_numpy(dtype=float)
    y = seat_y.to_numpy(dtype=float) if seat_y is not None else None

    dx = np.diff(x)
    # Indices i where dx[i-1] > 0 and dx[i] <= 0. This corresponds to a maximum at i.
    candidates = np.where((dx[:-1] > 0) & (dx[1:] <= 0))[0] + 1

    if candidates.size == 0:
        return np.array([], dtype=int)

    filtered: list[int] = []
    cluster_start = 0
    for i in range(1, len(candidates)):
        if candidates[i] - candidates[i - 1] >= min_separation:
            cluster = candidates[cluster_start:i]
            best_idx = int(cluster[np.argmax(x[cluster])])
            if _is_valid_finish(x, best_idx, min_separation, prominence, 
                               min_depth_ratio=min_depth_ratio, secondary_signal=y):
                filtered.append(best_idx)
            cluster_start = i

    cluster = candidates[cluster_start:]
    if cluster.size > 0:
        best_idx = int(cluster[np.argmax(x[cluster])])
        if _is_valid_finish(x, best_idx, min_separation, prominence, 
                           min_depth_ratio=min_depth_ratio, secondary_signal=y):
            filtered.append(best_idx)

    return np.array(filtered, dtype=int)
