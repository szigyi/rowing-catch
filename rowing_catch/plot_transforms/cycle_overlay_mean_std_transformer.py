"""Cycle Overlay Mean Std transform.

Transforms individual stroke cycles into data ready for overlaid mean ± SD rendering.
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


def compute_cycle_overlay(cycles: list[pd.DataFrame]) -> dict[str, Any]:
    """Compute cycle overlay statistics from a list of cycle DataFrames.

    Args:
        cycles: List of per-stroke cycle DataFrames (each must have 'Seat_X_Smooth')

    Returns:
        Dict with 'x_idx', 'cycle_arrays', 'mean_vals', 'std_vals', 'min_length'
    """
    if not cycles:
        return {
            'x_idx': [],
            'cycle_arrays': [],
            'mean_vals': [],
            'std_vals': [],
            'min_length': 0,
        }
    min_length = min(len(c) for c in cycles)
    cycle_arrays = [c['Seat_X_Smooth'].to_numpy(dtype=float)[:min_length] for c in cycles]
    x_idx = np.arange(min_length).tolist()
    stack = np.vstack(cycle_arrays)
    mean_vals = stack.mean(axis=0).tolist()
    std_vals = stack.std(axis=0).tolist()
    return {
        'x_idx': x_idx,
        'cycle_arrays': [arr.tolist() for arr in cycle_arrays],
        'mean_vals': mean_vals,
        'std_vals': std_vals,
        'min_length': min_length,
    }


class CycleOverlayMeanStdComponent(PlotComponent):
    """Cycle overlay with mean and ±1 SD band component."""

    @property
    def name(self) -> str:
        return 'Cycle Overlay (Mean ± SD)'

    @property
    def description(self) -> str:
        return 'All stroke cycles overlaid with mean and ±1 SD band for consistency assessment'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute cycle overlay data.

        Args:
            avg_cycle: Averaged cycle DataFrame (not used directly)
            catch_idx: Index of catch (not used)
            finish_idx: Index of finish (not used)
            ghost_cycle: Not used
            results: Must contain 'cycles' (list of per-stroke DataFrames)

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        cycles: list[pd.DataFrame] = results.get('cycles', []) if results else []
        overlay = compute_cycle_overlay(cycles)

        return {
            'data': overlay,
            'metadata': {
                'title': 'Averaged Seat_X — all cycles overlaid',
                'x_label': 'Cycle Index',
                'y_label': 'Seat_X_Smooth (mm)',
            },
            'coach_tip': (
                'A narrow SD band means consistent stroke shape. '
                'Wide bands indicate variability in the catch position or stroke length.'
            ),
        }
