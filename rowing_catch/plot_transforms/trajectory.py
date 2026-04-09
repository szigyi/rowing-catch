"""Handle Trajectory plot transform.

Transforms analysis results into data ready for rendering the handle's 2D path.
"""

from typing import Any

import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


class HandleTrajectoryComponent(PlotComponent):
    """Handle trajectory 'box' plot component."""

    @property
    def name(self) -> str:
        return 'Handle Trajectory'

    @property
    def description(self) -> str:
        return '2D handle path during stroke cycle'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute handle trajectory plot data including ideal path.

        Calculates the ideal handle path (rectangular 'box') based on
        actual trajectory bounds.
        """
        # Calculate handle trajectory bounds
        h_x_min = avg_cycle['Handle_X_Smooth'].min()
        h_x_max = avg_cycle['Handle_X_Smooth'].max()
        h_y_min = avg_cycle['Handle_Y_Smooth'].min()
        h_y_max = avg_cycle['Handle_Y_Smooth'].max()

        # Ideal path expanded by 10% beyond bounds
        ideal_y_drive = h_y_max + (h_y_max - h_y_min) * 0.1
        ideal_y_recovery = h_y_min - (h_y_max - h_y_min) * 0.1

        ideal_x = [h_x_min, h_x_max, h_x_max, h_x_min, h_x_min]
        ideal_y = [ideal_y_drive, ideal_y_drive, ideal_y_recovery, ideal_y_recovery, ideal_y_drive]

        return {
            'data': {
                'handle_x': avg_cycle['Handle_X_Smooth'].values,
                'handle_y': avg_cycle['Handle_Y_Smooth'].values,
                'ideal_x': ideal_x,
                'ideal_y': ideal_y,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
                'catch_x': avg_cycle.loc[catch_idx, 'Handle_X_Smooth'],
                'catch_y': avg_cycle.loc[catch_idx, 'Handle_Y_Smooth'],
                'finish_x': avg_cycle.loc[finish_idx, 'Handle_X_Smooth'],
                'finish_y': avg_cycle.loc[finish_idx, 'Handle_Y_Smooth'],
                'ideal_catch_x': [h_x_min, h_x_max],
                'ideal_catch_y': [ideal_y_drive, ideal_y_drive],
            },
            'metadata': {
                'title': "Handle Trajectory 'Box' Plot",
                'xlabel': 'Horizontal Position',
                'ylabel': 'Vertical Position',
            },
            'coach_tip': ('A flatter top line on the drive means a more consistent depth in the water.'),
        }


__all__ = ['HandleTrajectoryComponent']
