"""Centralized theme and styling constants for all plots."""

from rowing_catch.plot_transformer.annotations import (
    ANNOTATION_COLORS,
    ANNOTATION_COLORS_POINT,
    ANNOTATION_COLORS_REGION,
    ANNOTATION_COLORS_SEGMENT,
    ANNOTATION_COLORS_ZONE,
)

# --- Annotation Colors ---
# The palettes live in plot_transformer/annotations.py (Layer 2) so transformers
# can use them without importing from plot/. Re-exported here for convenience.
ANNOTATION_LABEL_BG = '#FFFFFF'  # White badge background

# --- Main line palette (multi-series plots) ---
# Ordered list for renderers that draw multiple named series on one axes.
# Usage: zip(series_list, MAIN_COLORS)
# Colours chosen to be mutually distinct and clear of COLOR_CATCH / COLOR_FINISH.
MAIN_COLORS: list[str] = [
    '#636EFA',  # 1. Blue-purple  — primary / handle velocity
    '#F59E0B',  # 2. Amber        — secondary / seat velocity
    '#8B5CF6',  # 3. Violet       — tertiary / shoulder / arms
    '#06B6D4',  # 4. Cyan         — quaternary / composite / rower velocity
]

# --- Semantic single-line colors ---
COLOR_MAIN = '#636EFA'  # Blue-purple (primary) — single main line for all plots
COLOR_LEGS = '#636EFA'  # Kinetic chain: legs (alias of main)
COLOR_TRUNK = '#636EFA'  # Was #EF553B — unified to main
COLOR_ARMS = '#8B5CF6'  # Kinetic chain: arms — violet, distinct from main and catch
COLOR_HANDLE = '#636EFA'  # Was #AB63FA — unified to main
COLOR_SEAT = '#636EFA'  # Was #FFA15A — unified to main
COLOR_CATCH = '#00CC96'  # Green — catch event marker
COLOR_FINISH = '#EF553B'  # Red   — finish event marker
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

__all__ = [
    'ANNOTATION_COLORS',
    'ANNOTATION_COLORS_POINT',
    'ANNOTATION_COLORS_SEGMENT',
    'ANNOTATION_COLORS_ZONE',
    'ANNOTATION_COLORS_REGION',
    'ANNOTATION_LABEL_BG',
    'MAIN_COLORS',
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
