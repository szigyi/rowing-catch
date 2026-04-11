"""Centralized theme and styling constants for all plots."""

from rowing_catch.plot_transformer.annotations import ANNOTATION_COLORS

# --- Annotation Colors ---
# The palette lives in plot_transformer/annotations.py (Layer 2) so transformers
# can use it without importing from plot/. Re-exported here for reference.
# Individual slot meanings (matched to annotation return order):
#   slot 1 → [P_] points   slot 3 → [S_] segments   slot 5 → [Z_] zones
#   slot 2 → [P_] points   slot 4 → [S_] segments   slot 6 → [Z_] zones
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
    'ANNOTATION_COLORS',
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
