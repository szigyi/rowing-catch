"""Handle-Seat Distance plot transform.

Transforms analysis results into data ready for rendering the handle-seat
distance (intra-stroke compression) plot.

Phase detection
---------------
The distance curve is divided into three sections:

  Drive phase      — catch_idx  →  first_min_idx
                     Handle stays far from seat while legs drive;
                     then upper body engages and distance drops.

  Intra-stroke     — first_min_idx  →  second_min_idx (around finish_idx)
  Compression        The hands-away bump: handle moves away from seat
                     while seat is still stationary at the finish.

  Recovery         — second_min_idx  →  end of avg_cycle
                     Handle and seat separate as the rower rocks over and
                     slides up for the next catch.
"""

from typing import Any

import numpy as np
import pandas as pd

from rowing_catch.coaching.profile import CoachingProfile
from rowing_catch.plot_transformer.annotations import (
    AnnotationEntry,
    PhaseAnnotation,
    PointAnnotation,
    SegmentAnnotation,
)
from rowing_catch.plot_transformer.base import PlotComponent
from rowing_catch.plot_transformer.handle_seat.tip import (
    ROCKOVER_DISTANCE_FRACTION,
    compression_duration_coach_tip,
    compression_timing_coach_tip,
    late_rockover_coach_tip,
    recovery_rockover_coach_tip,
)

# Minimum gradient magnitude (normalised) to count as start of compression.
_COMPRESSION_GRAD_THRESHOLD_FRACTION: float = 0.3


def _find_compression_start(
    distance: np.ndarray,
    catch_idx: int,
    first_min_idx: int,
) -> int:
    """Detect the index where distance starts to decrease during the drive.

    Uses normalised gradient: the first point where the gradient drops below
    -COMPRESSION_GRAD_THRESHOLD_FRACTION * std(gradient).

    Returns the absolute index into *distance* (same coordinates as catch_idx).
    Falls back to the midpoint of the drive if no clear onset is found.
    """
    drive_segment = distance[catch_idx:first_min_idx]
    if len(drive_segment) < 4:  # noqa: PLR2004
        return (catch_idx + first_min_idx) // 2

    grad = np.gradient(drive_segment.astype(float))
    threshold = -_COMPRESSION_GRAD_THRESHOLD_FRACTION * float(np.std(grad))

    candidates = np.where(grad < threshold)[0]
    if candidates.size == 0:
        return (catch_idx + first_min_idx) // 2  # fallback: midpoint

    return int(catch_idx + candidates[0])


