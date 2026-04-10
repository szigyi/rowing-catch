"""Debug Power Curve transform.

Transforms averaged cycle V³ power proxy data into plot-ready format.
"""

from typing import Any

import pandas as pd

from rowing_catch.plot_transformer.base import PlotComponent


class DebugPowerCurveComponent(PlotComponent):
    """Full-drive power curve breakdown component (V³ model)."""

    @property
    def name(self) -> str:
        return 'Power Curve (V³ Drag Model)'

    @property
    def description(self) -> str:
        return 'Segmental power breakdown across the drive phase using the V³ drag model'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute power curve data.

        Args:
            avg_cycle: Averaged cycle DataFrame with Power_Total, Power_Legs,
                       Power_Trunk, Power_Arms columns
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Not used
            results: Not used

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        drive_slice = avg_cycle.iloc[catch_idx:finish_idx]

        x = drive_slice.index.tolist()
        has_power_total = 'Power_Total' in drive_slice.columns
        total = drive_slice['Power_Total'].clip(lower=0).to_numpy(dtype=float).tolist() if has_power_total else []
        total_raw = drive_slice['Power_Total'].to_numpy(dtype=float).tolist() if 'Power_Total' in drive_slice.columns else []
        legs = drive_slice['Power_Legs'].to_numpy(dtype=float).tolist() if 'Power_Legs' in drive_slice.columns else []
        trunk = drive_slice['Power_Trunk'].to_numpy(dtype=float).tolist() if 'Power_Trunk' in drive_slice.columns else []
        arms = drive_slice['Power_Arms'].to_numpy(dtype=float).tolist() if 'Power_Arms' in drive_slice.columns else []

        return {
            'data': {
                'x': x,
                'total_clipped': total,
                'total_raw': total_raw,
                'legs': legs,
                'trunk': trunk,
                'arms': arms,
                'has_legs': bool(legs),
                'has_trunk': bool(trunk),
                'has_arms': bool(arms),
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
            },
            'metadata': {
                'title': 'Power Curve — V³ Drag Model (Drive Phase)',
                'x_label': 'Cycle index (time)',
                'y_label': 'Power Proxy (V³ units)',
            },
            'coach_tip': (
                'The power curve should peak early in the drive (legs dominant) and taper smoothly. '
                'A sharp late peak suggests over-reliance on trunk and arms after the legs are spent.'
            ),
        }
