"""Abstract base class for plot components.

A component transforms analytical results (avg_cycle, metrics, etc.) into
plot-ready data structures. This separates data computation from rendering.
"""

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class PlotComponent(ABC):
    """Abstract base for all plot components.

    A component transforms analytical results into plot-ready data structures.
    Subclasses compute everything needed for rendering in a single `compute()`
    call, returning structured data that a plot renderer can then visualize.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Plot display name (e.g., 'Trunk Angle', 'Velocity Coordination').

        Returns:
            Display name suitable for UI menus
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Short description of what this plot shows.

        Returns:
            1-2 sentence description
        """
        pass

    @abstractmethod
    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Transform analytical results into plot-ready data.

        This method does all plot-specific computation. The returned dict
        is passed to the corresponding plot renderer.

        Args:
            avg_cycle: Averaged stroke cycle DataFrame from pipeline
            catch_idx: Index of the catch point
            finish_idx: Index of the finish point
            ghost_cycle: Optional reference cycle for comparison (e.g., ideal scenario)
            results: Full analysis results dict from process_rowing_data() (for extra metrics)

        Returns:
            Dict with structure:
            {
                'data': {...},           # Main plot data (coordinates, values, etc.)
                'ghost_data': {...},     # Optional comparison data
                'metadata': {            # Plot metadata
                    'title': str,
                    'xlabel': str,
                    'ylabel': str,
                    ...
                },
                'coach_tip': str,        # Insight to display to user
            }

        Example:
            >>> component = VelocityCoordinationComponent()
            >>> computed = component.compute(avg_cycle, catch_idx, finish_idx)
            >>> # Pass computed to render_velocity_coordination(computed)
        """
        pass


__all__ = ['PlotComponent']
