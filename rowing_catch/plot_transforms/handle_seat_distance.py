"""Handle-Seat Distance plot transform.

Measures compression between handle and seat during the stroke.
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


class HandleSeatDistanceComponent(PlotComponent):
    """Handle-seat distance (compression) component."""

    @property
    def name(self) -> str:
        return "Handle-Seat Distance"

    @property
    def description(self) -> str:
        return "Compression measurement during stroke cycle"

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute handle-seat distance plot data.

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

        # Calculate distance
        dist = np.abs(avg_cycle['Handle_X_Smooth'] - avg_cycle['Seat_X_Smooth'])

        scenario_dist = None
        if scenario_data is not None:
            scenario_dist = np.abs(scenario_data['Handle_X_Smooth'] - scenario_data['Seat_X_Smooth'])

        return {
            'data': {
                'x': avg_cycle.index.values,
                'distance': dist.values,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
                'scenario_distance': scenario_dist.values if scenario_dist is not None else None,
                'scenario_data': scenario_data,
            },
            'metadata': {
                'title': 'Handle-Seat Separation',
                'xlabel': 'Stroke Index',
                'ylabel': 'Distance (mm)',
                'scenario_name': scenario_name,
            },
            'coach_tip': (
                "Maximizing this distance at the catch (compression) without 'over-reaching' "
                'is key to a long effective stroke.'
            ),
        }
