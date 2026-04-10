"""Plot transform layer - data preparation and computation.

Transforms convert analysis results into plot-ready data structures.
This layer ensures all rendering logic in plots/ can remain pure and testable.
"""

from rowing_catch.plot_transforms.base import PlotComponent
from rowing_catch.plot_transforms.handle_seat_distance import HandleSeatDistanceComponent
from rowing_catch.plot_transforms.handle_trajectory_dev import HandleTrajectoryDevComponent
from rowing_catch.plot_transforms.kinetic_chain import KineticChainComponent
from rowing_catch.plot_transforms.performance_metrics import PerformanceMetricsComponent
from rowing_catch.plot_transforms.power_accumulation import PowerAccumulationComponent
from rowing_catch.plot_transforms.recovery_slide_control import RecoverySlideControlComponent
from rowing_catch.plot_transforms.registry import get_all_plots, get_plot_component, list_plot_ids
from rowing_catch.plot_transforms.rhythm_consistency import RhythmConsistencyComponent
from rowing_catch.plot_transforms.trunk_angle import TrunkAngleComponent
from rowing_catch.plot_transforms.trunk_angle_separation import TrunkAngleSeparationComponent

__all__ = [
    'PlotComponent',
    'TrunkAngleComponent',
    'TrunkAngleSeparationComponent',
    'HandleSeatDistanceComponent',
    'RhythmConsistencyComponent',
    'RecoverySlideControlComponent',
    'HandleTrajectoryDevComponent',
    'PowerAccumulationComponent',
    'KineticChainComponent',
    'PerformanceMetricsComponent',
    'get_all_plots',
    'get_plot_component',
    'list_plot_ids',
]
