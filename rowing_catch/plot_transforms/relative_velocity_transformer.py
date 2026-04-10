"""Relative Velocity transform.

Transforms averaged cycle into relative velocity data (vs seat) for rendering.
"""

from typing import Any

import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


class RelativeVelocityComponent(PlotComponent):
    """Relative velocity (vs seat) visualization component."""

    @property
    def name(self) -> str:
        return 'Relative Velocity (vs. Seat)'

    @property
    def description(self) -> str:
        return 'Handle and Shoulder velocity relative to the seat, showing body segment independence'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute relative velocity data.

        Args:
            avg_cycle: Averaged cycle DataFrame with Handle_rel_Seat_Vel
                       and optionally Shoulder_rel_Seat_Vel
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Not used
            results: Not used

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        index = avg_cycle.index.tolist()
        handle_rel = avg_cycle['Handle_rel_Seat_Vel'].to_numpy(dtype=float).tolist()

        has_shoulder = 'Shoulder_rel_Seat_Vel' in avg_cycle.columns
        shoulder_rel = avg_cycle['Shoulder_rel_Seat_Vel'].to_numpy(dtype=float).tolist() if has_shoulder else []

        return {
            'data': {
                'index': index,
                'handle_rel': handle_rel,
                'shoulder_rel': shoulder_rel,
                'has_shoulder': has_shoulder,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
            },
            'metadata': {
                'title': 'Relative Velocity — Handle and Shoulder vs. Seat',
                'x_label': 'Cycle index (time)',
                'y_label': 'Relative Velocity (mm/s)',
            },
            'coach_tip': (
                'Relative velocity shows how much each segment moves independently of the seat. '
                'A clean separation between shoulder and handle relative velocities indicates '
                'a well-sequenced kinetic chain (legs → trunk → arms).'
            ),
        }
