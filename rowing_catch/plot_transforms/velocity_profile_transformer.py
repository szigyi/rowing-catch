"""Velocity Profile transform.

Transforms averaged cycle velocity data into plot-ready format.
"""

from typing import Any

import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


class VelocityProfileComponent(PlotComponent):
    """Velocity profile (Handle, Seat, Shoulder, Rower) component."""

    @property
    def name(self) -> str:
        return 'Velocity Profile'

    @property
    def description(self) -> str:
        return 'Rate of change (velocity) of all tracked segments across the averaged stroke'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute velocity profile data.

        Args:
            avg_cycle: Averaged cycle DataFrame with velocity columns
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Not used
            results: Not used

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        index = avg_cycle.index.tolist()
        handle_vel = avg_cycle['Handle_X_Vel'].to_numpy(dtype=float).tolist()
        seat_vel = avg_cycle['Seat_X_Vel'].to_numpy(dtype=float).tolist()

        has_shoulder = 'Shoulder_X_Vel' in avg_cycle.columns
        shoulder_vel = avg_cycle['Shoulder_X_Vel'].to_numpy(dtype=float).tolist() if has_shoulder else []
        rower_vel = avg_cycle['Rower_Vel'].to_numpy(dtype=float).tolist() if 'Rower_Vel' in avg_cycle.columns else []

        return {
            'data': {
                'index': index,
                'handle_vel': handle_vel,
                'seat_vel': seat_vel,
                'shoulder_vel': shoulder_vel,
                'rower_vel': rower_vel,
                'has_shoulder': has_shoulder,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
            },
            'metadata': {
                'title': 'Velocity Profile — Seat, Handle, Shoulder, Rower',
                'x_label': 'Cycle index (time)',
                'y_label': 'Velocity (mm/s)',
            },
            'coach_tip': (
                'The handle velocity should peak during the mid-drive. '
                'Seat velocity should reach its maximum at the catch and decelerate smoothly. '
                'Large spikes in shoulder velocity relative to seat indicate trunk-arm disconnect.'
            ),
        }
