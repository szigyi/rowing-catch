"""Trunk Angle plot transform.

Transforms analysis results into data ready for rendering trunk angle with
anatomical stick figures at key stages.
"""

from typing import Any, cast

import numpy as np
import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


class TrunkAngleComponent(PlotComponent):
    """Trunk angle with anatomical stick figures at stroke stages."""

    @property
    def name(self) -> str:
        return 'Trunk Angle & Range'

    @property
    def description(self) -> str:
        return 'Trunk angle progression with anatomical stick figures'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute trunk angle plot data including stage points and ideal zones.

        Calculates stage progression, ideal zones, and prepares data for
        stick figure rendering.
        """
        x = avg_cycle.index.to_numpy()

        # Calculate stage points
        drive_len = max(1, int(finish_idx) - int(catch_idx))
        rec_end = int(x.max())
        rec_len = max(1, rec_end - int(finish_idx))

        stage_points = [
            ('Catch', int(catch_idx)),
            ('3/4 Slide', int(catch_idx + 0.25 * drive_len)),
            ('1/2 Slide', int(catch_idx + 0.50 * drive_len)),
            ('1/4 Slide', int(catch_idx + 0.75 * drive_len)),
            ('Finish', int(finish_idx)),
            ('1/4 Slide', int(finish_idx + 0.25 * rec_len)),
            ('1/2 Slide', int(finish_idx + 0.50 * rec_len)),
            ('3/4 Slide', int(finish_idx + 0.75 * rec_len)),
            ('Next Catch', rec_end),
        ]

        x_min = int(x.min())
        x_max = int(x.max())
        stage_points = [(label, int(np.clip(ix, x_min, x_max))) for label, ix in stage_points]

        # Ideal zones
        catch_zone = (-33, -27)
        finish_zone = (12, 18)

        # Extract angles at stage points for stick figures
        stage_angles = []
        for label, ix in stage_points:
            try:
                angle = float(cast(float, avg_cycle.at[ix, 'Trunk_Angle']))
            except Exception:
                nearest = int(np.argmin(np.abs(x - ix)))
                angle = float(avg_cycle['Trunk_Angle'].iloc[nearest])
            stage_angles.append((label, ix, angle))

        # Ghost cycle data if provided
        ghost_data = None
        if ghost_cycle is not None:
            ghost_data = {
                'trunk_angle': ghost_cycle['Trunk_Angle'].values,
                'x': ghost_cycle.index.values,
            }

        catch_lean = float(cast(float, avg_cycle.at[catch_idx, 'Trunk_Angle']))
        finish_lean = float(cast(float, avg_cycle.at[finish_idx, 'Trunk_Angle']))

        return {
            'data': {
                'trunk_angle': avg_cycle['Trunk_Angle'].values,
                'x': avg_cycle.index.values,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
                'x_max': x_max,
                'x_min': x_min,
                'stage_points': stage_points,
                'stage_angles': stage_angles,
                'catch_zone': catch_zone,
                'finish_zone': finish_zone,
                'catch_lean': catch_lean,
                'finish_lean': finish_lean,
            },
            'ghost_data': ghost_data,
            'metadata': {
                'title': 'Trunk Angle & Range Analysis',
                'x_label': 'Stroke Timeline (Data Points)',
                'y_label': 'Degrees from Vertical',
            },
            'coach_tip': (
                f'You are achieving {abs(finish_lean - catch_lean):.1f}° of range. '
                f'Catch lean: {catch_lean:.1f}°, Finish lean: {finish_lean:.1f}°. '
                'Aim for the shaded zones to optimize power.'
            ),
        }


__all__ = ['TrunkAngleComponent']
