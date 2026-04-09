"""Rhythm Consistency plot transform.

Shows SPM vs Drive/Recovery ratio consistency across cycles.
"""

from typing import Any

import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


class RhythmConsistencyComponent(PlotComponent):
    """Rhythm consistency (SPM vs ratio) component."""

    @property
    def name(self) -> str:
        return "Rhythm Consistency"

    @property
    def description(self) -> str:
        return "SPM and drive/recovery ratio consistency across cycles"

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
            results: Results dict with cycle_details

        Returns:
            Dict with plot data and metadata
        """
        cycle_details = []
        if results and 'cycle_details' in results:
            cycle_details = results['cycle_details']

        # Extract SPM and ratio data
        df_data = []
        for cycle in cycle_details:
            if 'spm' in cycle and 'drive_recovery_ratio' in cycle:
                df_data.append({
                    'cycle_idx': cycle.get('cycle_idx', 0),
                    'spm': cycle['spm'],
                    'drive_recovery_ratio': cycle['drive_recovery_ratio'],
                })

        df = pd.DataFrame(df_data).dropna(subset=['spm', 'drive_recovery_ratio']) if df_data else pd.DataFrame()

        return {
            'data': {
                'dataframe': df,
                'has_data': not df.empty,
            },
            'metadata': {
                'title': 'Rhythm Consistency (SPM vs Ratio)',
                'x_label': 'Strokes Per Minute (SPM)',
                'y_label': 'Drive/Recovery Ratio',
            },
            'coach_tip': (
                'Elite rowers maintain a tight cluster. '
                'A vertical spread means inconsistent rhythm at the same speed. '
                'A horizontal spread means the ratio changes too much with rate.'
            ),
        }
