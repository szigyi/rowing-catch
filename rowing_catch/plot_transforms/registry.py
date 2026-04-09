"""Plot component registry - central discovery point for all available plots."""

from rowing_catch.plot_transforms.rhythm import ConsistencyRhythmComponent
from rowing_catch.plot_transforms.trajectory import HandleTrajectoryComponent
from rowing_catch.plot_transforms.trunk_angle import TrunkAngleComponent
from rowing_catch.plot_transforms.velocity import VelocityCoordinationComponent

# Map of component ID → component instance
COMPONENTS = {
    'trunk_angle': TrunkAngleComponent(),
    'velocity': VelocityCoordinationComponent(),
    'trajectory': HandleTrajectoryComponent(),
    'rhythm': ConsistencyRhythmComponent(),
}


def get_all_plots() -> dict:
    """Get dictionary of all available plots.

    Returns:
        Dict mapping plot_id => plot_name (suitable for UI menus)

        Example:
            >>> get_all_plots()
            {
                'trunk_angle': 'Trunk Angle & Range',
                'velocity': 'Velocity Coordination',
                ...
            }
    """
    return {name: comp.name for name, comp in COMPONENTS.items()}


def get_plot_component(plot_id: str):
    """Get a plot component by ID.

    Args:
        plot_id: One of 'trunk_angle', 'velocity', 'trajectory', 'rhythm'

    Returns:
        PlotComponent instance, or None if not found

    Example:
        >>> comp = get_plot_component('trunk_angle')
        >>> computed = comp.compute(avg_cycle, catch_idx, finish_idx)
    """
    return COMPONENTS.get(plot_id)


def list_plot_ids() -> list:
    """Get list of all available plot IDs.

    Returns:
        List of plot identifiers
    """
    return list(COMPONENTS.keys())


__all__ = ['get_all_plots', 'get_plot_component', 'list_plot_ids', 'COMPONENTS']
