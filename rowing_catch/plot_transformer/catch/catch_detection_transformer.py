"""Catch Detection transform.

Transforms smoothed seat signal and catch indices into data ready for rendering.
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.plot_transformer.base import PlotComponent


class CatchDetectionComponent(PlotComponent):
    """Catch detection visualization component."""

    @property
    def name(self) -> str:
        return 'Catch Detection'

    @property
    def description(self) -> str:
        return 'Seat_X smoothed signal with detected catch positions overlaid'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute catch detection plot data.

        Args:
            avg_cycle: DataFrame with rowing stroke data (not used directly)
            catch_idx: Index of catch (not used here — full-trajectory catches used)
            finish_idx: Index of finish (not used)
            ghost_cycle: Not used
            results: Must contain 'df_smoothed' and 'catch_indices'

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        df = results.get('df_smoothed') if results else None
        catch_indices: np.ndarray = results.get('catch_indices', np.array([], dtype=int)) if results else np.array([], dtype=int)

        index = list(df.index) if df is not None else []
        seat_smooth = (
            df['Seat_X_Smooth'].to_numpy(dtype=float).tolist() if df is not None and 'Seat_X_Smooth' in df.columns else []
        )
        catch_idx_list = catch_indices.tolist() if hasattr(catch_indices, 'tolist') else list(catch_indices)
        catch_values = (
            df['Seat_X_Smooth'].iloc[catch_indices].to_numpy(dtype=float).tolist()
            if df is not None and 'Seat_X_Smooth' in df.columns and len(catch_indices) > 0
            else []
        )

        intervals: list[dict[str, Any]] = []
        if len(catch_indices) > 1:
            for i in range(len(catch_indices) - 1):
                intervals.append(
                    {
                        'catch_num': i + 1,
                        'start': int(catch_indices[i]),
                        'end': int(catch_indices[i + 1]),
                        'interval': int(catch_indices[i + 1] - catch_indices[i]),
                    }
                )

        return {
            'data': {
                'index': index,
                'seat_smooth': seat_smooth,
                'catch_indices': catch_idx_list,
                'catch_values': catch_values,
                'intervals': intervals,
            },
            'metadata': {
                'title': 'Seat_X_Smooth — local minima = catches (one per stroke)',
                'x_label': 'Sample index',
                'y_label': 'Seat_X_Smooth',
            },
            'coach_tip': (
                'Each green dot marks a detected catch. '
                'Catches should be evenly spaced — large variation indicates inconsistent stroke timing.'
            ),
        }
