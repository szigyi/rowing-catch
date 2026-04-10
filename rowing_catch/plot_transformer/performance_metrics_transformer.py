"""Performance Metrics plot transform.

Jerk analysis and handle height stability metrics.
"""

from typing import Any

import pandas as pd

from rowing_catch.plot_transformer.base import PlotComponent


class PerformanceMetricsComponent(PlotComponent):
    """Performance metrics component."""

    @property
    def name(self) -> str:
        return 'Performance Metrics'

    @property
    def description(self) -> str:
        return 'Jerk analysis and handle height stability'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute performance metrics plot data.

        Args:
            avg_cycle: DataFrame with rowing stroke data
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Unused for performance metrics
            results: Optional results dict with scenario_name

        Returns:
            Dict with plot data and metadata
        """
        scenario_name = results.get('scenario_name', 'None') if results else 'None'

        # Extract jerk for full cycle
        jerk_data = avg_cycle['Handle_X_Jerk'].values

        # Extract handle height during drive phase
        drive_y = avg_cycle.loc[catch_idx:finish_idx, 'Handle_Y_Smooth']

        # Compute boxplot statistics for drive phase
        boxplot_data = {
            'min': drive_y.min(),
            'q1': drive_y.quantile(0.25),
            'median': drive_y.median(),
            'q3': drive_y.quantile(0.75),
            'max': drive_y.max(),
        }

        return {
            'data': {
                'stroke_index': avg_cycle.index.values,
                'jerk': jerk_data,
                'drive_y': drive_y.values,
                'boxplot_stats': boxplot_data,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
            },
            'metadata': {
                'title': 'Smoothness & Stability',
                'x_label': 'Stroke Index',
                'y_label': 'Jerk (mm/s³)',
                'scenario_name': scenario_name,
            },
            'coach_tip': (
                "Minimizing Jerk means a more 'fluid' connection. Tight Handle Height boxplots indicate stable blade depth."
            ),
        }
