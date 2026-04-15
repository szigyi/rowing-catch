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
# Annotation palettes — one per annotation geometry type.
# Each type starts its own counter independently per plot, so [P1] and [S1]
# never compete for the same palette slot.
# All colours are chosen to contrast against COLOR_MAIN (#636EFA blue-purple),
# COLOR_CATCH (#00CC96 green), and COLOR_FINISH (#EF553B red).
# ---------------------------------------------------------------------------

# Points ([P_]) — callout dots + arrows. Pop clearly off the main line.
# In practice [P1]/[P2] are often overridden by COLOR_CATCH/COLOR_FINISH.
ANNOTATION_COLORS_POINT: list[str] = [
    '#D946EF',  # Fuchsia  — [P1]
    '#14B8A6',  # Teal     — [P2]
]

# Segments ([S_]) — wide semi-transparent backdrops on the main line.
# Warm/violet tones contrast against the blue-purple main line.
ANNOTATION_COLORS_SEGMENT: list[str] = [
    '#F59E0B',  # Amber  — [S1] drive phase
    '#8B5CF6',  # Violet — [S2] recovery phase (distinct from amber)
]

# Zones ([Z_]) — horizontal shaded bands (ideal range target zones).
# Usually overridden by COLOR_CATCH/COLOR_FINISH in renderers.
ANNOTATION_COLORS_ZONE: list[str] = [
    '#10B981',  # Emerald — [Z1] (overridden by catch green in practice)
    '#EC4899',  # Pink    — [Z2] (overridden by finish red in practice)
]

# Regions ([R_]) — vertical phase spans. Intentionally subtle.
ANNOTATION_COLORS_REGION: list[str] = [
    '#94A3B8',  # Slate grey — [R1]
]

# Legacy flat list kept for backward compatibility with code that imports it.
# New code should prefer the typed palettes above.
ANNOTATION_COLORS: list[str] = (
    ANNOTATION_COLORS_POINT + ANNOTATION_COLORS_SEGMENT + ANNOTATION_COLORS_ZONE + ANNOTATION_COLORS_REGION
)


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
    coach_tip_is_ideal: bool = True


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
    coach_tip_is_ideal: bool = True


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
    coach_tip_is_ideal: bool = True


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
    coach_tip_is_ideal: bool = True


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

    When ``palette`` is None (the default), each annotation type draws from its
    own typed palette so the counters are independent:
      - PointAnnotation    → ANNOTATION_COLORS_POINT
      - SegmentAnnotation  → ANNOTATION_COLORS_SEGMENT
      - BandAnnotation     → ANNOTATION_COLORS_ZONE
      - PhaseAnnotation    → ANNOTATION_COLORS_REGION

    This ensures [P1] and [S1] never share a slot — a segment backdrop colour
    is always visually distinct from the point callout colour on the same plot.

    When a custom ``palette`` list is supplied the old behaviour is preserved:
    all types share that single list and draw from it in order.

    Annotations with an explicit color are always left unchanged.

    Args:
        annotations: List of AnnotationEntry objects from compute()
        palette: Override palette. When None, typed palettes are used.

    Returns:
        New list with color fields filled in. Original objects are not mutated.
    """
    if palette is not None:
        # Legacy / override path: single shared palette
        color_iter = iter(palette)
        result: list[AnnotationEntry] = []
        for ann in annotations:
            if ann.color is None:
                color = next(color_iter, '#888888')
                ann = dataclasses.replace(ann, color=color)
            result.append(ann)
        return result

    # Typed palette path: independent counter per annotation geometry type.
    point_iter = iter(ANNOTATION_COLORS_POINT)
    segment_iter = iter(ANNOTATION_COLORS_SEGMENT)
    zone_iter = iter(ANNOTATION_COLORS_ZONE)
    region_iter = iter(ANNOTATION_COLORS_REGION)

    result = []
    for ann in annotations:
        if ann.color is not None:
            result.append(ann)
            continue
        if isinstance(ann, PointAnnotation):
            color = next(point_iter, '#888888')
        elif isinstance(ann, SegmentAnnotation):
            color = next(segment_iter, '#888888')
        elif isinstance(ann, BandAnnotation):
            color = next(zone_iter, '#888888')
        else:  # PhaseAnnotation
            color = next(region_iter, '#888888')
        result.append(dataclasses.replace(ann, color=color))
    return result


__all__ = [
    'ANNOTATION_COLORS',
    'ANNOTATION_COLORS_POINT',
    'ANNOTATION_COLORS_SEGMENT',
    'ANNOTATION_COLORS_ZONE',
    'ANNOTATION_COLORS_REGION',
    'AnnotationDefinition',
    'AnnotationEntry',
    'BandAnnotation',
    'PhaseAnnotation',
    'PointAnnotation',
    'SegmentAnnotation',
    'assign_annotation_colors',
]
