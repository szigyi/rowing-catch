"""Centralized theme and styling constants for all plots."""

# --- Annotation Colors ---
# A palette distinct from the main data colors, used for annotation overlays.
# Assigned automatically by apply_annotations() when color=None on an annotation.
ANNOTATION_COLOR_1 = '#F59E0B'  # Amber
ANNOTATION_COLOR_2 = '#10B981'  # Emerald
ANNOTATION_COLOR_3 = '#D946EF'  # Fuchsia (replaces Indigo #6366F1 — too close to COLOR_MAIN #636EFA)
ANNOTATION_COLOR_4 = '#EC4899'  # Pink
ANNOTATION_COLOR_5 = '#14B8A6'  # Teal
ANNOTATION_LABEL_BG = '#FFFFFF'  # White badge background

# --- Colors ---
COLOR_MAIN = '#636EFA'  # Blue-purple (primary)
COLOR_LEGS = '#636EFA'
COLOR_TRUNK = '#EF553B'
COLOR_ARMS = '#00CC96'
COLOR_HANDLE = '#AB63FA'
COLOR_SEAT = '#FFA15A'  # Orange
COLOR_CATCH = '#00CC96'  # Green
COLOR_FINISH = '#EF553B'  # Red
COLOR_COMPARE = '#A8B2C1'  # Gray (Ideal/Compare/Ghost)
COLOR_IDEAL_RATIO = '#FDB833'  # Gold — biomechanically ideal ratio
COLOR_TEXT_MAIN = '#444444'
COLOR_TEXT_SUB = '#666666'

# --- Background Colors ---
BG_COLOR_FIGURE = '#F8F9FA'  # Light gray
BG_COLOR_AXES = '#FFFFFF'  # White

# --- Spine/Line Colors ---
SPINE_COLOR = '#DDDDDD'
GRID_COLOR = '#F0F0F0'
REFERENCE_LINE_COLOR = '#888888'

# --- Zone Colors (Semi-transparent) ---
CATCH_ZONE_ALPHA = 0.08
FINISH_ZONE_ALPHA = 0.08

# Export commonly used sets
__all__ = [
    'ANNOTATION_COLOR_1',
    'ANNOTATION_COLOR_2',
    'ANNOTATION_COLOR_3',
    'ANNOTATION_COLOR_4',
    'ANNOTATION_COLOR_5',
    'ANNOTATION_LABEL_BG',
    'COLOR_MAIN',
    'COLOR_LEGS',
    'COLOR_TRUNK',
    'COLOR_ARMS',
    'COLOR_HANDLE',
    'COLOR_SEAT',
    'COLOR_CATCH',
    'COLOR_FINISH',
    'COLOR_COMPARE',
    'COLOR_IDEAL_RATIO',
    'COLOR_TEXT_MAIN',
    'COLOR_TEXT_SUB',
    'BG_COLOR_FIGURE',
    'BG_COLOR_AXES',
    'SPINE_COLOR',
    'GRID_COLOR',
    'REFERENCE_LINE_COLOR',
    'CATCH_ZONE_ALPHA',
    'FINISH_ZONE_ALPHA',
]
