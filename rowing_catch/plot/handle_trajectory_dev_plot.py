"""Handle Trajectory Development renderer.

Renders 2D vertical vs horizontal handle path (box plot).
"""

from typing import Any, cast

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from rowing_catch.plot.theme import COLOR_CATCH, COLOR_COMPARE, COLOR_FINISH, COLOR_HANDLE
from rowing_catch.plot.utils import setup_premium_plot
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
    """Helper to apply markers and text from DIAGRAM_ANNOTATIONS to an axis."""
    if scenario_name == 'None' or scenario_name not in DIAGRAM_ANNOTATIONS:
        return

    scenario_configs = cast(dict[str, Any], DIAGRAM_ANNOTATIONS[scenario_name])
    if diagram_key not in scenario_configs:
        return

    annotations: list[dict[str, Any]] = scenario_configs[diagram_key]

    n_points = len(data)
    y_min, y_max = ax.get_ylim()
    y_range = y_max - y_min

    for ann in annotations:
        x_idx = _calculate_annotation_index(ann, n_points, catch_idx, finish_idx)
        if x_idx is None:
            continue

        x_pos = _get_annotation_x_coordinate(ax, ann, data, x_idx, diagram_key)
        y_pos = _get_annotation_y_coordinate(y_data, x_idx, y_max, y_range)

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


def _calculate_annotation_index(
    ann: dict[str, Any], n_points: int, catch_idx: int | None = None, finish_idx: int | None = None
) -> int | None:
    """Calculate the index for an annotation from its anchor/offset."""
    if 'anchor' in ann:
        anchor = ann['anchor']
        if anchor == 'catch' and catch_idx is not None:
            return catch_idx
        if anchor == 'finish' and finish_idx is not None:
            return finish_idx
    return None


def _get_annotation_x_coordinate(ax: Any, ann: dict[str, Any], data: pd.DataFrame, x_idx: int, diagram_key: str) -> float:
    """Get the physical X coordinate for an annotation."""
    if diagram_key == 'handle_trajectory':
        return cast(float, data['Handle_X_Smooth'].iloc[x_idx])
    return float(x_idx)


def _get_annotation_y_coordinate(y_data, x_idx: int | None, y_max: float, y_range: float) -> float:
    """Get the vertical Y coordinate for an annotation."""
    if y_data is not None and x_idx is not None and x_idx < len(y_data):
        return cast(float, y_data.iloc[x_idx])
    return y_max - y_range * 0.1


def render_handle_trajectory_dev(
    computed_data: dict[str, Any],
    return_fig: bool = False,
) -> plt.Figure | None:
    """Render handle trajectory 2D path plot.

    Args:
        computed_data: Output from HandleTrajectoryDevComponent.compute()
        return_fig: If True, skip st.pyplot() and return the Figure for PDF export.
    """
    data = computed_data['data']
    metadata = computed_data['metadata']
    coach_tip = computed_data['coach_tip']

    fig, ax = setup_premium_plot(metadata['title'], metadata['x_label'], metadata['y_label'])

    # Plot Ideal Box
    ideal_x = data['ideal_x']
    ideal_y = data['ideal_y']
    ax.plot(ideal_x, ideal_y, color=COLOR_COMPARE, linestyle='--', alpha=0.4, label='Reference Path', linewidth=1.5, zorder=1)

    # Grey per-cycle trajectory overlays — behind main trace
    for cyc_x, cyc_y in zip(data.get('cycle_handle_x', []), data.get('cycle_handle_y', []), strict=False):
        ax.plot(cyc_x, cyc_y, color='#AAAAAA', linewidth=0.8, alpha=0.15, zorder=2)

    # Plot Actual Trajectory
    ax.plot(data['handle_x'], data['handle_y'], color=COLOR_HANDLE, linewidth=3, label='Your Data', zorder=3)

    # Comparison
    if data['scenario_x'] is not None:
        ax.plot(
            data['scenario_x'],
            data['scenario_y'],
            color=COLOR_COMPARE,
            linestyle=':',
            alpha=0.6,
            label=f'Comparison: {metadata.get("scenario_name", "Reference")}',
            zorder=2,
        )

    # Mark catch/finish
    ax.scatter(data['catch_x'], data['catch_y'], color=COLOR_CATCH, s=100, label='Catch', zorder=4)
    ax.scatter(data['finish_x'], data['finish_y'], color=COLOR_FINISH, s=100, label='Finish', zorder=4)

    ax.invert_yaxis()  # Up is higher, down is deeper
    ax.legend()

    if not return_fig:
        st.pyplot(fig)
        st.info(f"**Coach's Tip:** {coach_tip}")
        plt.close(fig)
        return None

    return fig
