"""Rhythm Consistency transform.

Shows SPM vs drive phase percentage consistency across cycles, with ideal curve.
This is the authoritative version (migrated from the debug pipeline).
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.algo.helpers import calculate_ideal_drive_ratio
from rowing_catch.coaching.profile import CoachingProfile
from rowing_catch.plot_transformer.annotations import AnnotationEntry, BandAnnotation, PointAnnotation, SegmentAnnotation
from rowing_catch.plot_transformer.base import PlotComponent
from rowing_catch.plot_transformer.rhythm.drive_recovery_balance_transformer import compute_rhythm_spread


class RhythmConsistencyComponent(PlotComponent):
    """Rhythm consistency (SPM vs drive%) component."""

    def __init__(self, profile: CoachingProfile | None = None):
        """Initialize with optional coaching profile.

        Args:
            profile: Contains thresholds for SPM range and ideal rhythm.
        """
        self.profile = profile

    @property
    def name(self) -> str:
        return 'Rhythm Consistency'

    @property
    def description(self) -> str:
        return 'SPM and drive phase % consistency across cycles with biomechanical ideal curve'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute rhythm consistency plot data.

        Args:
            avg_cycle: DataFrame with rowing stroke data (not used directly)
            catch_idx: Index of catch (not used)
            finish_idx: Index of finish (not used)
            ghost_cycle: Not used
            results: Must contain 'cycles' (list of per-stroke DataFrames)

        Returns:
            Dict with 'data', 'metadata', 'coach_tip' keys
        """
        cycles: list[pd.DataFrame] = results.get('cycles', []) if results else []
        cycle_data = compute_rhythm_spread(cycles)

        df = pd.DataFrame(cycle_data) if cycle_data else pd.DataFrame()

        if not df.empty:
            spm_vals = df['SPM'].to_numpy(dtype=float)
            drive_pct_vals = df['Drive_Pct'].to_numpy(dtype=float)
            mean_spm = float(np.nanmean(spm_vals))
            mean_drive_pct = float(np.nanmean(drive_pct_vals))
        else:
            spm_vals = np.array([], dtype=float)
            drive_pct_vals = np.array([], dtype=float)
            mean_spm = float('nan')
            mean_drive_pct = float('nan')

        # Ideal drive% curve: configurable SPM range from profile
        min_spm = self.profile.rhythm_spm_min if self.profile else 15.0
        max_spm = self.profile.rhythm_spm_max if self.profile else 45.0

        spm_curve = np.linspace(min_spm, max_spm, 100)
        ideal_ratios = np.asarray(calculate_ideal_drive_ratio(spm_curve), dtype=float)
        ideal_drive_pct_curve = ideal_ratios / (1.0 + ideal_ratios) * 100

        # --- Annotations Calculation ---
        annotations: list[AnnotationEntry] = []
        if not np.isnan(mean_spm) and not np.isnan(mean_drive_pct):
            # 1. Ideal Drive % at current Mean SPM
            ideal_ratio_at_mean = float(calculate_ideal_drive_ratio(np.array([mean_spm]))[0])
            ideal_pct_at_mean = (ideal_ratio_at_mean / (1.0 + ideal_ratio_at_mean)) * 100
            diff_pct = mean_drive_pct - ideal_pct_at_mean

            # [P1] Performance Mean
            annotations.append(
                PointAnnotation(
                    label='[P1]',
                    description=f'Mean Performance: {mean_spm:.1f} SPM @ {mean_drive_pct:.1f}% Drive',
                    x=mean_spm,
                    y=mean_drive_pct,
                    style='callout',
                    coach_tip=(
                        f'Your mean drive % is {abs(diff_pct):.1f}% {"above" if diff_pct > 0 else "below"} '
                        f'the elite benchmark ({ideal_pct_at_mean:.1f}%) for this stroke rate.'
                    ),
                )
            )

            # [I1] Ideal Rhythm Reference (Segment Annotation replaces the old Band)
            annotations.append(
                SegmentAnnotation(
                    label='[I1]',
                    description='Ideal Rhythm',
                    x_start=float(spm_curve[0]),
                    x_end=float(spm_curve[-1]),
                    x=spm_curve.tolist(),
                    y=ideal_drive_pct_curve.tolist(),
                    style='glow',
                    coach_tip=(
                        'Elite rowers adapt their drive ratio as SPM increases. If your strokes do not '
                        "follow this arch, you aren't adapting your technique to the rhythm."
                    ),
                )
            )

            # [Z1] Consistency & Spread
            if len(spm_vals) > 1:
                spm_std = float(np.std(spm_vals))
                drive_std = float(np.std(drive_pct_vals))

                annotations.append(
                    BandAnnotation(
                        label='[Z1]',
                        description='Consistency Spread (±1 SD)',
                        y_low=mean_drive_pct - drive_std,
                        y_high=mean_drive_pct + drive_std,
                        x_start=mean_spm - spm_std,
                        x_end=mean_spm + spm_std,
                        coach_tip=(
                            f'Vertical spread ({drive_std:.1f}%) indicates the rhythm '
                            '(drive/recovery balance) is changing a lot. '
                            f'Horizontal spread ({spm_std:.1f} SPM) shows inconsistency '
                            'keeping the same SPM during the piece.'
                        ),
                    )
                )

        return {
            'data': {
                'spm_vals': spm_vals.tolist(),
                'drive_pct_vals': drive_pct_vals.tolist(),
                'mean_spm': mean_spm,
                'mean_drive_pct': mean_drive_pct,
                'ideal_curve_spm': spm_curve.tolist(),
                'ideal_curve_drive_pct': ideal_drive_pct_curve.tolist(),
                'has_data': len(cycle_data) > 0,
                'dataframe': df,
            },
            'metadata': {
                'title': 'Stroke-by-Stroke Rhythm Consistency',
                'x_label': 'Strokes Per Minute (SPM)',
                'y_label': 'Drive Phase (% of stroke)',
            },
            'coach_tip': (
                'Elite rowers maintain a tight cluster near the ideal curve. '
                'A vertical spread means inconsistent drive % at the same stroke rate. '
                'A horizontal spread means the stroke rate changes too much stroke-to-stroke.'
            ),
            'annotations': annotations,
        }
