"""Avg Cycle Multi-Axis Events transform.

Transforms averaged cycle into multi-axis plot data (Seat, Handle, Shoulder) with catch/finish markers.
"""

from typing import Any, cast

import numpy as np
import pandas as pd

from rowing_catch.plot_transformer.base import PlotComponent


def _rescale_bounds(data: np.ndarray, pad: float = 0.15) -> tuple[float, float] | None:
    """Compute padded y-limits for a data array.

    Args:
        data: 1D array of values
        pad: Fractional padding to add

    Returns:
        (ymin, ymax) tuple or None if data contains only NaN
    """
    ymin, ymax = float(np.nanmin(data)), float(np.nanmax(data))
    if np.isnan(ymin) or np.isnan(ymax):
        return None
    diff = ymax - ymin
    r = diff * pad if diff > 0 else 1.0
    return ymin - r, ymax + r


class AvgCycleMultiAxisComponent(PlotComponent):
    """Averaged cycle multi-axis (Seat/Handle/Shoulder) component."""

    @property
    def name(self) -> str:
        return 'Averaged Cycle — Multi-Axis Events'

    @property
    def description(self) -> str:
        return 'Seat, Handle and Shoulder position on the averaged stroke with catch and finish markers'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute multi-axis averaged cycle plot data.

        Args:
            avg_cycle: Averaged cycle DataFrame (with _Smooth columns)
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Not used
            results: Not used

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        index = avg_cycle.index.tolist()
        seat = avg_cycle['Seat_X_Smooth'].to_numpy(dtype=float).tolist()
        handle = avg_cycle['Handle_X_Smooth'].to_numpy(dtype=float).tolist()

        has_shoulder = 'Shoulder_X_Smooth' in avg_cycle.columns
        shoulder = avg_cycle['Shoulder_X_Smooth'].to_numpy(dtype=float).tolist() if has_shoulder else []

        catch_seat_y = float(cast(Any, avg_cycle.loc[catch_idx, 'Seat_X_Smooth']))
        finish_seat_y = float(cast(Any, avg_cycle.loc[finish_idx, 'Seat_X_Smooth']))
        seat_min = float(avg_cycle['Seat_X_Smooth'].min())
        seat_max = float(avg_cycle['Seat_X_Smooth'].max())
        x_end = float(avg_cycle.index.max())

        seat_bounds = _rescale_bounds(np.array(seat))
        handle_bounds = _rescale_bounds(np.array(handle))
        shoulder_bounds = _rescale_bounds(np.array(shoulder)) if has_shoulder else None

        return {
            'data': {
                'index': index,
                'seat': seat,
                'handle': handle,
                'shoulder': shoulder,
                'has_shoulder': has_shoulder,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
                'catch_seat_y': catch_seat_y,
                'finish_seat_y': finish_seat_y,
                'seat_min': seat_min,
                'seat_max': seat_max,
                'x_end': x_end,
                'seat_bounds': seat_bounds,
                'handle_bounds': handle_bounds,
                'shoulder_bounds': shoulder_bounds,
                'n': len(avg_cycle),
            },
            'metadata': {
                'title': 'Averaged Cycle — Catch & Finish Events',
                'x_label': 'Cycle index (time)',
                'y_label': 'Seat X (mm)',
            },
            'coach_tip': (
                'The catch (green) is the forward seat position; the finish (red) is where the drive ends. '
                'All three trackers should invert direction smoothly at each event.'
            ),
        }
