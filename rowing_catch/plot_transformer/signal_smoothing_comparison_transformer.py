"""Signal Smoothing Comparison transform.

Transforms raw vs smoothed signal data ready for rendering side-by-side comparison plots.
"""

from typing import Any

import pandas as pd

from rowing_catch.plot_transformer.base import PlotComponent


class SignalSmoothingComparisonComponent(PlotComponent):
    """Signal smoothing comparison visualization component."""

    @property
    def name(self) -> str:
        return 'Signal Smoothing Comparison'

    @property
    def description(self) -> str:
        return 'Before/after smoothing comparison for Seat_X and Handle_X signals'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute smoothing comparison data.

        Args:
            avg_cycle: DataFrame with rowing stroke data (not used directly)
            catch_idx: Index of catch (not used)
            finish_idx: Index of finish (not used)
            ghost_cycle: Not used
            results: Results dict; must contain 'df_raw_step1' and 'df_smoothed'

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        df_raw = results.get('df_raw_step1') if results else None
        df_smooth = results.get('df_smoothed') if results else None

        seat_raw = df_raw['Seat_X'].to_numpy(dtype=float) if df_raw is not None and 'Seat_X' in df_raw.columns else []
        seat_smooth = (
            df_smooth['Seat_X_Smooth'].to_numpy(dtype=float)
            if df_smooth is not None and 'Seat_X_Smooth' in df_smooth.columns
            else []
        )
        handle_raw = df_raw['Handle_X'].to_numpy(dtype=float) if df_raw is not None and 'Handle_X' in df_raw.columns else []
        handle_smooth = (
            df_smooth['Handle_X_Smooth'].to_numpy(dtype=float)
            if df_smooth is not None and 'Handle_X_Smooth' in df_smooth.columns
            else []
        )

        index_raw = list(df_raw.index) if df_raw is not None else []
        index_smooth = list(df_smooth.index) if df_smooth is not None else []

        return {
            'data': {
                'index_raw': index_raw,
                'index_smooth': index_smooth,
                'seat_raw': list(seat_raw),
                'seat_smooth': list(seat_smooth),
                'handle_raw': list(handle_raw),
                'handle_smooth': list(handle_smooth),
            },
            'metadata': {
                'title': 'Signal Smoothing Comparison',
                'x_label': 'Sample index',
                'y_label': 'Position (mm)',
            },
            'coach_tip': (
                'Smoothing removes high-frequency sensor noise. '
                'The smoothed signal should follow the raw signal closely without losing stroke shape.'
            ),
        }
