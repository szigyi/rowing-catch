"""Kinetic Chain Coordination plot transform.

Velocity and acceleration coordination between seat and handle.
"""

from typing import Any

import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


class KineticChainComponent(PlotComponent):
    """Kinetic chain coordination component."""

    @property
    def name(self) -> str:
        return 'Kinetic Chain Coordination'

    @property
    def description(self) -> str:
        return 'Velocity and acceleration coordination between seat and handle'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute kinetic chain plot data.

        Args:
            avg_cycle: DataFrame with rowing stroke data
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Unused for kinetic chain
            results: Optional results dict with scenario_name

        Returns:
            Dict with plot data and metadata
        """
        scenario_name = results.get('scenario_name', 'None') if results else 'None'

        return {
            'data': {
                'stroke_index': avg_cycle.index.values,
                'handle_x_vel': avg_cycle['Handle_X_Vel'].values,
                'seat_x_vel': avg_cycle['Seat_X_Vel'].values,
                'handle_x_accel': avg_cycle['Handle_X_Accel'].values,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
            },
            'metadata': {
                'title': 'Kinetic Chain Coordination',
                'x_label': 'Stroke Index',
                'y_label': 'Velocity / Accel',
                'scenario_name': scenario_name,
            },
            'coach_tip': (
                "Coordination between seat velocity and handle acceleration. A lag here indicates 'shooting the slide'."
            ),
        }
