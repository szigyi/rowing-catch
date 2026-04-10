"""Rhythm Consistency transform.

Shows SPM vs Drive/Recovery ratio consistency across cycles, with ideal ratio curve.
This is the authoritative version (migrated from the debug pipeline).
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.algo.helpers import calculate_ideal_drive_ratio
from rowing_catch.plot_transformer.base import PlotComponent
from rowing_catch.plot_transformer.rhythm.drive_recovery_balance_transformer import compute_rhythm_spread


class RhythmConsistencyComponent(PlotComponent):
    """Rhythm consistency (SPM vs ratio) component."""

    @property
    def name(self) -> str:
        return 'Rhythm Consistency'

    @property
    def description(self) -> str:
        return 'SPM and drive/recovery ratio consistency across cycles with biomechanical ideal curve'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute rhythm consistency plot data.

        Args:
            avg_cycle: DataFrame with rowing stroke data (not used directly)
            catch_idx: Index of catch (not used)
            finish_idx: Index of finish (not used)
            ghost_cycle: Not used
            results: Must contain 'cycles' (list of per-stroke DataFrames)

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        cycles: list[pd.DataFrame] = results.get('cycles', []) if results else []
        cycle_data = compute_rhythm_spread(cycles)

        df = pd.DataFrame(cycle_data) if cycle_data else pd.DataFrame()

        if not df.empty:
            spm_vals = df['SPM'].to_numpy(dtype=float)
            ratio_vals = df['Ratio_DR'].to_numpy(dtype=float)
            cycle_nums = df['Cycle'].tolist()
            mean_spm = float(np.nanmean(spm_vals))
            mean_ratio = float(np.nanmean(ratio_vals))
        else:
            spm_vals = np.array([], dtype=float)
            ratio_vals = np.array([], dtype=float)
            cycle_nums = []
            mean_spm = float('nan')
            mean_ratio = float('nan')

        # Ideal ratio curve (15–45 SPM)
        spm_curve = np.linspace(15, 45, 100)
        ideal_ratios = np.asarray(calculate_ideal_drive_ratio(spm_curve), dtype=float)

        return {
            'data': {
                'spm_vals': spm_vals.tolist(),
                'ratio_vals': ratio_vals.tolist(),
                'cycle_nums': cycle_nums,
                'mean_spm': mean_spm,
                'mean_ratio': mean_ratio,
                'ideal_curve_spm': spm_curve.tolist(),
                'ideal_curve_ratio': ideal_ratios.tolist(),
                'has_data': len(cycle_data) > 0,
                'dataframe': df,
            },
            'metadata': {
                'title': 'Stroke-by-Stroke Rhythm Consistency',
                'x_label': 'Strokes Per Minute (SPM)',
                'y_label': 'Drive:Recovery Ratio',
            },
            'coach_tip': (
                'Elite rowers maintain a tight cluster near the ideal curve. '
                'A vertical spread means inconsistent ratio at the same rate. '
                'A horizontal spread means the rate changes too much stroke-to-stroke.'
            ),
        }
