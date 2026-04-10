"""Recovery Slide Control plot transform.

Shows seat velocity during recovery phase to detect rushing or pausing.
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


class RecoverySlideControlComponent(PlotComponent):
    """Recovery slide control component."""

    @property
    def name(self) -> str:
        return 'Recovery Slide Control'

    @property
    def description(self) -> str:
        return 'Seat velocity during recovery phase'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute recovery slide control plot data.

        Args:
            avg_cycle: DataFrame with rowing stroke data
            catch_idx: Index of catch (not used)
            finish_idx: Index of finish (start of recovery)
            ghost_cycle: Not used
            results: Optional results dict with scenario_name

        Returns:
            Dict with plot data and metadata
        """
        scenario_name = results.get('scenario_name', 'None') if results else 'None'

        # Recovery is from finish to end of cycle
        rec = avg_cycle.loc[finish_idx:].copy()

        # Recovery progress 0-100%
        rec_progress = np.linspace(0, 100, len(rec)) if len(rec) > 0 else np.array([])

        # Seat velocity (absolute value for "speed")
        seat_speed = np.abs(rec['Seat_X_Vel'].values) if len(rec) > 0 else np.array([])

        return {
            'data': {
                'recovery_progress': rec_progress,
                'seat_speed': seat_speed,
                'finish_idx': finish_idx,
                'recovery_data': rec,
            },
            'metadata': {
                'title': 'Recovery Slide Control',
                'x_label': 'Recovery Progress (%)',
                'y_label': 'Seat Velocity',
                'scenario_name': scenario_name,
            },
            'coach_tip': (
                "Look for a symmetric 'bell curve' on the slide. A sharp peak early in recovery indicates 'rushing' the slide."
            ),
        }