class HandleSeatDistanceComponent(PlotComponent):
    """Handle-seat distance (intra-stroke compression) component."""

    def __init__(self, profile: CoachingProfile | None = None) -> None:
        """Initialise with optional coaching profile.

        Args:
            profile: Coach-configurable thresholds.  Uses defaults when None.
        """
        self.profile = profile or CoachingProfile()

    @property
    def name(self) -> str:
        return 'Handle-Seat Distance'

    @property
    def description(self) -> str:
        return 'Intra-stroke compression: handle-to-seat separation across the stroke cycle'

    def compute(
        self,
        avg_cycle: pd.DataFrame,
        catch_idx: int,
        finish_idx: int,
        ghost_cycle: pd.DataFrame | None = None,
        results: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Compute handle-seat distance plot data with phase annotations.

        Args:
            avg_cycle: DataFrame with rowing stroke data
            catch_idx: Index of catch
            finish_idx: Index of finish
            ghost_cycle: Optional comparison DataFrame
            results: Optional results dict with scenario_name

        Returns:
            Dict with 'data', 'metadata', 'annotations', 'coach_tip' keys
        """
        scenario_data = ghost_cycle
        scenario_name = results.get('scenario_name', 'None') if results else 'None'

        dist_series = np.abs(avg_cycle['Handle_X_Smooth'] - avg_cycle['Seat_X_Smooth'])
        distance: np.ndarray = dist_series.values if hasattr(dist_series, 'values') else np.asarray(dist_series)
        x: np.ndarray = avg_cycle.index.values

        scenario_dist_values = None
        if scenario_data is not None:
            sd = np.abs(scenario_data['Handle_X_Smooth'] - scenario_data['Seat_X_Smooth'])
            scenario_dist_values = sd.values if hasattr(sd, 'values') else np.asarray(sd)

        # Per-cycle distance overlays
        cycles: list[Any] = results.get('cycles', []) if results else []
        min_length = len(avg_cycle)
        cycle_distances: list[list[float]] = []
        for cyc in cycles:
            n = min(min_length, len(cyc))
            cd = np.abs(cyc['Handle_X_Smooth'].iloc[:n].values - cyc['Seat_X_Smooth'].iloc[:n].values)
            cycle_distances.append(cd.tolist())

        # ------------------------------------------------------------------ #
        # Phase boundary detection
        # ------------------------------------------------------------------ #

        # First minimum: deepest compression just before the hands-away bump
        drive_slice = distance[catch_idx:finish_idx]
        first_min_rel = int(np.argmin(drive_slice)) if drive_slice.size > 0 else 0
        first_min_idx = catch_idx + first_min_rel

        # Second minimum: after the finish bump, before recovery extension
        search_end = min(len(distance), finish_idx + max(4, (finish_idx - catch_idx) // 2))
        post_finish = distance[finish_idx:search_end]
        second_min_rel = int(np.argmin(post_finish)) if post_finish.size > 0 else 0
        second_min_idx = finish_idx + second_min_rel

        end_idx = len(distance) - 1

        # ------------------------------------------------------------------ #
        # Compression start during drive
        # ------------------------------------------------------------------ #

        compression_start_idx = _find_compression_start(distance, catch_idx, first_min_idx)
        drive_length = finish_idx - catch_idx
        compression_start_pct = (compression_start_idx - catch_idx) / drive_length * 100.0 if drive_length > 0 else 50.0
        compression_duration_pct = (first_min_idx - compression_start_idx) / drive_length * 100.0 if drive_length > 0 else 50.0

        # ------------------------------------------------------------------ #
        # Recovery rock-over metrics
        # ------------------------------------------------------------------ #

        recovery_segment = distance[second_min_idx:]
        recovery_length = len(recovery_segment)
        max_recovery = float(np.max(recovery_segment)) if recovery_segment.size > 0 else 0.0
        min_recovery = float(distance[second_min_idx])
        recovery_range = max_recovery - min_recovery

        rockover_achieved_pct: float = 100.0
        if recovery_range > 0 and recovery_length > 1:
            target_value = min_recovery + ROCKOVER_DISTANCE_FRACTION * recovery_range
            reached = np.where(recovery_segment >= target_value)[0]
            if reached.size > 0:
                rockover_achieved_pct = float(reached[0]) / recovery_length * 100.0

        # Q6: still increasing in the last handle_seat_rockover_pct% of recovery
        late_window_pct = self.profile.handle_seat_rockover_pct
        late_start_rel = int(recovery_length * (1.0 - late_window_pct / 100.0))
        late_start_rel = max(0, min(late_start_rel, recovery_length - 2))
        late_segment = recovery_segment[late_start_rel:]
        still_increasing = bool(late_segment.size >= 2 and float(np.mean(np.gradient(late_segment.astype(float)))) > 0.5)

        # ------------------------------------------------------------------ #
        # Build annotations
        # ------------------------------------------------------------------ #

        annotations: list[AnnotationEntry] = []

        # [Ph1] Drive Phase region
        annotations.append(
            PhaseAnnotation(
                label='[Ph1]',
                description='Drive Phase — legs pushing, handle held out, then upper body engages',
                x_start=float(x[catch_idx]),
                x_end=float(x[first_min_idx]),
                coach_tip='',
            )
        )

        # [Ph2] Intra-Stroke Compression region (no coaching tip)
        annotations.append(
            PhaseAnnotation(
                label='[Ph2]',
                description='Intra-Stroke Compression — hands-away bump at the finish',
                x_start=float(x[first_min_idx]),
                x_end=float(x[second_min_idx]),
                coach_tip='',
            )
        )

        # [Ph3] Recovery region
        annotations.append(
            PhaseAnnotation(
                label='[Ph3]',
                description='Recovery — rower rocks forward, handle and seat separate',
                x_start=float(x[second_min_idx]),
                x_end=float(x[end_idx]),
                coach_tip='',
            )
        )

        # [P1] Compression start point — upper body engagement timing
        p1_tip, p1_ideal = compression_timing_coach_tip(
            compression_start_pct,
            self.profile.trunk_opening_ideal_pct,
            self.profile.trunk_open_tolerance_pct,
        )
        annotations.append(
            PointAnnotation(
                label='[P1]',
                description=f'Upper body engagement start: {compression_start_pct:.0f}% of drive',
                x=float(x[compression_start_idx]),
                y=float(distance[compression_start_idx]),
                style='callout',
                coach_tip=p1_tip,
                coach_tip_is_ideal=p1_ideal,
            )
        )

        # [S1] Compression phase segment — duration tip
        comp_x = x[compression_start_idx : first_min_idx + 1].tolist()
        comp_y = distance[compression_start_idx : first_min_idx + 1].tolist()
        s1_tip, s1_ideal = compression_duration_coach_tip(
            compression_duration_pct,
            self.profile.handle_seat_compression_max_pct,
        )
        annotations.append(
            SegmentAnnotation(
                label='[S1]',
                description=f'Upper body draw phase: {compression_duration_pct:.0f}% of drive',
                x_start=float(x[compression_start_idx]),
                x_end=float(x[first_min_idx]),
                x=comp_x,
                y=comp_y,
                style='glow',
                coach_tip=s1_tip,
                coach_tip_is_ideal=s1_ideal,
            )
        )

        # [P2] Rock-over achievement point in recovery
        rockover_abs_idx = second_min_idx + int(rockover_achieved_pct / 100.0 * recovery_length)
        rockover_abs_idx = min(rockover_abs_idx, end_idx)
        p2_tip, p2_ideal = recovery_rockover_coach_tip(
            rockover_achieved_pct,
            self.profile.handle_seat_rockover_pct,
        )
        annotations.append(
            PointAnnotation(
                label='[P2]',
                description=f'50% rock-over reached at {rockover_achieved_pct:.0f}% of recovery',
                x=float(x[rockover_abs_idx]),
                y=float(distance[rockover_abs_idx]),
                style='callout',
                coach_tip=p2_tip,
                coach_tip_is_ideal=p2_ideal,
            )
        )

        # [P3] Still increasing close to catch (only shown when flagged)
        if still_increasing:
            late_abs_idx = second_min_idx + late_start_rel
            p3_tip, p3_ideal = late_rockover_coach_tip(still_increasing, late_window_pct)
            annotations.append(
                PointAnnotation(
                    label='[P3]',
                    description=f'Handle still separating in last {late_window_pct:.0f}% of recovery',
                    x=float(x[late_abs_idx]),
                    y=float(distance[late_abs_idx]),
                    style='callout',
                    coach_tip=p3_tip,
                    coach_tip_is_ideal=p3_ideal,
                )
            )

        # ------------------------------------------------------------------ #
        # Summary coach tip (overall)
        # ------------------------------------------------------------------ #

        coach_tip = (
            'Maximising handle-seat distance at the catch (compression) without over-reaching '
            'is key to a long effective stroke. '
            'After the finish, rock over quickly — get the body forward early before the slide begins.'
        )

        return {
            'data': {
                'x': x,
                'distance': distance,
                'catch_idx': catch_idx,
                'finish_idx': finish_idx,
                'first_min_idx': first_min_idx,
                'second_min_idx': second_min_idx,
                'scenario_distance': scenario_dist_values,
                'scenario_data': scenario_data,
                'cycle_distances': cycle_distances,
            },
            'metadata': {
                'title': 'Handle-Seat Separation (Intra-Stroke Compression)',
                'x_label': 'Stroke Index',
                'y_label': 'Distance (mm)',
                'scenario_name': scenario_name,
            },
            'annotations': annotations,
            'coach_tip': coach_tip,
        }
