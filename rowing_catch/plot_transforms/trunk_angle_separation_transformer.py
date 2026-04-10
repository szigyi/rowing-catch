"""Trunk Angle Separation plot transform.

Shows how the body rocks over relative to seat position timing.
"""

from typing import Any, cast

import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


class TrunkAngleSeparationComponent(PlotComponent):
    """Trunk angle vs seat position component."""

    @property
    def name(self) -> str:
        return 'Trunk Angle Separation'

    @property
    def description(self) -> str:
        return 'Body rocking timing relative to seat position'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute trunk angle separation plot data.

        Args:
            avg_cycle: DataFrame with rowing stroke data
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Optional comparison DataFrame (used as scenario_data)
            results: Optional results dict with scenario_name

        Returns:
            Dict with plot data and metadata
        """
        scenario_data = ghost_cycle
        scenario_name = results.get('scenario_name', 'None') if results else 'None'

        return {
            'data': {
                'seat_position': avg_cycle['Seat_X_Smooth'].values,
                'trunk_angle_plot': avg_cycle['Trunk_Angle'].values,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
                'catch_seat': cast(float, avg_cycle.at[catch_idx, 'Seat_X_Smooth']),
                'catch_angle': cast(float, avg_cycle.at[catch_idx, 'Trunk_Angle']),
                'finish_seat': cast(float, avg_cycle.at[finish_idx, 'Seat_X_Smooth']),
                'finish_angle': cast(float, avg_cycle.at[finish_idx, 'Trunk_Angle']),
                'scenario_seat': scenario_data['Seat_X_Smooth'].values if scenario_data is not None else None,
                'scenario_angle': scenario_data['Trunk_Angle'].values if scenario_data is not None else None,
                'scenario_data': scenario_data,
            },
            'metadata': {
                'title': 'Trunk Angle vs Stroke Progress',
                'x_label': 'Seat Position (mm)',
                'y_label': 'Trunk Angle (deg)',
                'scenario_name': scenario_name,
            },
            'coach_tip': (
                "Watch for 'Body Over' before the knees come up in recovery. "
                'The angle should drop towards the catch while the seat is still moving backwards.'
            ),
        }
