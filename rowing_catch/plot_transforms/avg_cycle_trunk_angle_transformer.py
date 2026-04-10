"""Avg Cycle Trunk Angle transform.

Transforms averaged cycle into trunk angle plot data with catch/finish annotations.
"""

from typing import Any, cast

import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


def compute_trunk_angle_metrics(
    avg_cycle: pd.DataFrame,
    catch_idx: int,
    finish_idx: int,
) -> dict[str, Any]:
    """Extract trunk angle series and event values.

    Args:
        avg_cycle: Averaged cycle DataFrame with 'Trunk_Angle' column
        catch_idx: Index of catch
        finish_idx: Index of finish

    Returns:
        Dict with trunk angle arrays and event annotations
    """
    index = avg_cycle.index.tolist()
    trunk = avg_cycle['Trunk_Angle'].to_numpy(dtype=float).tolist()
    catch_angle = float(cast(Any, avg_cycle.loc[catch_idx, 'Trunk_Angle']))
    finish_angle = float(cast(Any, avg_cycle.loc[finish_idx, 'Trunk_Angle']))
    return {
        'index': index,
        'trunk': trunk,
        'catch_idx': catch_idx,
        'finish_idx': finish_idx,
        'catch_angle': catch_angle,
        'finish_angle': finish_angle,
    }


class AvgCycleTrunkAngleComponent(PlotComponent):
    """Averaged cycle trunk angle with catch/finish annotation component."""

    @property
    def name(self) -> str:
        return 'Averaged Cycle — Trunk Angle'

    @property
    def description(self) -> str:
        return 'Trunk angle across the averaged stroke with catch and finish event annotations'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute trunk angle plot data.

        Args:
            avg_cycle: Averaged cycle DataFrame (must have 'Trunk_Angle')
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Not used
            results: Not used

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        metrics = compute_trunk_angle_metrics(avg_cycle, catch_idx, finish_idx)

        return {
            'data': metrics,
            'metadata': {
                'title': 'Trunk Angle across the Averaged Stroke',
                'x_label': 'Cycle index (time)',
                'y_label': 'Degrees from vertical',
            },
            'coach_tip': (
                f'Drive angle: {abs(metrics["catch_angle"] - metrics["finish_angle"]):.1f}°. '
                'A large forward lean at catch and strong layback at finish signals efficient trunk use.'
            ),
        }
