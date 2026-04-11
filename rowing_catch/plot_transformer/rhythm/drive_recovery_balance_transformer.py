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
        min_length: Length of the averaged cycle. Equals next-catch index in local cycle space,
            because each cycle is sliced from ``catch_i - pre_catch_window`` to ``catch_next``.
        catch_idx: Catch index on the averaged cycle
        finish_idx: Finish index on the averaged cycle

    Returns:
        Dict with drive_pct, rec_pct, mean_spm, ideal_ratio, ideal_drive_pct
    """
    # The averaged cycle includes a pre-catch window before catch_idx.
    # Drive and recovery percentages must be relative to the catch-to-end span,
    # not the full min_length (which includes the pre-catch window).
    stroke_len = min_length - catch_idx  # samples from catch to next catch
    drive_len = finish_idx - catch_idx
    recovery_len = min_length - finish_idx
    drive_pct = drive_len / stroke_len * 100 if stroke_len > 0 else 0.0
    rec_pct = recovery_len / stroke_len * 100 if stroke_len > 0 else 0.0

    # Compute SPM from catch-to-next-catch duration, excluding the pre-catch window.
    cycle_spms = []
    for c in cycles:
        if 'Time' not in c.columns or len(c) <= 1:
            continue
        t_arr = c['Time'].to_numpy(dtype=float)
        if 'Seat_X_Smooth' in c.columns:
            seat_arr = c['Seat_X_Smooth'].to_numpy(dtype=float)
            search_end = max(1, int(len(seat_arr) * 0.35))
            catch_in_c = int(np.argmin(seat_arr[:search_end]))
        else:
            catch_in_c = 0
        stroke_dur = t_arr[-1] - t_arr[catch_in_c]
        if stroke_dur > 0:
            cycle_spms.append(60.0 / stroke_dur)
    mean_spm = float(np.nanmean(cycle_spms)) if cycle_spms else float('nan')

    if not np.isnan(mean_spm):
        ideal_ratio = float(calculate_ideal_drive_ratio(mean_spm))
        ideal_drive_pct = (ideal_ratio / (1.0 + ideal_ratio)) * 100
    else:
        ideal_drive_pct = 100 / 3
        mean_spm = float('nan')

    return {
        'drive_pct': drive_pct,
        'rec_pct': rec_pct,
        'mean_spm': mean_spm,
        'ideal_drive_pct': ideal_drive_pct,
    }


class DriveRecoveryBalanceComponent(PlotComponent):
    """Drive vs recovery balance component."""

    @property
    def name(self) -> str:
        return 'Drive vs. Recovery Balance'

    @property
    def description(self) -> str:
        return 'Stacked bar showing drive and recovery percentages vs the biomechanically ideal drive%'

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
                f'At {balance["mean_spm"]:.0f} SPM the ideal drive phase is {balance["ideal_drive_pct"]:.1f}% of the stroke. '
                'A drive phase significantly above ideal indicates rushing the recovery.'
            )
            if not np.isnan(balance['mean_spm'])
            else (
                'The ideal drive phase is ~33% of the stroke. '
                'A drive phase significantly above ideal indicates rushing the recovery.'
            ),
        }


def _find_catch_idx_in_cycle(c: pd.DataFrame, search_fraction: float = 0.35) -> int:
    """Find the catch index within a per-cycle DataFrame.

    Each cycle is sliced from ``catch_i - pre_catch_window`` to ``catch_next``
    by step4.  The catch therefore always falls near the *start* of the cycle
    (within the first ~pre_catch_window + small_buffer samples).

    We must NOT use a global argmin because the cycle ends at the *next* catch,
    which is also a Seat_X minimum and is often lower than the current catch,
    so argmin over the full cycle would return the last index instead.

    Instead we search only the first ``search_fraction`` of the cycle (default
    35%), which is always enough to capture the real catch and avoids picking
    up the next catch at the end.

    Args:
        c: Per-stroke cycle DataFrame with 'Seat_X_Smooth' column.
        search_fraction: Fraction of the cycle length to search (default 0.35).

    Returns:
        Integer index of the catch within the cycle DataFrame.
    """
    if 'Seat_X_Smooth' not in c.columns:
        return 0
    seat = c['Seat_X_Smooth'].to_numpy(dtype=float)
    # Limit search to the first portion of the cycle where the catch always lives.
    search_end = max(1, int(len(seat) * search_fraction))
    return int(np.argmin(seat[:search_end]))


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
            # Locate the catch within this cycle (it is NOT at index 0 because
            # each cycle includes a pre_catch_window of samples before the catch).
            catch_in_cycle = _find_catch_idx_in_cycle(c)
            t_catch = t[catch_in_cycle]
            # Next catch is at t[-1] (the cycle ends at the following catch).
            t_next_catch = t[-1]
            stroke_duration = t_next_catch - t_catch
            if stroke_duration <= 0:
                continue
            spm = 60.0 / stroke_duration
            f_idx = _pick_finish_index(c, catch_idx=catch_in_cycle)
            t_finish = t[f_idx]
            drive_dur = t_finish - t_catch
            rec_dur = t_next_catch - t_finish
            stroke_dur_total = drive_dur + rec_dur
            drive_pct = drive_dur / stroke_dur_total * 100 if stroke_dur_total > 0 else float('nan')
            cycle_data.append(
                {
                    'Cycle': i + 1,
                    'SPM': round(spm, 1),
                    'Drive_Pct': round(drive_pct, 1),
                    'Drive (s)': round(drive_dur, 2),
                    'Recovery (s)': round(rec_dur, 2),
                }
            )
    return cycle_data
