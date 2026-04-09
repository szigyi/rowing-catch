"""Plot transform layer - data preparation and computation.

Transforms convert analysis results into plot-ready data structures.
This layer ensures all rendering logic in plots/ can remain pure and testable.
"""

from rowing_catch.plot_transforms.base import PlotComponent
from rowing_catch.plot_transforms.registry import get_all_plots, get_plot_component, list_plot_ids
from rowing_catch.plot_transforms.rhythm import ConsistencyRhythmComponent
from rowing_catch.plot_transforms.trajectory import HandleTrajectoryComponent
from rowing_catch.plot_transforms.trunk_angle import TrunkAngleComponent
from rowing_catch.plot_transforms.velocity import VelocityCoordinationComponent

__all__ = [
    'PlotComponent',
    'TrunkAngleComponent',
    'VelocityCoordinationComponent',
    'HandleTrajectoryComponent',
    'ConsistencyRhythmComponent',
    'get_all_plots',
    'get_plot_component',
    'list_plot_ids',
]
