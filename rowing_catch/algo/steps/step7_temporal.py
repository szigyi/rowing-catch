import numpy as np
import pandas as pd


def step7_temporal_metrics(
    avg_cycle: pd.DataFrame,
    catch_idx: int,
    finish_idx: int,
) -> dict:
    """Calculate temporal metrics and standard units for the averaged cycle."""
    metrics = {
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
        # Time column is not strictly increasing; skip temporal-derived metrics.
        return metrics

    dt = np.diff(t)
    if np.any(dt <= 0):
        return metrics

    sample_rate_hz = float(1.0 / np.median(dt))
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

    metrics.update({
        'sample_rate_hz': sample_rate_hz,
        'cycle_duration_s': cycle_duration_s,
        'drive_duration_s': drive_duration_s,
        'recovery_duration_s': recovery_duration_s,
        'stroke_rate_spm': stroke_rate_spm,
    })

    return metrics
