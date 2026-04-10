from typing import Any, cast

import pandas as pd

from rowing_catch.ui.annotations_data import DIAGRAM_ANNOTATIONS


def _apply_annotations(
    ax: Any,
    diagram_key: str,
    data: pd.DataFrame,
    catch_idx: int | None = None,
    finish_idx: int | None = None,
    y_data: pd.Series | None = None,
    scenario_name: str = 'None',
) -> None:
    """
    Helper to apply markers and text from DIAGRAM_ANNOTATIONS to an axis.
    Only applies if a scenario is selected.
    """
    if scenario_name == 'None' or scenario_name not in DIAGRAM_ANNOTATIONS:
        return

    scenario_configs = cast(dict[str, Any], DIAGRAM_ANNOTATIONS[scenario_name])
    if diagram_key not in scenario_configs:
        return

    annotations: list[dict[str, Any]] = scenario_configs[diagram_key]

    # Get common data characteristics
    n_points = len(data)

    # Determine the y-range for normalized placement if y_data is not provided
    y_min, y_max = ax.get_ylim()
    y_range = y_max - y_min

    for ann in annotations:
        # 1. Calculate the index to look up
        x_idx = _calculate_annotation_index(ann, n_points, catch_idx, finish_idx)
        if x_idx is None:
            continue

        # 2. Get the physical X coordinate for the plot
        x_pos = _get_annotation_x_coordinate(ax, ann, data, x_idx, diagram_key)

        # 3. Get the vertical Y coordinate
        y_pos = _get_annotation_y_coordinate(y_data, x_idx, y_max, y_range)

        # Apply the annotation
        color = ann.get('color', '#333333')
        offset = ann.get('offset', (20, 20))

        ax.annotate(
            ann['text'],
            xy=(x_pos, y_pos),
            xytext=offset,
            textcoords='offset points',
            arrowprops=dict(arrowstyle='->', color=color, connectionstyle='arc3,rad=.2', lw=1.5),
            fontsize=10,
            fontweight='bold',
            color=color,
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=color, alpha=0.9, lw=1.5),
            zorder=10,
        )


def _calculate_annotation_index(ann: dict, n_points: int, catch_idx: int | None, finish_idx: int | None) -> int | None:
    """Helper to calculate the integer index for an annotation based on its timing type."""
    if ann['x_type'] == 'percentage_of_cycle':
        return int((ann['x'] / 100) * (n_points - 1))

    if ann['x_type'] == 'percentage_of_drive':
        if catch_idx is not None and finish_idx is not None:
            drive_len = finish_idx - catch_idx
            return int(catch_idx + (ann['x'] / 100) * drive_len)
        return None

    if ann['x_type'] == 'percentage_of_recovery':
        if finish_idx is not None:
            rec_len = n_points - finish_idx
            return int(finish_idx + (ann['x'] / 100) * rec_len)
        return None

    if ann['x_type'] == 'point':
        if ann['point_name'] == 'catch' and catch_idx is not None:
            return catch_idx
        if ann['point_name'] == 'finish' and finish_idx is not None:
            return finish_idx
        return None

    return None


def _get_annotation_x_coordinate(ax, ann: dict, data: pd.DataFrame, x_idx: int, diagram_key: str) -> float:
    """Map a data index to a plot's physical X-coordinate."""
    # Ensure index is within bounds
    x_idx = min(max(0, x_idx), len(data) - 1)
    base_idx = data.index[x_idx]

    # Handle trajectory: X is Handle_X
    if diagram_key == 'handle_trajectory' and 'Handle_X_Smooth' in data.columns:
        try:
            return float(data.loc[base_idx, 'Handle_X_Smooth'])
        except Exception:
            return float(base_idx)

    # Trunk angle: X is Seat_X
    if diagram_key == 'trunk_angle_separation' and 'Seat_X_Smooth' in data.columns:
        try:
            return float(data.loc[base_idx, 'Seat_X_Smooth'])
        except Exception:
            return float(base_idx)

    # Special handling for percentage-based X axes
    x_label = str(ax.get_xlabel())
    if '%' in x_label:
        if ann['x_type'] in ['percentage_of_drive', 'percentage_of_recovery']:
            return float(ann['x'])
        if ann['x_type'] == 'point':
            return 0.0 if ann['point_name'] == 'catch' else 100.0

    return float(base_idx)


def _get_annotation_y_coordinate(y_data: pd.Series | None, x_idx: int, y_max: float, y_range: float) -> float:
    """Determine the vertical Y coordinate for an annotation."""
    if y_data is not None:
        try:
            x_idx = min(max(0, x_idx), len(y_data) - 1)
            return float(y_data.iloc[int(x_idx)])
        except Exception:
            return y_max - (y_range * 0.1)

    return y_max - (y_range * 0.2)
