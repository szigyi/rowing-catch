"""Production Finish Trajectory transform.

Shows full trajectory with production-heuristic finish markers for every cycle.
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.algo.steps.step5_metrics import _pick_finish_index
from rowing_catch.plot_transforms.base import PlotComponent


def compute_production_finish_indices(
    df_debug: pd.DataFrame,
    catch_indices: np.ndarray,
) -> np.ndarray:
    """Compute production finish indices for each cycle using the standard heuristic.

    Args:
        df_debug: Full-trajectory DataFrame with Trunk_Angle and Handle_X_Smooth
        catch_indices: Array of catch indices

    Returns:
        Array of production finish indices (one per cycle)
    """
    production_finish_indices = []
    for i in range(len(catch_indices) - 1):
        idx_start = int(catch_indices[i])
        idx_end = int(catch_indices[i + 1])
        cycle_slice = df_debug.iloc[idx_start:idx_end]
        rel_finish = _pick_finish_index(cycle_slice, catch_idx=0)
        production_finish_indices.append(idx_start + rel_finish)
    return np.array(production_finish_indices, dtype=int)


def compute_trunk_angle_full(df: pd.DataFrame) -> pd.Series:
    """Compute trunk angle for every row in a full-trajectory DataFrame.

    Assumes Shoulder_X_Smooth, Shoulder_Y_Smooth, Seat_X_Smooth, Seat_Y_Smooth exist.

    Args:
        df: Full-trajectory DataFrame after smoothing

    Returns:
        Series of trunk angles (degrees from vertical)
    """
    ref = df.iloc[0]
    is_facing_left = ref['Handle_X_Smooth'] < ref['Seat_X_Smooth']

    def _calc(row: pd.Series) -> float:
        dx = row['Shoulder_X_Smooth'] - row['Seat_X_Smooth']
        dy = row['Shoulder_Y_Smooth'] - row['Seat_Y_Smooth']
        dy_abs = abs(dy)
        return float(np.degrees(np.arctan2(dx if is_facing_left else -dx, dy_abs)))

    return df.apply(_calc, axis=1).astype(float)


class ProductionFinishTrajectoryComponent(PlotComponent):
    """Production-heuristic finish detection on the full trajectory."""

    @property
    def name(self) -> str:
        return 'Full Trajectory — Production Finish Detection'

    @property
    def description(self) -> str:
        return 'Full recording with catch and production-heuristic finish markers for every cycle'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute full-trajectory event plot data.

        Args:
            avg_cycle: Not used directly
            catch_idx: Not used
            finish_idx: Not used
            ghost_cycle: Not used
            results: Must contain 'df_smoothed' and 'catch_indices'

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        df_smooth: pd.DataFrame | None = results.get('df_smoothed') if results else None
        catch_indices: np.ndarray = results.get('catch_indices', np.array([], dtype=int)) if results else np.array([], dtype=int)

        if df_smooth is None or len(catch_indices) < 2:
            return {
                'data': {
                    'index': [],
                    'seat_smooth': [],
                    'catch_indices': [],
                    'catch_values': [],
                    'finish_indices': [],
                    'finish_values': [],
                },
                'metadata': {
                    'title': 'Full Trajectory: Seat_X_Smooth with Detected Events',
                    'x_label': 'Sample index',
                    'y_label': 'Seat_X (mm)',
                },
                'coach_tip': 'Insufficient data to display full trajectory.',
            }

        df_debug = df_smooth.copy()

        has_shoulder = all(c in df_debug.columns for c in ['Shoulder_X_Smooth', 'Shoulder_Y_Smooth', 'Seat_Y_Smooth'])
        if has_shoulder:
            df_debug['Trunk_Angle'] = compute_trunk_angle_full(df_debug)

        finish_indices = compute_production_finish_indices(df_debug, catch_indices)

        seat = df_debug['Seat_X_Smooth']
        catch_values = seat.iloc[catch_indices].to_numpy(dtype=float).tolist()
        finish_values = seat.iloc[finish_indices].to_numpy(dtype=float).tolist()

        return {
            'data': {
                'index': df_debug.index.tolist(),
                'seat_smooth': seat.to_numpy(dtype=float).tolist(),
                'catch_indices': catch_indices.tolist(),
                'catch_values': catch_values,
                'finish_indices': finish_indices.tolist(),
                'finish_values': finish_values,
            },
            'metadata': {
                'title': 'Full Trajectory: Seat_X_Smooth with Detected Events',
                'x_label': 'Sample index',
                'y_label': 'Seat_X (mm)',
            },
            'coach_tip': (
                'The finish marker (red X) shows where the production heuristic places the end of the drive. '
                'It should sit consistently near the handle velocity reversal point.'
            ),
        }
