import logging
from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.algo.steps.step5_metrics import _pick_finish_index

logger = logging.getLogger(__name__)


def step6_statistics(
    cycles: list[pd.DataFrame],
    min_length: int,
    catch_idx: int,
    finish_idx: int,
    avg_cycle: pd.DataFrame,
) -> dict:
    """Compute stroke-level statistics from the individual cycles and the average.

    This step consolidates all scalar performance metrics, including both sample-based
    and time-based (temporal) metrics.

    Args:
        cycles: List of per-stroke DataFrames (output of
            :func:`step4_segment_and_average`).
        min_length: Shortest cycle length, used as the total stroke length for
            ratio calculations.
        catch_idx: Catch position within the averaged stroke.
        finish_idx: Finish position within the averaged stroke.
        avg_cycle: Averaged cycle DataFrame (output of :func:`step5_compute_metrics`).

    Returns:
        A dict with scalar performance metrics:

        * ``'cv_length'`` – coefficient of variation of stroke lengths (%).
        * ``'drive_len'`` – samples from catch to finish.
        * ``'recovery_len'`` – samples from finish to next catch.
        * ``'mean_duration'`` – average cycle length in samples.
        * ``'drive_volume_mm_sec'`` – integrated drive phase displacement (mm*sec).
        * ``'recovery_volume_mm_sec'`` – integrated recovery phase displacement (mm*sec).
        * ``'sample_rate_hz'`` – data collection frequency.
        * ``'cycle_duration_s'`` – duration of the average cycle in seconds.
        * ``'drive_duration_s'`` – duration of the drive phase in seconds.
        * ``'recovery_duration_s'`` – duration of the recovery phase in seconds.
        * ``'stroke_rate_spm'`` – strokes per minute.
    """
    # 1. Sample-based statistics from individual cycles
    stroke_lengths = [c['Seat_X_Smooth'].max() - c['Seat_X_Smooth'].min() for c in cycles]
    stroke_durations = [len(c) for c in cycles]
    mean_len = np.mean(stroke_lengths)
    if mean_len > 0:
        cv_length = (np.std(stroke_lengths) / mean_len) * 100
    else:
        cv_length = 0.0

    # 2. Performance volumes from the averaged cycle
    seat_x = avg_cycle['Seat_X_Smooth'].to_numpy(dtype=float)
    times = avg_cycle['Time'].to_numpy(dtype=float) if 'Time' in avg_cycle.columns else None

    drive_volume_mm_sec = _compute_phase_volume(seat_x, times, catch_idx, finish_idx)
    recovery_volume_mm_sec = _compute_phase_volume(seat_x, times, finish_idx, min_length)

    # 3. Temporal metrics from the averaged cycle (merged from former Step 7)
    temporal = _compute_temporal_metrics(avg_cycle, catch_idx, finish_idx)

    # 4. Per-cycle details for consistency spread
    # Use per-cycle finish indices for accurate drive/recovery ratios
    cycle_details = []
    per_cycle_ratios = []
    for i, c in enumerate(cycles):
        detail: dict[str, Any] = {'cycle_idx': i + 1}
        if 'Time' in c.columns and len(c) > 1:
            t_c = c['Time'].to_numpy(dtype=float)
            dur = t_c[-1] - t_c[0]
            if dur > 0:
                detail['spm'] = 60.0 / dur
                # Map finish to this cycle using per-cycle heuristic
                f_idx_c = _pick_finish_index(c, catch_idx=0)
                drive_dur = t_c[f_idx_c] - t_c[0]
                rec_dur = dur - drive_dur
                ratio = drive_dur / rec_dur if rec_dur > 0 else None
                detail['drive_recovery_ratio'] = ratio
                if ratio is not None:
                    per_cycle_ratios.append(ratio)

        cycle_details.append(detail)

    # Compute average ratio from per-cycle values (not from averaged cycle)
    avg_drive_recovery_ratio = np.nanmean(per_cycle_ratios) if per_cycle_ratios else np.nan

    # Convert to sample-based metrics for backward compatibility
    # These are computed from the average ratio, not the averaged cycle's finish
    if not np.isnan(avg_drive_recovery_ratio):
        # Inverse calculation: if drive/recovery ≈ R, then drive_fraction ≈ R / (1 + R)
        drive_fraction = avg_drive_recovery_ratio / (1.0 + avg_drive_recovery_ratio)
        drive_len = int(round(drive_fraction * min_length))
        recovery_len = min_length - drive_len
    else:
        drive_len = finish_idx - catch_idx
        recovery_len = min_length - drive_len

    return {
        'cv_length': cv_length,
        'drive_len': drive_len,
        'recovery_len': recovery_len,
        'mean_duration': np.mean(stroke_durations),
        'drive_volume_mm_sec': drive_volume_mm_sec,
        'recovery_volume_mm_sec': recovery_volume_mm_sec,
        'avg_drive_recovery_ratio': avg_drive_recovery_ratio,
        **temporal,
        'cycle_details': cycle_details,
    }


def _compute_phase_volume(positions: np.ndarray, times: np.ndarray | None, phase_start_idx: int, phase_end_idx: int) -> float:
    """Compute integrated distance * time for a phase (drive or recovery)."""
    if phase_end_idx <= phase_start_idx or phase_end_idx > len(positions):
        return 0.0

    pos_segment = np.asarray(positions[phase_start_idx:phase_end_idx], dtype=float)
    if len(pos_segment) < 2 or np.all(np.isnan(pos_segment)):
        return 0.0

    if times is not None:
        times = np.asarray(times, dtype=float)
        time_segment = times[phase_start_idx:phase_end_idx]
        dt = np.diff(time_segment)
        if np.any(dt <= 0) or np.any(np.isnan(dt)):
            dt = np.ones(len(time_segment) - 1)
    else:
        dt = np.ones(len(pos_segment) - 1)

    disp = np.abs(np.diff(pos_segment))
    volume = float(np.sum(disp * dt))

    return volume


def _compute_temporal_metrics(
    avg_cycle: pd.DataFrame,
    catch_idx: int,
    finish_idx: int,
) -> dict:
    """Calculate temporal metrics and standard units for the averaged cycle."""
    metrics: dict[str, Any] = {
        'sample_rate_hz': None,
        'cycle_duration_s': None,
        'drive_duration_s': None,
        'recovery_duration_s': None,
        'stroke_rate_spm': None,
    }

    if 'Time' not in avg_cycle.columns or len(avg_cycle) < 2:
        return metrics

    t = avg_cycle['Time'].to_numpy(dtype=float)
    if np.any(np.isnan(t)) or not np.all(np.diff(t) > 0):
        return metrics

    dt = np.diff(t)
    sample_rate_hz = float(1.0 / np.median(dt)) if np.median(dt) > 0 else None
    cycle_duration_s = float(t[-1] - t[0])

    if 0 <= int(catch_idx) < len(t) and 0 <= int(finish_idx) < len(t):
        drive_duration_s = float(max(0.0, t[int(finish_idx)] - t[int(catch_idx)]))
    else:
        drive_duration_s = None

    if drive_duration_s is not None:
        recovery_duration_s = float(max(0.0, cycle_duration_s - drive_duration_s))
    else:
        recovery_duration_s = None

    stroke_rate_spm = float(60.0 / cycle_duration_s) if cycle_duration_s > 0 else None

    metrics.update(
        {
            'sample_rate_hz': sample_rate_hz,
            'cycle_duration_s': cycle_duration_s,
            'drive_duration_s': drive_duration_s,
            'recovery_duration_s': recovery_duration_s,
            'stroke_rate_spm': stroke_rate_spm,
        }
    )

    return metrics
