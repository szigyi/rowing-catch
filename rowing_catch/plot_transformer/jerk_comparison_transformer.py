"""Jerk Comparison transform.

Transforms averaged cycle jerk data into plot-ready format for subplots.
"""

from typing import Any

import pandas as pd

from rowing_catch.plot_transformer.base import PlotComponent


class JerkComparisonComponent(PlotComponent):
    """Jerk comparison subplots component."""

    @property
    def name(self) -> str:
        return 'Jerk Comparison (Smoothness)'

    @property
    def description(self) -> str:
        return 'Per-segment jerk compared to system jerk — lower jerk means smoother movement'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute jerk comparison data.

        Args:
            avg_cycle: Averaged cycle DataFrame with jerk columns
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Not used
            results: Not used

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        index = avg_cycle.index.tolist()

        components: list[dict[str, Any]] = [
            {'label': 'Handle', 'col': 'Handle_X_Jerk', 'color': '#ec4899'},
            {'label': 'Seat', 'col': 'Seat_X_Jerk', 'color': '#FFA15A'},
        ]
        if 'Shoulder_X_Jerk' in avg_cycle.columns:
            components.append({'label': 'Shoulder', 'col': 'Shoulder_X_Jerk', 'color': '#00CC96'})

        panels: list[dict[str, Any]] = []
        for comp in components:
            col = comp['col']
            if col not in avg_cycle.columns:
                continue
            panels.append(
                {
                    'label': comp['label'],
                    'color': comp['color'],
                    'jerk': avg_cycle[col].to_numpy(dtype=float).tolist(),
                }
            )

        rower_jerk = avg_cycle['Rower_Jerk'].to_numpy(dtype=float).tolist() if 'Rower_Jerk' in avg_cycle.columns else []

        return {
            'data': {
                'index': index,
                'panels': panels,
                'rower_jerk': rower_jerk,
                'has_rower_jerk': bool(rower_jerk),
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
            },
            'metadata': {
                'title': 'Jerk in the System (Smoothness)',
                'x_label': 'Cycle index (time)',
                'y_label': 'Jerk (mm/s³)',
            },
            'coach_tip': (
                'Jerk is the rate of change of acceleration — lower is smoother. '
                'Spikes near the catch indicate an abrupt start; spikes at the finish indicate a slam. '
                'Aim for a smooth bell-shaped jerk curve.'
            ),
        }
