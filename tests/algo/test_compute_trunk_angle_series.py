"""Tests for compute_trunk_angle_series in algo.helpers.

This function is the single source of truth for trunk angle geometry —
used by both the analysis pipeline (step5_metrics) and per-cycle overlay
computation (plot_transformer/trunk/cycle_utils).
"""

import numpy as np
import pandas as pd

from rowing_catch.algo.helpers import compute_trunk_angle_series


def _make_df(shoulder_x, shoulder_y, seat_x, seat_y):
    """Build a minimal DataFrame with the four required smooth columns."""
    return pd.DataFrame(
        {
            'Shoulder_X_Smooth': np.asarray(shoulder_x, dtype=float),
            'Shoulder_Y_Smooth': np.asarray(shoulder_y, dtype=float),
            'Seat_X_Smooth': np.asarray(seat_x, dtype=float),
            'Seat_Y_Smooth': np.asarray(seat_y, dtype=float),
        }
    )


# ---------------------------------------------------------------------------
# Upright rower (trunk vertical)
# ---------------------------------------------------------------------------


def test_upright_rower_returns_zero():
    """When shoulder is directly above seat, trunk angle is 0°."""
    df = _make_df(
        shoulder_x=[100],
        shoulder_y=[500],
        seat_x=[100],  # same X → dx = 0
        seat_y=[100],
    )
    result = compute_trunk_angle_series(df, is_facing_left=True)
    assert np.isclose(result.iloc[0], 0.0)


# ---------------------------------------------------------------------------
# Left-facing rower
# ---------------------------------------------------------------------------


def test_left_facing_forward_lean_is_negative():
    """Left-facing rower leaning forward: shoulder moves left (lower X), angle < 0."""
    # dx = shoulder_x - seat_x = 90 - 100 = -10 → lean forward → negative angle
    df = _make_df(
        shoulder_x=[90],
        shoulder_y=[500],
        seat_x=[100],
        seat_y=[100],
    )
    result = compute_trunk_angle_series(df, is_facing_left=True)
    assert result.iloc[0] < 0


def test_left_facing_layback_is_positive():
    """Left-facing rower leaning back: shoulder moves right (higher X), angle > 0."""
    df = _make_df(
        shoulder_x=[110],
        shoulder_y=[500],
        seat_x=[100],
        seat_y=[100],
    )
    result = compute_trunk_angle_series(df, is_facing_left=True)
    assert result.iloc[0] > 0


def test_left_facing_exact_angle():
    """Left-facing: angle = arctan2(dx, dy_abs) in degrees."""
    dx, dy_abs = 50.0, 400.0
    df = _make_df(
        shoulder_x=[100 + dx],
        shoulder_y=[500],
        seat_x=[100],
        seat_y=[100],
    )
    expected = np.degrees(np.arctan2(dx, dy_abs))
    result = compute_trunk_angle_series(df, is_facing_left=True)
    assert np.isclose(result.iloc[0], expected)


# ---------------------------------------------------------------------------
# Right-facing rower (sign flips)
# ---------------------------------------------------------------------------


def test_right_facing_exact_angle():
    """Right-facing: angle = arctan2(-dx, dy_abs) in degrees."""
    dx, dy_abs = 50.0, 400.0
    df = _make_df(
        shoulder_x=[100 + dx],
        shoulder_y=[500],
        seat_x=[100],
        seat_y=[100],
    )
    expected = np.degrees(np.arctan2(-dx, dy_abs))
    result = compute_trunk_angle_series(df, is_facing_left=False)
    assert np.isclose(result.iloc[0], expected)


def test_right_facing_forward_lean_is_negative():
    """Right-facing rower leaning forward: shoulder moves right (higher X), angle < 0."""
    df = _make_df(
        shoulder_x=[110],
        shoulder_y=[500],
        seat_x=[100],
        seat_y=[100],
    )
    result = compute_trunk_angle_series(df, is_facing_left=False)
    assert result.iloc[0] < 0


# ---------------------------------------------------------------------------
# Symmetry: facing direction flips sign
# ---------------------------------------------------------------------------


def test_left_and_right_are_sign_flipped():
    """For the same posture, left-facing and right-facing angles are equal and opposite."""
    df = _make_df(
        shoulder_x=[150],
        shoulder_y=[600],
        seat_x=[100],
        seat_y=[100],
    )
    angle_left = compute_trunk_angle_series(df, is_facing_left=True).iloc[0]
    angle_right = compute_trunk_angle_series(df, is_facing_left=False).iloc[0]
    assert np.isclose(angle_left, -angle_right)


# ---------------------------------------------------------------------------
# Multi-row DataFrame
# ---------------------------------------------------------------------------


def test_multi_row_shape_and_index():
    """Returns a Series with the same length and index as the input DataFrame."""
    n = 10
    df = _make_df(
        shoulder_x=np.linspace(90, 110, n),
        shoulder_y=np.full(n, 500),
        seat_x=np.full(n, 100),
        seat_y=np.full(n, 100),
    )
    result = compute_trunk_angle_series(df, is_facing_left=True)
    assert len(result) == n
    assert list(result.index) == list(df.index)


def test_multi_row_values_match_elementwise():
    """Each row result matches individually computed expected angle."""
    dxs = [20.0, 0.0, -30.0]
    dy_abs = 400.0
    df = _make_df(
        shoulder_x=[100 + dx for dx in dxs],
        shoulder_y=[500, 500, 500],
        seat_x=[100, 100, 100],
        seat_y=[100, 100, 100],
    )
    result = compute_trunk_angle_series(df, is_facing_left=True)
    for i, dx in enumerate(dxs):
        expected = np.degrees(np.arctan2(dx, dy_abs))
        assert np.isclose(result.iloc[i], expected), f'Row {i}: {result.iloc[i]} != {expected}'


# ---------------------------------------------------------------------------
# dy = 0 edge case (degenerate: shoulder at same height as seat)
# ---------------------------------------------------------------------------


def test_zero_dy_does_not_raise():
    """When shoulder and seat are at the same height, result is ±90° (not an error)."""
    df = _make_df(
        shoulder_x=[120],
        shoulder_y=[100],  # same Y as seat
        seat_x=[100],
        seat_y=[100],
    )
    result = compute_trunk_angle_series(df, is_facing_left=True)
    assert np.isclose(abs(result.iloc[0]), 90.0)
