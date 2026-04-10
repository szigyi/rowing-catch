"""Power Accumulation plot transform.

Segmental power contribution from Legs, Trunk, and Arms during drive phase.
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.plot_transformer.base import PlotComponent


class PowerAccumulationComponent(PlotComponent):
    """Power accumulation by body segment component."""

    @property
    def name(self) -> str:
        return 'Power Accumulation'

    @property
    def description(self) -> str:
        return 'Segmental power contribution during drive phase'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute power accumulation plot data.

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

        # Only plot drive phase
        drive = avg_cycle.loc[catch_idx:finish_idx].copy()
        if len(drive) < 2:
            return {
                'data': {'has_data': False},
                'metadata': {
                    'title': 'Segmental Power Accumulation',
                    'x_label': 'Drive Progress (%)',
                    'y_label': 'Power Proxy (Watts-like)',
                },
                'coach_tip': 'Drive phase too short for power analysis.',
            }

        drive_progress = np.linspace(0, 100, len(drive))

        p_legs = drive['Power_Legs'].clip(lower=0).values
        p_trunk = drive['Power_Trunk'].clip(lower=0).values
        p_arms = drive['Power_Arms'].clip(lower=0).values

        # Scenario comparison (if provided)
        scenario_power_total = None
        scenario_progress = None
        if scenario_data is not None:
            try:
                s_drive = scenario_data.loc[catch_idx:finish_idx] if len(scenario_data) > finish_idx else scenario_data
                scenario_power_total = s_drive['Power_Total'].clip(lower=0).values
                scenario_progress = np.linspace(0, 100, len(s_drive))
            except KeyError, IndexError:
                pass

        return {
            'data': {
                'has_data': True,
                'drive_progress': drive_progress,
                'power_legs': p_legs,
                'power_trunk': p_trunk,
                'power_arms': p_arms,
                'scenario_power_total': scenario_power_total,
                'scenario_progress': scenario_progress,
                'drive': drive,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
            },
            'metadata': {
                'title': 'Segmental Power Accumulation',
                'x_label': 'Drive Progress (%)',
                'y_label': 'Power Proxy (Watts-like)',
                'scenario_name': scenario_name,
            },
            'coach_tip': (
                "The 'Power Curve' should be smooth and convex. "
                'Legs should dominate the first 50%, followed by a smooth handover to the Trunk and finally Arms.'
            ),
        }
