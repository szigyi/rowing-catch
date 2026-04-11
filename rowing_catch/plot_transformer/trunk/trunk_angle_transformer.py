"""Trunk Angle plot transform.

Transforms analysis results into data ready for rendering trunk angle with
anatomical stick figures at key stages.
"""

from typing import Any, cast

import numpy as np
import pandas as pd

from rowing_catch.plot_transformer.annotations import (
    BandAnnotation,
    PointAnnotation,
    SegmentAnnotation,
)
from rowing_catch.plot_transformer.base import PlotComponent
from rowing_catch.plot_transformer.trunk.tip import (
    catch_lean_coach_tip,
    drive_trunk_opening_coach_tip,
    finish_lean_coach_tip,
    recovery_rock_over_coach_tip,
)

# Backward-compatible underscore aliases (used by existing tests and imports)
_catch_lean_coach_tip = catch_lean_coach_tip
_finish_lean_coach_tip = finish_lean_coach_tip
_drive_trunk_opening_coach_tip = drive_trunk_opening_coach_tip
_recovery_rock_over_coach_tip = recovery_rock_over_coach_tip


class TrunkAngleComponent(PlotComponent):
    """Trunk angle with anatomical stick figures at stroke stages."""

    # Ideal target zones (degrees from vertical)
    IDEAL_CATCH_ZONE: tuple[float, float] = (-33.0, -27.0)
    IDEAL_FINISH_ZONE: tuple[float, float] = (12.0, 18.0)

    @property
    def name(self) -> str:
        return 'Trunk Angle & Range'

    @property
    def description(self) -> str:
        return 'Trunk angle progression with anatomical stick figures'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute trunk angle plot data including stage points and ideal zones.

        Calculates stage progression, ideal zones, and prepares data for
        stick figure rendering.

        Annotations produced:
            [P1] Catch Lean — trunk angle at catch vs. ideal zone
            [P2] Finish Lean — trunk angle at finish vs. ideal zone
            [S1] Drive Segment — the drive phase on the trunk angle line (backdrop)
            [S2] Recovery Segment — finish to next catch rock-over (backdrop)
            [Z1] Ideal Catch Zone — target catch angle band
            [Z2] Ideal Finish Zone — target finish angle band
        """
        x = avg_cycle.index.to_numpy()

        # Calculate stage points
        drive_len = max(1, int(finish_idx) - int(catch_idx))
        rec_end = int(x.max())
        rec_len = max(1, rec_end - int(finish_idx))

        stage_points = [
            ('Catch', int(catch_idx)),
            ('3/4 Slide', int(catch_idx + 0.25 * drive_len)),
            ('1/2 Slide', int(catch_idx + 0.50 * drive_len)),
            ('1/4 Slide', int(catch_idx + 0.75 * drive_len)),
            ('Finish', int(finish_idx)),
            ('1/4 Slide', int(finish_idx + 0.25 * rec_len)),
            ('1/2 Slide', int(finish_idx + 0.50 * rec_len)),
            ('3/4 Slide', int(finish_idx + 0.75 * rec_len)),
            ('Next Catch', rec_end),
        ]

        x_min = int(x.min())
        x_max = int(x.max())
        stage_points = [(label, int(np.clip(ix, x_min, x_max))) for label, ix in stage_points]

        # Ideal zones
        catch_zone = self.IDEAL_CATCH_ZONE
        finish_zone = self.IDEAL_FINISH_ZONE

        # Extract angles at stage points for stick figures
        stage_angles = []
        for label, ix in stage_points:
            try:
                angle = float(cast(float, avg_cycle.at[ix, 'Trunk_Angle']))
            except Exception:
                nearest = int(np.argmin(np.abs(x - ix)))
                angle = float(avg_cycle['Trunk_Angle'].iloc[nearest])
            stage_angles.append((label, ix, angle))

        # Ghost cycle data if provided
        ghost_data = None
        if ghost_cycle is not None:
            ghost_data = {
                'trunk_angle_plot': ghost_cycle['Trunk_Angle'].values,
                'x': ghost_cycle.index.values,
            }

        catch_lean = float(cast(float, avg_cycle.at[catch_idx, 'Trunk_Angle']))
        finish_lean = float(cast(float, avg_cycle.at[finish_idx, 'Trunk_Angle']))
        drive_range = abs(finish_lean - catch_lean)

        # --- Compute annotations ---
        annotations = _compute_trunk_annotations(
            x=x,
            trunk_angle=avg_cycle['Trunk_Angle'].values,
            catch_idx=catch_idx,
            finish_idx=finish_idx,
            x_max_idx=x_max,
            catch_lean=catch_lean,
            finish_lean=finish_lean,
            catch_zone=catch_zone,
            finish_zone=finish_zone,
            x_min=float(x_min),
            x_max=float(x_max),
        )

        return {
            'data': {
                'trunk_angle_plot': avg_cycle['Trunk_Angle'].values,
                'x': avg_cycle.index.values,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
                'x_max': x_max,
                'x_min': x_min,
                'stage_points': stage_points,
                'stage_angles': stage_angles,
                'catch_zone': catch_zone,
                'finish_zone': finish_zone,
                'catch_lean': catch_lean,
                'finish_lean': finish_lean,
            },
            'ghost_data': ghost_data,
            'metadata': {
                'title': 'Trunk Angle & Range Analysis',
                'x_label': 'Stroke Timeline (Data Points)',
                'y_label': 'Degrees from Vertical',
            },
            'coach_tip': (
                f'You are achieving {drive_range:.1f}° of range. '
                f'Catch lean: {catch_lean:.1f}°, Finish lean: {finish_lean:.1f}°. '
                'Aim for the shaded zones to optimize power.'
            ),
            'annotations': annotations,
        }



# ---------------------------------------------------------------------------
# Main annotation builder — pure function, independently testable
# ---------------------------------------------------------------------------


def _compute_trunk_annotations(
    x: Any,
    trunk_angle: Any,
    catch_idx: int,
    finish_idx: int,
    catch_lean: float,
    finish_lean: float,
    catch_zone: tuple[float, float],
    finish_zone: tuple[float, float],
    x_min: float = 0.0,
    x_max: float | None = None,
    x_max_idx: int | None = None,
) -> list:
    """Compute the annotation entries for the trunk angle plot.

    Extracted as a pure function so it can be independently tested.

    Annotations produced:
        [P1] Catch Lean point
        [P2] Finish Lean point
        [S1] Drive segment — catch to finish (backdrop + opening timing tip)
        [S2] Recovery segment — finish to next catch (backdrop + rock-over timing tip)
        [Z1] Ideal Catch Zone band
        [Z2] Ideal Finish Zone band

    Returns:
        List of AnnotationEntry objects describing key features of the trunk angle trace.
    """
    catch_ideal_mid = (catch_zone[0] + catch_zone[1]) / 2
    finish_ideal_mid = (finish_zone[0] + finish_zone[1]) / 2
    catch_deviation = catch_lean - catch_ideal_mid
    finish_deviation = finish_lean - finish_ideal_mid

    catch_sign = '+' if catch_deviation >= 0 else ''
    finish_sign = '+' if finish_deviation >= 0 else ''

    # Resolve x bounds for band display names (use data range, not axes xlim)
    x_data_start = float(x[0]) if x_min == 0.0 else x_min
    x_data_end = float(x[-1]) if x_max is None else x_max

    # [P1] Catch lean point
    p1 = PointAnnotation(
        label='[P1]',
        description=f'Catch Lean: {catch_lean:.1f}° (ideal {catch_zone[0]}–{catch_zone[1]}°, {catch_sign}{catch_deviation:.1f}°)',
        x=float(x[catch_idx]) if catch_idx < len(x) else float(catch_idx),
        y=catch_lean,
        style='callout',
        axis_id='top',
        coach_tip=_catch_lean_coach_tip(catch_lean, catch_zone),
    )

    # [P2] Finish lean point
    finish_desc = (
        f'Finish Lean: {finish_lean:.1f}° (ideal {finish_zone[0]}–{finish_zone[1]}°, {finish_sign}{finish_deviation:.1f}°)'
    )
    p2 = PointAnnotation(
        label='[P2]',
        description=finish_desc,
        x=float(x[finish_idx]) if finish_idx < len(x) else float(finish_idx),
        y=finish_lean,
        style='callout',
        axis_id='top',
        coach_tip=_finish_lean_coach_tip(finish_lean, finish_zone),
    )

    # [S1] Drive segment (backdrop)
    drive_x = [float(v) for v in x[catch_idx : finish_idx + 1]]
    drive_y = [float(v) for v in trunk_angle[catch_idx : finish_idx + 1]]
    s1 = SegmentAnnotation(
        label='[S1]',
        description=f'Drive phase: {catch_lean:.1f}° → {finish_lean:.1f}° ({abs(finish_lean - catch_lean):.1f}° range)',
        x_start=float(x[catch_idx]),
        x_end=float(x[finish_idx]),
        x=drive_x,
        y=drive_y,
        style='glow',
        axis_id='top',
        coach_tip=_drive_trunk_opening_coach_tip(drive_y),
    )

    # [S2] Recovery segment (backdrop) — finish to next catch
    rec_end_idx = x_max_idx if x_max_idx is not None else len(x) - 1
    rec_end_idx = min(rec_end_idx, len(x) - 1)
    next_catch_lean = float(trunk_angle[rec_end_idx])
    rec_x = [float(v) for v in x[finish_idx : rec_end_idx + 1]]
    rec_y = [float(v) for v in trunk_angle[finish_idx : rec_end_idx + 1]]
    s2 = SegmentAnnotation(
        label='[S2]',
        description=(
            f'Recovery: {finish_lean:.1f}° \u2192 {next_catch_lean:.1f}° '
            f'({abs(next_catch_lean - finish_lean):.1f}° rock-over)'
        ),
        x_start=float(x[finish_idx]),
        x_end=float(x[rec_end_idx]),
        x=rec_x,
        y=rec_y,
        style='glow',
        axis_id='top',
        coach_tip=_recovery_rock_over_coach_tip(rec_y, catch_zone),
    )

    # [Z1] Ideal catch zone band — color supplied by renderer via color_overrides
    z1 = BandAnnotation(
        label='[Z1]',
        description=f'Ideal Catch Zone: {catch_zone[0]}° to {catch_zone[1]}°',
        y_low=catch_zone[0],
        y_high=catch_zone[1],
        display_name='Ideal Catch Range',
        x_start=x_data_start,
        x_end=x_data_end,
        axis_id='top',
    )

    # [Z2] Ideal finish zone band — color supplied by renderer via color_overrides
    z2 = BandAnnotation(
        label='[Z2]',
        description=f'Ideal Finish Zone: {finish_zone[0]}° to {finish_zone[1]}°',
        y_low=finish_zone[0],
        y_high=finish_zone[1],
        display_name='Ideal Finish Range',
        x_start=x_data_start,
        x_end=x_data_end,
        axis_id='top',
    )

    return [p1, p2, s1, s2, z1, z2]


__all__ = [
    'TrunkAngleComponent',
    '_compute_trunk_annotations',
    '_catch_lean_coach_tip',
    '_finish_lean_coach_tip',
    '_drive_trunk_opening_coach_tip',
    '_recovery_rock_over_coach_tip',
]
