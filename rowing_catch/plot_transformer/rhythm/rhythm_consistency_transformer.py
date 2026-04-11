"""Rhythm Consistency transform.

Shows SPM vs drive phase percentage consistency across cycles, with ideal curve.
This is the authoritative version (migrated from the debug pipeline).
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.algo.helpers import calculate_ideal_drive_ratio
from rowing_catch.plot_transformer.base import PlotComponent
from rowing_catch.plot_transformer.rhythm.drive_recovery_balance_transformer import compute_rhythm_spread


class RhythmConsistencyComponent(PlotComponent):
    """Rhythm consistency (SPM vs drive%) component."""

    @property
    def name(self) -> str:
        return 'Rhythm Consistency'

    @property
    def description(self) -> str:
        return 'SPM and drive phase % consistency across cycles with biomechanical ideal curve'

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
            drive_pct_vals = df['Drive_Pct'].to_numpy(dtype=float)
            cycle_nums = df['Cycle'].tolist()
            mean_spm = float(np.nanmean(spm_vals))
            mean_drive_pct = float(np.nanmean(drive_pct_vals))
        else:
            spm_vals = np.array([], dtype=float)
            drive_pct_vals = np.array([], dtype=float)
            cycle_nums = []
            mean_spm = float('nan')
            mean_drive_pct = float('nan')

        # Ideal drive% curve (15–45 SPM): convert ratio → percentage
        spm_curve = np.linspace(15, 45, 100)
        ideal_ratios = np.asarray(calculate_ideal_drive_ratio(spm_curve), dtype=float)
        ideal_drive_pct_curve = ideal_ratios / (1.0 + ideal_ratios) * 100

        return {
            'data': {
                'spm_vals': spm_vals.tolist(),
                'drive_pct_vals': drive_pct_vals.tolist(),
                'cycle_nums': cycle_nums,
                'mean_spm': mean_spm,
                'mean_drive_pct': mean_drive_pct,
                'ideal_curve_spm': spm_curve.tolist(),
                'ideal_curve_drive_pct': ideal_drive_pct_curve.tolist(),
                'has_data': len(cycle_data) > 0,
                'dataframe': df,
            },
            'metadata': {
                'title': 'Stroke-by-Stroke Rhythm Consistency',
                'x_label': 'Strokes Per Minute (SPM)',
                'y_label': 'Drive Phase (% of stroke)',
            },
            'coach_tip': (
                'Elite rowers maintain a tight cluster near the ideal curve. '
                'A vertical spread means inconsistent drive % at the same stroke rate. '
                'A horizontal spread means the stroke rate changes too much stroke-to-stroke.'
            ),
        }
