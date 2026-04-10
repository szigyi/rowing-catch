"""Plot transform layer - data preparation and computation.

Transforms convert analysis results into plot-ready data structures.
This layer ensures all rendering logic in plot/ can remain pure and testable.
"""

from rowing_catch.plot_transformer.avg_cycle_multi_axis_transformer import AvgCycleMultiAxisComponent
from rowing_catch.plot_transformer.avg_cycle_trunk_angle_transformer import AvgCycleTrunkAngleComponent
from rowing_catch.plot_transformer.base import PlotComponent
from rowing_catch.plot_transformer.catch.catch_detection_transformer import CatchDetectionComponent
from rowing_catch.plot_transformer.cycle_overlay_mean_std_transformer import CycleOverlayMeanStdComponent
from rowing_catch.plot_transformer.handle_seat_distance_transformer import HandleSeatDistanceComponent
from rowing_catch.plot_transformer.handle_trajectory_dev_transformer import HandleTrajectoryDevComponent
from rowing_catch.plot_transformer.jerk_comparison_transformer import JerkComparisonComponent
from rowing_catch.plot_transformer.kinetic_chain_transformer import KineticChainComponent
from rowing_catch.plot_transformer.performance_metrics_transformer import PerformanceMetricsComponent
from rowing_catch.plot_transformer.power_curve.debug_power_curve_transformer import DebugPowerCurveComponent
from rowing_catch.plot_transformer.power_curve.power_accumulation_transformer import PowerAccumulationComponent
from rowing_catch.plot_transformer.production_finish_trajectory_transformer import ProductionFinishTrajectoryComponent
from rowing_catch.plot_transformer.recovery_slide_control_transformer import RecoverySlideControlComponent
from rowing_catch.plot_transformer.rhythm.drive_recovery_balance_transformer import DriveRecoveryBalanceComponent
from rowing_catch.plot_transformer.rhythm.rhythm_consistency_transformer import RhythmConsistencyComponent
from rowing_catch.plot_transformer.signal_smoothing_comparison_transformer import SignalSmoothingComparisonComponent
from rowing_catch.plot_transformer.trunk.trunk_angle_separation_transformer import TrunkAngleSeparationComponent
from rowing_catch.plot_transformer.trunk.trunk_angle_transformer import TrunkAngleComponent
from rowing_catch.plot_transformer.velocity.relative_velocity_transformer import RelativeVelocityComponent
from rowing_catch.plot_transformer.velocity.velocity_profile_transformer import VelocityProfileComponent

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
    'SignalSmoothingComparisonComponent',
    'CatchDetectionComponent',
    'CycleOverlayMeanStdComponent',
    'AvgCycleMultiAxisComponent',
    'ProductionFinishTrajectoryComponent',
    'AvgCycleTrunkAngleComponent',
    'VelocityProfileComponent',
    'RelativeVelocityComponent',
    'JerkComparisonComponent',
    'DebugPowerCurveComponent',
    'DriveRecoveryBalanceComponent',
]
