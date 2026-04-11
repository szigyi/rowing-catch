"""Annotation data model for plot components.

Annotations are computed in the transform layer (Layer 2) and consumed by
renderers (Layer 3). They carry no UI logic — they are pure data.

Each PlotComponent.compute() may return an 'annotations' key containing a
list of AnnotationEntry objects. Renderers call apply_annotations() from
plot/utils.py to draw them on the axes.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

# ---------------------------------------------------------------------------
# Annotation palette — distinct from main theme colors to avoid visual conflict.
# Used by apply_annotations() to auto-assign colors when color=None.
# ---------------------------------------------------------------------------
ANNOTATION_COLORS: list[str] = [
    '#D946EF',  # Fuchsia — [P_] points (slot 1)
    '#14B8A6',  # Teal    — [P_] points (slot 2)
    '#F59E0B',  # Amber   — [S_] segments (slot 3)
    '#F97316',  # Orange  — [S_] segments (slot 4)
    '#10B981',  # Emerald — [Z_] zones (slot 5, typically renderer-overridden)
    '#EC4899',  # Pink    — [Z_] zones (slot 6, typically renderer-overridden)
]


# ---------------------------------------------------------------------------
# Annotation dataclasses
# ---------------------------------------------------------------------------


@dataclass
class PointAnnotation:
    """Annotates a single (x, y) point on the plot.

    Attributes:
        label: Short reference shown on the plot, e.g. '[A1]'
        description: Full explanation shown in the legend table, e.g. 'Catch Lean: −31°'
        x: Data x-coordinate of the annotated point
        y: Data y-coordinate of the annotated point
        style: 'callout' draws an arrow+box; 'label' draws a compact badge
        color: Hex color string. None → auto-assigned from ANNOTATION_COLORS
        axis_id: Identifies the target axes in multi-axis plots ('main', 'top', 'bot', …)
        coach_tip: Short coaching cue shown in the legend table's Coach Tip column.
                   Empty string → column cell is blank.
    """

    label: str
    description: str
    x: float
    y: float
    style: Literal['callout', 'label'] = 'label'
    color: str | None = None
    axis_id: str = 'main'
    coach_tip: str = ''


@dataclass
class SegmentAnnotation:
    """Annotates a contiguous range on a plotted line.

    Attributes:
        label: Short reference shown on the plot, e.g. '[S1]'
        description: Full explanation shown in the legend table
        x_start: Start x-coordinate of the segment
        x_end: End x-coordinate of the segment
        x: Ordered list of x values in the segment (for glow rendering)
        y: Corresponding y values (must match len(x))
        style: Visual style — 'highlight' (thick colored line), 'glow' (neon layers),
               or 'highlight+glow' (both combined)
        color: Hex color. None → auto-assigned
        axis_id: Target axes identifier
        coach_tip: Short coaching cue for the legend table. Empty → blank cell.
    """

    label: str
    description: str
    x_start: float
    x_end: float
    x: list[float] = field(default_factory=list)
    y: list[float] = field(default_factory=list)
    style: Literal['highlight', 'glow', 'highlight+glow'] = 'glow'
    color: str | None = None
    axis_id: str = 'main'
    coach_tip: str = ''


@dataclass
class BandAnnotation:
    """Annotates a horizontal target zone (shaded band) on the plot.

    Attributes:
        label: Short reference shown on the plot, e.g. '[Z1]'
        description: Full explanation shown in the legend table
        y_low: Lower bound of the band (data units)
        y_high: Upper bound of the band (data units)
        display_name: Optional short text rendered inside the band on the plot itself.
                      E.g. 'Ideal Catch Range'. None → no in-plot label.
        x_start: Left edge of the band. None → full plot width
        x_end: Right edge of the band. None → full plot width
        color: Hex color. None → auto-assigned
        axis_id: Target axes identifier
        coach_tip: Short coaching cue for the legend table. Empty → blank cell.
    """

    label: str
    description: str
    y_low: float
    y_high: float
    display_name: str | None = None
    x_start: float | None = None
    x_end: float | None = None
    color: str | None = None
    axis_id: str = 'main'
    coach_tip: str = ''


@dataclass
class PhaseAnnotation:
    """Annotates a vertical phase region (e.g. Drive Phase) on the plot.

    Attributes:
        label: Short reference shown on the plot, e.g. '[Ph1]'
        description: Full explanation shown in the legend table
        x_start: Left edge of the phase region (data units)
        x_end: Right edge of the phase region (data units)
        color: Hex color. None → auto-assigned
        axis_id: Target axes identifier
        coach_tip: Short coaching cue for the legend table. Empty → blank cell.
    """

    label: str
    description: str
    x_start: float
    x_end: float
    color: str | None = None
    axis_id: str = 'main'
    coach_tip: str = ''


# Union type covering all annotation variants
AnnotationEntry = PointAnnotation | SegmentAnnotation | BandAnnotation | PhaseAnnotation


# ---------------------------------------------------------------------------
# AnnotationDefinition — metadata for pre-compute toggle UI (Phase 5)
# ---------------------------------------------------------------------------


@dataclass
class AnnotationDefinition:
    """Declares an annotation type that a PlotComponent can produce.

    Used by the page layer to render st.checkbox toggles *before* calling
    compute(), enabling expensive computations to be skipped when toggled off.

    Attributes:
        id: Must match the AnnotationEntry.label it describes, e.g. 'A1'
        name: Human-readable toggle label, e.g. 'Catch Lean Deviation'
        description: Help text shown next to the toggle
        default_on: Whether the annotation is enabled by default
    """

    id: str
    name: str
    description: str
    default_on: bool = True


# ---------------------------------------------------------------------------
# Color assignment utility
# ---------------------------------------------------------------------------


def assign_annotation_colors(
    annotations: Sequence[AnnotationEntry],
    palette: list[str] | None = None,
) -> list[AnnotationEntry]:
    """Auto-assign palette colors to annotations that have color=None.

    Annotations with an explicit color are left unchanged. Colors are assigned
    in palette order — first annotation without a color gets palette[0], etc.

    Args:
        annotations: List of AnnotationEntry objects from compute()
        palette: Color palette to draw from. Defaults to ANNOTATION_COLORS.

    Returns:
        New list with color fields filled in. Original objects are not mutated.
    """
    if palette is None:
        palette = ANNOTATION_COLORS

    color_iter = iter(palette)
    result: list[AnnotationEntry] = []
    for ann in annotations:
        if ann.color is None:
            color = next(color_iter, '#888888')
            ann = dataclasses.replace(ann, color=color)
        result.append(ann)
    return result


__all__ = [
    'ANNOTATION_COLORS',
    'AnnotationDefinition',
    'AnnotationEntry',
    'BandAnnotation',
    'PhaseAnnotation',
    'PointAnnotation',
    'SegmentAnnotation',
    'assign_annotation_colors',
]
