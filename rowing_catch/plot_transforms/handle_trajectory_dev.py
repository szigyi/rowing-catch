"""Handle Trajectory box plot transform.

Shows 2D vertical vs horizontal handle path during stroke.
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


class HandleTrajectoryDevComponent(PlotComponent):
    """Handle trajectory (2D path) component for development analysis."""

    @property
    def name(self) -> str:
        return "Handle Trajectory (Development)"

    @property
    def description(self) -> str:
        return "2D handle path showing vertical vs horizontal progression"

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute handle trajectory plot data.

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

        # Handle position
        h_x = avg_cycle['Handle_X_Smooth'].values
        h_y = avg_cycle['Handle_Y_Smooth'].values

        # Calculate reference box
        h_x_min, h_x_max = float(h_x.min()), float(h_x.max())
        h_y_min, h_y_max = float(h_y.min()), float(h_y.max())

        # Box padding (10% of y range)
        box_padding = (h_y_max - h_y_min) * 0.1
        ideal_y_drive = h_y_max + box_padding
        ideal_y_recovery = h_y_min - box_padding

        # Ideal reference box
        ideal_x = [h_x_min, h_x_max, h_x_max, h_x_min, h_x_min]
        ideal_y = [ideal_y_drive, ideal_y_drive, ideal_y_recovery, ideal_y_recovery, ideal_y_drive]

        # Scenario data if provided
        scenario_x = None
        scenario_y = None
        if scenario_data is not None:
            scenario_x = scenario_data['Handle_X_Smooth'].values
            scenario_y = scenario_data['Handle_Y_Smooth'].values

        return {
            'data': {
                'handle_x': h_x,
                'handle_y': h_y,
                'ideal_x': ideal_x,
                'ideal_y': ideal_y,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
                'catch_x': float(h_x[catch_idx]),
                'catch_y': float(h_y[catch_idx]),
                'finish_x': float(h_x[finish_idx]),
                'finish_y': float(h_y[finish_idx]),
                'scenario_x': scenario_x,
                'scenario_y': scenario_y,
                'scenario_data': scenario_data,
            },
            'metadata': {
                'title': 'Handle Trajectory Path',
                'xlabel': 'Horizontal Position (mm)',
                'ylabel': 'Vertical Position (mm)',
                'scenario_name': scenario_name,
            },
            'coach_tip': (
                "A 'rectangular' box means you are extracting the blade cleanly "
                'and depth is stable throughout the drive.'
            ),
        }
