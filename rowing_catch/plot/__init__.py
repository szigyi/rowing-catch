"""Plot rendering layer - pure visualization code.

This layer transforms plot-ready data into matplotlib figures and Streamlit output.
Depends on: components (for compute logic), theme (for styling).
"""

__all__ = [
    'theme',
    'utils',
    'trunk_angle_plot',
    'trunk_angle_separation_plot',
    'handle_seat_distance_plot',
    'rhythm_consistency_plot',
    'recovery_slide_control_plot',
    'handle_trajectory_dev_plot',
    'power_accumulation_plot',
    'kinetic_chain_plot',
    'performance_metrics_plot',
    # Debug / pipeline plots
    'signal_smoothing_comparison_plot',
    'catch_detection_plot',
    'cycle_overlay_mean_std_plot',
    'avg_cycle_multi_axis_plot',
    'production_finish_trajectory_plot',
    'avg_cycle_trunk_angle_plot',
    'velocity_profile_plot',
    'relative_velocity_plot',
    'jerk_comparison_plot',
    'debug_power_curve_plot',
    'drive_recovery_balance_plot',
]
