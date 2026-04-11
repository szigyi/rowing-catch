"""Trunk Angle Separation plot transform.

Shows how the body rocks over relative to seat position timing.
"""

from typing import Any, cast

import pandas as pd

from rowing_catch.plot_transformer.annotations import (
    PointAnnotation,
    SegmentAnnotation,
)
from rowing_catch.plot_transformer.base import PlotComponent
from rowing_catch.plot_transformer.trunk.tip.trunk_angle_separation_tips import (
    catch_separation_tip,
    finish_separation_tip,
    recovery_separation_tip,
)

# Ideal target zones (degrees from vertical) — consistent with TrunkAngleComponent
IDEAL_CATCH_ZONE: tuple[float, float] = (-33.0, -27.0)
IDEAL_FINISH_ZONE: tuple[float, float] = (12.0, 18.0)


class TrunkAngleSeparationComponent(PlotComponent):
    """Trunk angle vs seat position component."""

    @property
    def name(self) -> str:
        return 'Trunk Angle Separation'

    @property
    def description(self) -> str:
        return 'Body rocking timing relative to seat position'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute trunk angle separation plot data.

        Args:
            avg_cycle: DataFrame with rowing stroke data
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Optional comparison DataFrame (used as scenario_data)
            results: Optional results dict with scenario_name

        Returns:
            Dict with plot data, metadata, coach_tip, and annotations

        Annotations produced:
            [P1] Catch point — trunk angle at catch vs. ideal zone
            [P2] Finish point — trunk angle at finish vs. ideal zone
            [S1] Drive trajectory — seat×angle path from catch to finish (seat moves forward)
            [S2] Recovery trajectory — seat×angle path from finish back to next catch (seat moves backward)
        """
        scenario_data = ghost_cycle
        scenario_name = results.get('scenario_name', 'None') if results else 'None'

        catch_seat = cast(float, avg_cycle.at[catch_idx, 'Seat_X_Smooth'])
        catch_angle = cast(float, avg_cycle.at[catch_idx, 'Trunk_Angle'])
        finish_seat = cast(float, avg_cycle.at[finish_idx, 'Seat_X_Smooth'])
        finish_angle = cast(float, avg_cycle.at[finish_idx, 'Trunk_Angle'])

        seat_values = avg_cycle['Seat_X_Smooth'].values
        angle_values = avg_cycle['Trunk_Angle'].values

        annotations = _compute_separation_annotations(
            seat_values=seat_values,
            angle_values=angle_values,
            catch_idx=catch_idx,
            finish_idx=finish_idx,
            n=len(avg_cycle),
            catch_seat=catch_seat,
            catch_angle=catch_angle,
            finish_seat=finish_seat,
            finish_angle=finish_angle,
            catch_zone=IDEAL_CATCH_ZONE,
            finish_zone=IDEAL_FINISH_ZONE,
        )

        return {
            'data': {
                'seat_position': seat_values,
                'trunk_angle_plot': angle_values,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
                'catch_seat': catch_seat,
                'catch_angle': catch_angle,
                'finish_seat': finish_seat,
                'finish_angle': finish_angle,
                'scenario_seat': scenario_data['Seat_X_Smooth'].values if scenario_data is not None else None,
                'scenario_angle': scenario_data['Trunk_Angle'].values if scenario_data is not None else None,
                'scenario_data': scenario_data,
            },
            'metadata': {
                'title': 'Trunk Angle vs Stroke Progress',
                'x_label': 'Seat Position (mm)',
                'y_label': 'Trunk Angle (deg)',
                'scenario_name': scenario_name,
            },
            'coach_tip': (
                "Watch for 'Body Over' before the knees come up in recovery. "
                'The angle should drop towards the catch while the seat is still moving backwards.'
            ),
            'annotations': annotations,
        }


# ---------------------------------------------------------------------------
# Pure annotation builder — independently testable
# ---------------------------------------------------------------------------


def _compute_separation_annotations(
    seat_values: Any,
    angle_values: Any,
    catch_idx: int,
    finish_idx: int,
    catch_seat: float,
    catch_angle: float,
    finish_seat: float,
    finish_angle: float,
    n: int | None = None,
    catch_zone: tuple[float, float] = IDEAL_CATCH_ZONE,
    finish_zone: tuple[float, float] = IDEAL_FINISH_ZONE,
) -> list:
    """Compute annotation entries for the Trunk Angle Separation plot.

    The x-axis of this plot is seat position (mm); the y-axis is trunk angle (°).
    All annotation x-coordinates are therefore seat positions, not stroke indices.

    During the **drive** the seat moves forward (X increases, catch → finish).
    During **recovery** the seat moves backward (X decreases, finish → next catch).

    Annotations produced:
        [P1] Catch point  — trunk angle at catch seat position vs. ideal zone
        [P2] Finish point — trunk angle at finish seat position vs. ideal zone
        [S1] Drive segment  — seat×angle path from catch to finish (seat moves forward)
        [S2] Recovery segment — seat×angle path from finish to next catch (seat moves backward)

    Args:
        seat_values: Full array of Seat_X_Smooth values
        angle_values: Full array of Trunk_Angle values
        catch_idx: Index of catch in the arrays
        finish_idx: Index of finish in the arrays
        catch_seat: Seat position at catch (mm)
        catch_angle: Trunk angle at catch (degrees)
        finish_seat: Seat position at finish (mm)
        finish_angle: Trunk angle at finish (degrees)
        n: Total length of the arrays. Defaults to len(seat_values).
        catch_zone: (low, high) ideal catch angle range
        finish_zone: (low, high) ideal finish angle range

    Returns:
        List of AnnotationEntry objects.
    """
    if n is None:
        n = len(seat_values)

    catch_ideal_mid = (catch_zone[0] + catch_zone[1]) / 2
    finish_ideal_mid = (finish_zone[0] + finish_zone[1]) / 2
    catch_dev = catch_angle - catch_ideal_mid
    finish_dev = finish_angle - finish_ideal_mid
    catch_sign = '+' if catch_dev >= 0 else ''
    finish_sign = '+' if finish_dev >= 0 else ''

    # [P1] Catch body position
    p1 = PointAnnotation(
        label='[P1]',
        description=(
            f'Catch: {catch_angle:.1f}\u00b0 lean at seat {catch_seat:.0f} mm '
            f'(ideal {catch_zone[0]}\u2013{catch_zone[1]}\u00b0, {catch_sign}{catch_dev:.1f}\u00b0)'
        ),
        x=float(catch_seat),
        y=float(catch_angle),
        style='callout',
        coach_tip=catch_separation_tip(catch_angle, catch_zone),
    )

    # [P2] Finish body position
    p2 = PointAnnotation(
        label='[P2]',
        description=(
            f'Finish: {finish_angle:.1f}\u00b0 lean at seat {finish_seat:.0f} mm '
            f'(ideal {finish_zone[0]}\u2013{finish_zone[1]}\u00b0, {finish_sign}{finish_dev:.1f}\u00b0)'
        ),
        x=float(finish_seat),
        y=float(finish_angle),
        style='callout',
        coach_tip=finish_separation_tip(finish_angle, finish_zone),
    )

    # [S1] Drive trajectory (catch → finish): seat moves forward (X increases)
    drive_x = [float(v) for v in seat_values[catch_idx : finish_idx + 1]]
    drive_y = [float(v) for v in angle_values[catch_idx : finish_idx + 1]]
    angle_range = abs(finish_angle - catch_angle)
    s1 = SegmentAnnotation(
        label='[S1]',
        description=(
            f'Drive: seat {catch_seat:.0f}\u2192{finish_seat:.0f} mm, '
            f'trunk {catch_angle:.1f}\u00b0\u2192{finish_angle:.1f}\u00b0 '
            f'({angle_range:.1f}\u00b0 range; seat moves forward)'
        ),
        x_start=float(catch_seat),
        x_end=float(finish_seat),
        x=drive_x,
        y=drive_y,
        style='glow',
        coach_tip='',
    )

    # [S2] Recovery trajectory (finish → next catch): seat moves backward (X decreases).
    # Compute when the trunk first reaches the catch zone midpoint, expressed as a
    # fraction of total recovery seat travel (0.0 = just left finish, 1.0 = back at catch).
    rec_end_idx = n - 1
    rec_x = [float(v) for v in seat_values[finish_idx : rec_end_idx + 1]]
    rec_y = [float(v) for v in angle_values[finish_idx : rec_end_idx + 1]]
    next_catch_angle = float(angle_values[rec_end_idx])
    next_catch_seat = float(seat_values[rec_end_idx])

    total_seat_travel = abs(float(seat_values[finish_idx]) - float(seat_values[rec_end_idx]))
    reach_frac = _recovery_reach_fraction(rec_y, catch_zone, rec_x, total_seat_travel)

    s2 = SegmentAnnotation(
        label='[S2]',
        description=(
            f'Recovery: seat {finish_seat:.0f}\u2192{next_catch_seat:.0f} mm, '
            f'trunk {finish_angle:.1f}\u00b0\u2192{next_catch_angle:.1f}\u00b0 '
            f'({abs(next_catch_angle - finish_angle):.1f}\u00b0 rock-over; seat moves backward)'
        ),
        x_start=float(seat_values[finish_idx]),
        x_end=float(seat_values[rec_end_idx]),
        x=rec_x,
        y=rec_y,
        style='glow',
        coach_tip=recovery_separation_tip(reach_frac),
    )

    return [p1, p2, s1, s2]


def _recovery_reach_fraction(
    rec_y: list[float],
    catch_zone: tuple[float, float],
    rec_x: list[float],
    total_seat_travel: float,
) -> float:
    """Compute the fraction of recovery seat travel at which the trunk enters the catch zone.

    Returns 1.0 if the trunk never reaches the catch zone midpoint during recovery,
    meaning there is no separation at all.

    Args:
        rec_y: Trunk angle values from finish to next catch
        catch_zone: (low, high) ideal catch angle range
        rec_x: Seat position values from finish to next catch (parallel to rec_y)
        total_seat_travel: Total seat distance covered during recovery (mm), always > 0

    Returns:
        Fraction in [0.0, 1.0].
    """
    catch_mid = (catch_zone[0] + catch_zone[1]) / 2
    if total_seat_travel <= 0 or len(rec_y) < 2:
        return 1.0
    finish_seat = rec_x[0]
    for seat_pos, angle in zip(rec_x, rec_y, strict=True):
        if angle <= catch_mid:
            seat_travelled = abs(seat_pos - finish_seat)
            return min(seat_travelled / total_seat_travel, 1.0)
    return 1.0


__all__ = [
    'IDEAL_CATCH_ZONE',
    'IDEAL_FINISH_ZONE',
    'TrunkAngleSeparationComponent',
    '_compute_separation_annotations',
    '_recovery_reach_fraction',
]
