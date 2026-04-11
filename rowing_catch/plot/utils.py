"""Shared utilities for plot rendering."""

from collections.abc import Sequence
from typing import Any, cast

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from rowing_catch.plot.theme import (
    ANNOTATION_LABEL_BG,
    BG_COLOR_AXES,
    BG_COLOR_FIGURE,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_SUB,
    GRID_COLOR,
    SPINE_COLOR,
)
from rowing_catch.plot_transformer.annotations import (
    AnnotationEntry,
    BandAnnotation,
    PhaseAnnotation,
    PointAnnotation,
    SegmentAnnotation,
    assign_annotation_colors,
)


def setup_premium_plot(title='', x_label='', y_label='', figsize=(10, 5)):
    """Set up a standard matplotlib figure with the premium UI aesthetic.

    Args:
        title: Plot title
        x_label: X-axis label
        y_label: Y-axis label
        figsize: Figure size (width, height)

    Returns:
        Tuple of (fig, ax) ready for plotting
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Modern Styling
    fig.patch.set_facecolor(BG_COLOR_FIGURE)
    ax.set_facecolor(BG_COLOR_AXES)

    # Clean up spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(SPINE_COLOR)
    ax.spines['bottom'].set_color(SPINE_COLOR)

    # Subtle horizontal gridlines
    ax.grid(axis='y', linestyle='-', linewidth=0.5, color=GRID_COLOR, zorder=0)

    # Fonts and labeling
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold', pad=20, color=COLOR_TEXT_MAIN)
    if x_label:
        ax.set_xlabel(x_label, fontweight='bold', color=COLOR_TEXT_SUB, labelpad=10)
    if y_label:
        ax.set_ylabel(y_label, fontweight='bold', color=COLOR_TEXT_SUB, labelpad=10)

    ax.tick_params(axis='x', colors=COLOR_TEXT_SUB)
    ax.tick_params(axis='y', colors=COLOR_TEXT_SUB)

    # Ensure constrained layout padding to prevent edge cropping in Streamlit
    try:
        cast(Any, fig).set_constrained_layout_pads(w_pad=0.04, h_pad=0.04, wspace=0.02, hspace=0.02)
    except Exception:
        pass

    return fig, ax


def get_traffic_light(value, ideal, yellow_threshold=15, green_threshold=5):
    """Return a status based on deviation from ideal value.

    Args:
        value: Observed value
        ideal: Target / ideal value
        yellow_threshold: Max % deviation still considered Yellow
        green_threshold: Max % deviation considered Green

    Returns:
        One of: 'Green', 'Yellow', 'Red'
    """
    deviation = abs(value - ideal) / ideal * 100
    if deviation <= green_threshold:
        return 'Green'
    elif deviation <= yellow_threshold:
        return 'Yellow'
    else:
        return 'Red'


# ---------------------------------------------------------------------------
# Annotation rendering helpers
# ---------------------------------------------------------------------------


def draw_segment_backdrop(
    ax: matplotlib.axes.Axes,
    x: list[float],
    y: list[float],
    color: str,
    n_layers: int = 4,
    base_linewidth: float = 2.5,
) -> None:
    """Draw a line segment with a wide semi-transparent backing line.

    Renders a single wide, semi-transparent line behind the original line
    to visually highlight the segment without overpowering the main trace.

    Args:
        ax: Target matplotlib axes
        x: X coordinates of the segment
        y: Y coordinates of the segment (same length as x)
        color: Hex color string for the highlight
        n_layers: Unused — kept for API compatibility
        base_linewidth: Width of the original line (backing line is proportionally wider)
    """
    ax.plot(
        x,
        y,
        color=color,
        linewidth=base_linewidth * 5,
        alpha=0.25,
        solid_capstyle='round',
        zorder=4,  # behind the main line
    )


def apply_annotations(
    ax: matplotlib.axes.Axes,
    annotations: Sequence[AnnotationEntry],
    active_labels: set[str] | None = None,
    axis_id: str = 'main',
    color_overrides: dict[str, str] | None = None,
) -> list[tuple[str, str, str]]:
    """Apply visible annotations to a matplotlib axes.

    Filters annotations by axis_id (for multi-axis plots) and active_labels
    (for toggle control), then draws each one using the appropriate style.

    Args:
        ax: The matplotlib axes to annotate
        annotations: All annotations from compute() — may include annotations
                     for other axes (filtered by axis_id)
        active_labels: Set of label strings to render. None means show all.
        axis_id: Only annotations with this axis_id are drawn on this axes.
        color_overrides: Optional dict mapping annotation label → hex color string.
                         Applied after palette auto-assignment, so the renderer can
                         inject theme-aware colors for specific annotations without
                         violating layer rules in the transformer.
                         Example: {'[A4]': '#00CC96', '[A5]': '#EF553B'}

    Returns:
        List of (label, description, coach_tip) tuples for the visible annotations,
        in the order they appear. Pass this to render_annotation_legend_on_figure().
    """
    # Filter to this axis, assign palette colors where needed
    axis_annotations = [a for a in annotations if a.axis_id == axis_id]
    axis_annotations = assign_annotation_colors(axis_annotations)

    # Apply renderer-supplied color overrides (e.g. theme colors from plot layer)
    if color_overrides:
        import dataclasses as _dc
        axis_annotations = [
            _dc.replace(a, color=color_overrides[a.label])
            if a.label in color_overrides else a
            for a in axis_annotations
        ]

    # Filter by toggle state
    if active_labels is not None:
        axis_annotations = [a for a in axis_annotations if a.label in active_labels]

    legend_items: list[tuple[str, str, str]] = []

    for ann in axis_annotations:
        color = ann.color or '#888888'

        if isinstance(ann, PointAnnotation):
            _draw_point_annotation(ax, ann, color)
        elif isinstance(ann, SegmentAnnotation):
            _draw_segment_annotation(ax, ann, color)
        elif isinstance(ann, BandAnnotation):
            _draw_band_annotation(ax, ann, color)
        elif isinstance(ann, PhaseAnnotation):
            _draw_phase_annotation(ax, ann, color)

        legend_items.append((ann.label, ann.description, ann.coach_tip))

    return legend_items


def render_annotation_legend_on_figure(
    fig: matplotlib.figure.Figure,
    ax_legend: matplotlib.axes.Axes,
    legend_items: list[tuple[str, str, str]],
    colors: list[str] | None = None,
    font_size: int = 8,
) -> None:
    """Render an annotation reference table inside a dedicated legend axes.

    Draws a 3-column table (Ref | Description | Coach Tip) into ax_legend so
    the legend is fully baked into the matplotlib Figure — visible in both
    Streamlit display and PDF export. The Coach Tip column is omitted entirely
    when all tips are empty, keeping the table compact for unannotated plots.

    Args:
        fig: The matplotlib figure (unused directly; kept for API symmetry)
        ax_legend: A dedicated axes reserved for the legend table.
        legend_items: List of (label, description, coach_tip) tuples from apply_annotations()
        colors: Optional per-row label colors (one per data row). Defaults to '#555555'.
        font_size: Font size for table rows
    """
    if not legend_items:
        ax_legend.axis('off')
        return

    ax_legend.axis('off')
    ax_legend.set_facecolor(BG_COLOR_FIGURE)

    row_colors_list = colors if colors else ['#555555'] * len(legend_items)

    # Only show Coach Tip column when at least one tip is non-empty
    has_tips = any(tip for _, _, tip in legend_items)

    if has_tips:
        col_labels = ['Ref', 'Description', 'Coach Tip']
        cell_text = [[label, desc, tip] for label, desc, tip in legend_items]
    else:
        col_labels = ['Ref', 'Description']
        cell_text = [[label, desc] for label, desc, _ in legend_items]

    from typing import cast as _cast

    tbl = ax_legend.table(
        cellText=cell_text,
        colLabels=col_labels,
        cellLoc='left',
        loc='upper left',
        bbox=_cast(matplotlib.transforms.Bbox, (0.0, 0.0, 1.0, 1.0)),
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(font_size)
    tbl.auto_set_column_width(list(range(len(col_labels))))

    # Style: subtle borders, light header, colored ref labels, italic coach tips
    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor('#E8E8E8')
        cell.set_linewidth(0.5)
        if row == 0:
            cell.set_facecolor('#F0F0F0')
            cell.set_text_props(fontweight='bold', color='#444444')
        else:
            cell.set_facecolor(BG_COLOR_FIGURE)
            if col == 0:
                label_color = row_colors_list[row - 1] if row - 1 < len(row_colors_list) else '#555555'
                cell.set_text_props(fontweight='bold', color=label_color)
            elif has_tips and col == 2:
                # Coach Tip column: italic, slightly muted
                cell.set_text_props(style='italic', color='#555555')
            else:
                cell.set_text_props(color='#444444')


# ---------------------------------------------------------------------------
# Private drawing helpers (not exported)
# ---------------------------------------------------------------------------


def _draw_point_annotation(
    ax: matplotlib.axes.Axes,
    ann: PointAnnotation,
    color: str,
) -> None:
    """Draw a PointAnnotation as a badge label or callout with arrow."""
    if ann.style == 'callout':
        # Leader-line callout: arrow from badge to data point
        x_off = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.06
        y_off = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.10
        ax.annotate(
            ann.label,
            xy=(ann.x, ann.y),
            xytext=(ann.x + x_off, ann.y + y_off),
            fontsize=7,
            fontweight='bold',
            color=color,
            arrowprops=dict(
                arrowstyle='-|>',
                color=color,
                lw=0.9,
                connectionstyle='arc3,rad=0.15',
            ),
            bbox=dict(
                boxstyle='round,pad=0.25',
                facecolor=ANNOTATION_LABEL_BG,
                edgecolor=color,
                linewidth=0.9,
                alpha=0.95,
            ),
            zorder=10,
        )
    else:
        # Compact badge label directly at the point
        y_offset = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.05
        ax.text(
            ann.x,
            ann.y + y_offset,
            ann.label,
            fontsize=7,
            fontweight='bold',
            color=color,
            ha='center',
            va='bottom',
            bbox=dict(
                boxstyle='round,pad=0.22',
                facecolor=ANNOTATION_LABEL_BG,
                edgecolor=color,
                linewidth=0.8,
                alpha=0.95,
            ),
            zorder=10,
        )
    # Dot at the data point
    ax.plot(ann.x, ann.y, 'o', color=color, markersize=5, zorder=11)


def _draw_segment_annotation(
    ax: matplotlib.axes.Axes,
    ann: SegmentAnnotation,
    color: str,
) -> None:
    """Draw a SegmentAnnotation as a glow, highlight, or both."""
    x = ann.x
    y = ann.y

    if not x or not y:
        return  # Nothing to draw without data

    if ann.style in ('glow', 'highlight+glow'):
        draw_segment_backdrop(ax, x, y, color, n_layers=4, base_linewidth=2.5)

    if ann.style in ('highlight', 'highlight+glow'):
        ax.plot(
            x,
            y,
            color=color,
            linewidth=4.5,
            solid_capstyle='round',
            zorder=7,
        )

    # Label badge at the midpoint of the segment
    mid = len(x) // 2
    y_offset = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.05
    ax.text(
        x[mid],
        y[mid] + y_offset,
        ann.label,
        fontsize=7,
        fontweight='bold',
        color=color,
        ha='center',
        va='bottom',
        bbox=dict(
            boxstyle='round,pad=0.22',
            facecolor=ANNOTATION_LABEL_BG,
            edgecolor=color,
            linewidth=0.8,
            alpha=0.95,
        ),
        zorder=12,
    )


def _draw_band_annotation(
    ax: matplotlib.axes.Axes,
    ann: BandAnnotation,
    color: str,
) -> None:
    """Draw a BandAnnotation as a shaded horizontal region."""
    xlim = ax.get_xlim()
    x_start = ann.x_start if ann.x_start is not None else xlim[0]
    x_end = ann.x_end if ann.x_end is not None else xlim[1]

    x_fill = np.array([x_start, x_end])
    ax.fill_between(
        x_fill,
        ann.y_low,
        ann.y_high,
        color=color,
        alpha=0.12,
        linewidth=0,
        zorder=1,
    )
    # Dashed borders
    for y_val in (ann.y_low, ann.y_high):
        ax.plot(
            [x_start, x_end],
            [y_val, y_val],
            color=color,
            linewidth=0.8,
            linestyle='--',
            alpha=0.5,
            zorder=2,
        )
    # Optional in-plot display name — placed at 80% across the visible band width
    if ann.display_name:
        x_text = x_start + (x_end - x_start) * 0.80
        y_mid = (ann.y_low + ann.y_high) / 2
        ax.text(
            x_text,
            y_mid,
            ann.display_name,
            color=color,
            fontsize=8,
            fontweight='medium',
            ha='center',
            va='center',
            bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.75, pad=1.2),
            zorder=3,
        )


def _draw_phase_annotation(
    ax: matplotlib.axes.Axes,
    ann: PhaseAnnotation,
    color: str,
) -> None:
    """Draw a PhaseAnnotation as a vertical shaded region."""
    ax.axvspan(
        ann.x_start,
        ann.x_end,
        color=color,
        alpha=0.09,
        linewidth=0,
        zorder=1,
    )
    # Vertical border lines
    for x_val in (ann.x_start, ann.x_end):
        ax.axvline(x_val, color=color, linewidth=0.8, linestyle=':', alpha=0.5, zorder=2)


__all__ = [
    'apply_annotations',
    'draw_segment_backdrop',
    'get_traffic_light',
    'render_annotation_legend_on_figure',
    'setup_premium_plot',
]
