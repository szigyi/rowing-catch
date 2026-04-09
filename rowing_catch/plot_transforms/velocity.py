"""Velocity Coordination plot transform.

Transforms analysis results into data ready for rendering seat vs. handle velocity.
"""

from typing import Any

import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


class VelocityCoordinationComponent(PlotComponent):
    """Seat vs. Handle velocity alignment plot component."""

    @property
    def name(self) -> str:
        return 'Velocity Coordination'

    @property
    def description(self) -> str:
        return 'Handle and seat velocity alignment during drive phase'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute velocity coordination plot data.

        Extracts handle and seat velocity traces from avg_cycle,
        preparing them for rendering.
        """
        return {
            'data': {
                'handle_vel': avg_cycle['Handle_X_Vel'].values,
                'seat_vel': avg_cycle['Seat_X_Vel'].values,
                'x': avg_cycle.index.values,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
            },
            'metadata': {
                'title': 'Velocity Coordination',
                'xlabel': 'Stroke Index',
                'ylabel': 'Velocity',
            },
            'coach_tip': (
                'The goal is for your legs and handle to accelerate together. '
                'Gaps between these peaks mean you are losing power (shooting the slide).'
            ),
        }


__all__ = ['VelocityCoordinationComponent']
