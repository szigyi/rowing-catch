"""Consistency & Rhythm plot transform.

Transforms analysis results into data ready for rendering rhythm metrics.
"""

from typing import Any

import pandas as pd

from rowing_catch.plot_transforms.base import PlotComponent


class ConsistencyRhythmComponent(PlotComponent):
    """Consistency and rhythm metrics component."""

    @property
    def name(self) -> str:
        return 'Consistency & Rhythm'

    @property
    def description(self) -> str:
        return 'Stroke variability and drive/recovery proportion'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute consistency and rhythm plot data.

        Extracts coefficient of variation and drive/recovery percentages
        from results dict.
        """
        if results is None:
            results = {}

        # Extract metrics from results
        cv_length = results.get('cv_length', 0.0)
        drive_len = results.get('drive_len', 0)
        recovery_len = results.get('recovery_len', 0)

        # Calculate proportions
        total = drive_len + recovery_len
        drive_p = (drive_len / total * 100) if total > 0 else 50
        rec_p = (recovery_len / total * 100) if total > 0 else 50

        return {
            'data': {
                'cv': cv_length,
                'drive_percent': drive_p,
                'recovery_percent': rec_p,
            },
            'metadata': {
                'title': 'Consistency & Rhythm',
            },
            'coach_tip': (
                f'{"You are rushing the recovery." if drive_p > 35 else "Good rhythm."} '
                'Slower movement on the slide (recovery) allows your muscles to recover.'
            ),
        }


__all__ = ['ConsistencyRhythmComponent']
