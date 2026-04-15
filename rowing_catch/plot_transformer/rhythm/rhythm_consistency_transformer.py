"""Rhythm Consistency transform.

Shows SPM vs drive phase percentage consistency across cycles, with ideal curve.
This is the authoritative version (migrated from the debug pipeline).
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.algo.helpers import calculate_ideal_drive_rhythm
from rowing_catch.coaching.profile import CoachingProfile
from rowing_catch.plot_transformer.annotations import (
    AnnotationEntry,
    BandAnnotation,
    PhaseAnnotation,
    PointAnnotation,
    SegmentAnnotation,
)
from rowing_catch.plot_transformer.base import PlotComponent
from rowing_catch.plot_transformer.rhythm.drive_recovery_balance_transformer import compute_rhythm_spread
from rowing_catch.plot_transformer.rhythm.tip import (
    drive_pct_spread_coach_tip,
    drive_pct_vs_ideal_coach_tip,
    spm_spread_coach_tip,
)


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

        # Ideal drive% curve: SPM range derived from actual data with 10% padding
        if spm_vals.size > 0:
            spm_range = spm_vals.max() - spm_vals.min()
            spm_pad = spm_range * 0.50 if spm_range > 0 else 2.0
            min_spm = spm_vals.min() - spm_pad
            max_spm = spm_vals.max() + spm_pad
        else:
            min_spm, max_spm = 15.0, 45.0

        spm_curve = np.linspace(min_spm, max_spm, 100)
        offset = self.profile.rhythm_drive_pct_offset if self.profile is not None else 0.0
        ideal_drive_pct_curve = np.asarray(calculate_ideal_drive_rhythm(spm_curve), dtype=float) + offset

        # --- Annotations Calculation ---
        annotations: list[AnnotationEntry] = []
        if not np.isnan(mean_spm) and not np.isnan(mean_drive_pct):
            # 1. Ideal Drive % at current Mean SPM (with profile offset applied)
            ideal_pct_at_mean = float(calculate_ideal_drive_rhythm(mean_spm)) + offset

            # [P1] Performance Mean — tip delegates to pure function in tip/
            p1_tip, p1_ideal = drive_pct_vs_ideal_coach_tip(mean_drive_pct, ideal_pct_at_mean, mean_spm)
            annotations.append(
                PointAnnotation(
                    label='[P1]',
                    description=f'Mean Performance: {mean_spm:.1f} SPM @ {mean_drive_pct:.1f}% Drive',
                    x=mean_spm,
                    y=mean_drive_pct,
                    style='callout',
                    coach_tip=p1_tip,
                    coach_tip_is_ideal=p1_ideal,
                )
            )

            # [S1] Ideal Rhythm Reference (Segment Annotation — renamed from [I1] to match segment convention)
            annotations.append(
                SegmentAnnotation(
                    label='[S1]',
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

            # [Z1] + [Z2] Consistency spread — Band (Drive% ±1SD) + Phase (SPM ±1SD)
            if len(spm_vals) > 1:
                spm_std = float(np.std(spm_vals))
                drive_std = float(np.std(drive_pct_vals))

                z1_tip, z1_ideal = drive_pct_spread_coach_tip(drive_std)
                annotations.append(
                    BandAnnotation(
                        label='[Z1]',
                        description=f'Drive% spread (±{drive_std:.1f}%)',
                        y_low=mean_drive_pct - drive_std,
                        y_high=mean_drive_pct + drive_std,
                        display_name='[Z1]',
                        coach_tip=z1_tip,
                        coach_tip_is_ideal=z1_ideal,
                    )
                )

                z2_tip, z2_ideal = spm_spread_coach_tip(spm_std)
                annotations.append(
                    PhaseAnnotation(
                        label='[Z2]',
                        description=f'SPM spread (±{spm_std:.1f} SPM)',
                        x_start=mean_spm - spm_std,
                        x_end=mean_spm + spm_std,
                        coach_tip=z2_tip,
                        coach_tip_is_ideal=z2_ideal,
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
