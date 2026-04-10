"""Drive Recovery Balance transform.

Transforms stroke statistics into drive vs recovery stacked bar data.
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.algo.helpers import calculate_ideal_drive_ratio
from rowing_catch.algo.step.step5_metrics import _pick_finish_index
from rowing_catch.plot_transformer.base import PlotComponent


def compute_drive_recovery_balance(
    cycles: list[pd.DataFrame],
    min_length: int,
    catch_idx: int,
    finish_idx: int,
) -> dict[str, Any]:
    """Compute drive and recovery percentages and ideal ratio.

    Args:
        cycles: List of per-stroke cycle DataFrames
        min_length: Length of the averaged cycle (used for drive/recovery split)
        catch_idx: Catch index on the averaged cycle
        finish_idx: Finish index on the averaged cycle

    Returns:
        Dict with drive_pct, rec_pct, mean_spm, ideal_ratio, ideal_drive_pct
    """
    drive_len = finish_idx - catch_idx
    recovery_len = min_length - drive_len
    drive_pct = drive_len / min_length * 100
    rec_pct = recovery_len / min_length * 100

    cycle_spms = [
        60.0 / (c['Time'].to_numpy(dtype=float)[-1] - c['Time'].to_numpy(dtype=float)[0])
        for c in cycles
        if 'Time' in c.columns and len(c) > 1 and c['Time'].to_numpy(dtype=float)[-1] > c['Time'].to_numpy(dtype=float)[0]
    ]
    mean_spm = float(np.nanmean(cycle_spms)) if cycle_spms else float('nan')

    if not np.isnan(mean_spm):
        ideal_ratio = float(calculate_ideal_drive_ratio(mean_spm))
        ideal_drive_pct = (ideal_ratio / (1.0 + ideal_ratio)) * 100
    else:
        ideal_ratio = 0.5
        mean_spm = float('nan')
        ideal_drive_pct = 100 / 3

    return {
        'drive_pct': drive_pct,
        'rec_pct': rec_pct,
        'mean_spm': mean_spm,
        'ideal_ratio': ideal_ratio,
        'ideal_drive_pct': ideal_drive_pct,
    }


class DriveRecoveryBalanceComponent(PlotComponent):
    """Drive vs recovery balance component."""

    @property
    def name(self) -> str:
        return 'Drive vs. Recovery Balance'

    @property
    def description(self) -> str:
        return 'Stacked bar showing drive and recovery percentages vs the biomechanically ideal ratio'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute drive vs recovery balance data.

        Args:
            avg_cycle: Averaged cycle DataFrame
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Not used
            results: Must contain 'cycles' and 'min_length'

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        cycles: list[pd.DataFrame] = results.get('cycles', []) if results else []
        min_length: int = results.get('min_length', len(avg_cycle)) if results else len(avg_cycle)

        balance = compute_drive_recovery_balance(cycles, min_length, catch_idx, finish_idx)

        return {
            'data': balance,
            'metadata': {
                'title': 'Drive vs. Recovery Balance',
                'x_label': 'Percentage of stroke cycle',
                'y_label': '',
            },
            'coach_tip': (
                f'At {balance["mean_spm"]:.0f} SPM the ideal drive ratio is {balance["ideal_ratio"]:.2f}:1 '
                f'({balance["ideal_drive_pct"]:.1f}% drive). '
                'Ratios significantly above ideal indicate rushing the recovery.'
            )
            if not np.isnan(balance['mean_spm'])
            else ('Ideal drive ratio is ~0.50:1 (33% drive). Ratios significantly above ideal indicate rushing the recovery.'),
        }


def compute_rhythm_spread(
    cycles: list[pd.DataFrame],
) -> list[dict[str, Any]]:
    """Compute per-cycle SPM, drive:recovery ratio and durations.

    Args:
        cycles: List of per-stroke cycle DataFrames

    Returns:
        List of dicts with Cycle, SPM, Ratio_DR, Drive (s), Recovery (s)
    """
    cycle_data: list[dict[str, Any]] = []
    for i, c in enumerate(cycles):
        if 'Time' in c.columns and len(c) > 1:
            t = c['Time'].to_numpy(dtype=float)
            duration = t[-1] - t[0]
            if duration > 0:
                spm = 60.0 / duration
                f_idx = _pick_finish_index(c, catch_idx=0)
                drive_dur = t[f_idx] - t[0]
                rec_dur = duration - drive_dur
                ratio = drive_dur / rec_dur if rec_dur > 0 else float('nan')
                cycle_data.append(
                    {
                        'Cycle': i + 1,
                        'SPM': round(spm, 1),
                        'Ratio_DR': round(ratio, 2),
                        'Drive (s)': round(drive_dur, 2),
                        'Recovery (s)': round(rec_dur, 2),
                    }
                )
    return cycle_data
