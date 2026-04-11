"""Tests for TrunkAngleSeparationComponent annotations output."""

import numpy as np
import pandas as pd
import pytest

from rowing_catch.plot_transformer.annotations import (
    PointAnnotation,
    SegmentAnnotation,
)
from rowing_catch.plot_transformer.trunk.tip.trunk_angle_separation_tips import (
    catch_separation_tip,
    finish_separation_tip,
    recovery_separation_tip,
)
from rowing_catch.plot_transformer.trunk.trunk_angle_separation_transformer import (
    IDEAL_CATCH_ZONE,
    IDEAL_FINISH_ZONE,
    TrunkAngleSeparationComponent,
    _compute_separation_annotations,
    _recovery_reach_fraction,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_avg_cycle(n: int = 100, catch_idx: int = 20, finish_idx: int = 50) -> pd.DataFrame:
    """Create a minimal avg_cycle DataFrame for testing the separation plot."""
    index = np.arange(n)
    # Seat: goes from 0 mm (catch, front) to 400 mm (finish, back)
    seat = np.linspace(0.0, 400.0, n)
    # Trunk: starts at -30° (forward lean at catch), ends at +15° at finish
    trunk = np.linspace(-30.0, 15.0, n)
    return pd.DataFrame({'Seat_X_Smooth': seat, 'Trunk_Angle': trunk}, index=index)


# ---------------------------------------------------------------------------
# _compute_separation_annotations (pure function)
# ---------------------------------------------------------------------------


class TestComputeSeparationAnnotations:
    def setup_method(self):
        self.n = 100
        self.catch_idx = 20
        self.finish_idx = 50
        self.df = _make_avg_cycle(self.n, self.catch_idx, self.finish_idx)
        self.seat = self.df['Seat_X_Smooth'].values
        self.trunk = self.df['Trunk_Angle'].values
        self.catch_seat = float(self.seat[self.catch_idx])
        self.catch_angle = float(self.trunk[self.catch_idx])
        self.finish_seat = float(self.seat[self.finish_idx])
        self.finish_angle = float(self.trunk[self.finish_idx])

    def _run(self):
        return _compute_separation_annotations(
            seat_values=self.seat,
            angle_values=self.trunk,
            catch_idx=self.catch_idx,
            finish_idx=self.finish_idx,
            n=self.n,
            catch_seat=self.catch_seat,
            catch_angle=self.catch_angle,
            finish_seat=self.finish_seat,
            finish_angle=self.finish_angle,
            catch_zone=IDEAL_CATCH_ZONE,
            finish_zone=IDEAL_FINISH_ZONE,
        )

    def test_returns_three_annotations(self):
        result = self._run()
        assert len(result) == 4

    def test_p1_is_point_annotation_at_catch(self):
        result = self._run()
        p1 = result[0]
        assert isinstance(p1, PointAnnotation)
        assert p1.label == '[P1]'
        assert p1.x == pytest.approx(self.catch_seat, abs=1e-3)
        assert p1.y == pytest.approx(self.catch_angle, abs=1e-6)
        assert p1.style == 'callout'
        assert p1.axis_id == 'main'

    def test_p2_is_point_annotation_at_finish(self):
        result = self._run()
        p2 = result[1]
        assert isinstance(p2, PointAnnotation)
        assert p2.label == '[P2]'
        assert p2.x == pytest.approx(self.finish_seat, abs=1e-3)
        assert p2.y == pytest.approx(self.finish_angle, abs=1e-6)
        assert p2.style == 'callout'
        assert p2.axis_id == 'main'

    def test_s1_is_segment_annotation_for_drive(self):
        result = self._run()
        s1 = result[2]
        assert isinstance(s1, SegmentAnnotation)
        assert s1.label == '[S1]'
        assert s1.style == 'glow'
        assert s1.axis_id == 'main'

    def test_s1_drive_segment_x_y_lengths_match(self):
        result = self._run()
        s1 = result[2]
        expected_len = self.finish_idx - self.catch_idx + 1
        assert len(s1.x) == expected_len
        assert len(s1.y) == expected_len

    def test_s1_drive_x_values_are_seat_positions(self):
        """Segment x must be seat positions, not stroke indices."""
        result = self._run()
        s1 = result[2]
        expected_x = [float(v) for v in self.seat[self.catch_idx : self.finish_idx + 1]]
        assert s1.x == pytest.approx(expected_x, abs=1e-3)

    def test_s1_drive_y_values_are_trunk_angles(self):
        result = self._run()
        s1 = result[2]
        expected_y = [float(v) for v in self.trunk[self.catch_idx : self.finish_idx + 1]]
        assert s1.y == pytest.approx(expected_y, abs=1e-6)

    def test_p1_p2_have_non_empty_coach_tips(self):
        result = self._run()
        for ann in [result[0], result[1]]:
            assert ann.coach_tip, f'{ann.label} coach_tip must not be empty'

    def test_s1_has_empty_coach_tip(self):
        """Drive segment carries no coaching tip — the zone markers tell the story."""
        result = self._run()
        assert result[2].coach_tip == ''

    def test_s2_is_segment_annotation_for_recovery(self):
        result = self._run()
        s2 = result[3]
        assert isinstance(s2, SegmentAnnotation)
        assert s2.label == '[S2]'
        assert s2.style == 'glow'
        assert s2.axis_id == 'main'

    def test_s2_recovery_segment_x_y_lengths_match(self):
        result = self._run()
        s2 = result[3]
        expected_len = self.n - self.finish_idx
        assert len(s2.x) == expected_len
        assert len(s2.y) == expected_len

    def test_s2_x_values_are_seat_positions(self):
        """Recovery segment x must be seat positions, not stroke indices."""
        result = self._run()
        s2 = result[3]
        expected_x = [float(v) for v in self.seat[self.finish_idx :]]
        assert s2.x == pytest.approx(expected_x, abs=1e-3)

    def test_s2_y_values_are_trunk_angles(self):
        result = self._run()
        s2 = result[3]
        expected_y = [float(v) for v in self.trunk[self.finish_idx :]]
        assert s2.y == pytest.approx(expected_y, abs=1e-6)

    def test_s2_has_non_empty_coach_tip(self):
        """Recovery segment carries the separation coaching tip."""
        result = self._run()
        assert result[3].coach_tip, '[S2] coach_tip must not be empty'

    def test_s2_description_mentions_seat_direction(self):
        """Description must explicitly state that seat moves backward."""
        result = self._run()
        assert 'backward' in result[3].description

    def test_all_colors_are_none(self):
        """Colors must be None in the transformer — assigned by apply_annotations()."""
        result = self._run()
        for ann in result:
            assert ann.color is None, f'{ann.label} should have color=None in transformer'

    def test_p1_description_contains_catch_angle(self):
        result = self._run()
        assert f'{self.catch_angle:.1f}' in result[0].description

    def test_p2_description_contains_finish_angle(self):
        result = self._run()
        assert f'{self.finish_angle:.1f}' in result[1].description

    def test_s1_description_contains_range(self):
        result = self._run()
        angle_range = abs(self.finish_angle - self.catch_angle)
        assert f'{angle_range:.1f}' in result[2].description


# ---------------------------------------------------------------------------
# TrunkAngleSeparationComponent.compute() integration
# ---------------------------------------------------------------------------


class TestTrunkAngleSeparationComponentAnnotations:
    def test_compute_includes_annotations_key(self):
        df = _make_avg_cycle()
        component = TrunkAngleSeparationComponent()
        result = component.compute(df, catch_idx=20, finish_idx=50)
        assert 'annotations' in result

    def test_annotations_is_list_of_three(self):
        df = _make_avg_cycle()
        component = TrunkAngleSeparationComponent()
        result = component.compute(df, catch_idx=20, finish_idx=50)
        assert isinstance(result['annotations'], list)
        assert len(result['annotations']) == 4

    def test_annotations_backward_compatible_via_get(self):
        """Renderers use .get('annotations', []) — must be truthy."""
        df = _make_avg_cycle()
        component = TrunkAngleSeparationComponent()
        result = component.compute(df, catch_idx=20, finish_idx=50)
        assert len(result.get('annotations', [])) > 0

    def test_coach_tip_is_non_empty_string(self):
        df = _make_avg_cycle()
        component = TrunkAngleSeparationComponent()
        result = component.compute(df, catch_idx=20, finish_idx=50)
        assert isinstance(result['coach_tip'], str)
        assert len(result['coach_tip']) > 0

    def test_data_keys_present(self):
        df = _make_avg_cycle()
        component = TrunkAngleSeparationComponent()
        result = component.compute(df, catch_idx=20, finish_idx=50)
        for key in ('seat_position', 'trunk_angle_plot', 'catch_seat', 'catch_angle', 'finish_seat', 'finish_angle'):
            assert key in result['data'], f'Missing data key: {key}'


# ---------------------------------------------------------------------------
# catch_separation_tip — scenario coverage
# ---------------------------------------------------------------------------


class TestCatchSeparationTip:
    ZONE = IDEAL_CATCH_ZONE  # (-33.0, -27.0)

    def test_too_upright_returns_rock_over_more(self):
        tip = catch_separation_tip(-20.0, self.ZONE)
        assert 'Rock over more' in tip
        assert '7.0' in tip  # deficit = |-20 - (-27)| = 7.0
        assert 'ideal lean' in tip  # aligned with trunk_angle_tips

    def test_over_leaning_returns_reduce_lean(self):
        tip = catch_separation_tip(-40.0, self.ZONE)
        assert 'Reduce lean' in tip
        assert '7.0' in tip  # excess = |-40 - (-33)| = 7.0

    def test_within_zone_returns_ok_message(self):
        tip = catch_separation_tip(-30.0, self.ZONE)
        assert 'Catch lean is within ideal range' in tip  # aligned with trunk_angle_tips

    def test_exactly_on_upper_bound_is_ok(self):
        tip = catch_separation_tip(-27.0, self.ZONE)
        assert 'ideal range' in tip

    def test_exactly_on_lower_bound_is_ok(self):
        tip = catch_separation_tip(-33.0, self.ZONE)
        assert 'ideal range' in tip

    def test_returns_string(self):
        assert isinstance(catch_separation_tip(-30.0, self.ZONE), str)


# ---------------------------------------------------------------------------
# finish_separation_tip — scenario coverage
# ---------------------------------------------------------------------------


class TestFinishSeparationTip:
    ZONE = IDEAL_FINISH_ZONE  # (12.0, 18.0)

    def test_too_little_layback_returns_lay_back_more(self):
        tip = finish_separation_tip(8.0, self.ZONE)
        assert 'Lay back more' in tip
        assert '4.0' in tip  # deficit = |8 - 12| = 4.0
        assert 'ideal finish lean' in tip  # aligned with trunk_angle_tips

    def test_over_extended_returns_reduce_layback(self):
        tip = finish_separation_tip(24.0, self.ZONE)
        assert 'Reduce lay-back' in tip
        assert '6.0' in tip  # excess = |24 - 18| = 6.0

    def test_within_zone_returns_ok_message(self):
        tip = finish_separation_tip(15.0, self.ZONE)
        assert 'Finish lean is within ideal range' in tip  # aligned with trunk_angle_tips; uses ✓ not –

    def test_exactly_on_lower_bound_is_ok(self):
        tip = finish_separation_tip(12.0, self.ZONE)
        assert 'ideal range' in tip

    def test_exactly_on_upper_bound_is_ok(self):
        tip = finish_separation_tip(18.0, self.ZONE)
        assert 'ideal range' in tip

    def test_returns_string(self):
        assert isinstance(finish_separation_tip(15.0, self.ZONE), str)


# ---------------------------------------------------------------------------
# _recovery_reach_fraction — unit tests
# ---------------------------------------------------------------------------


class TestRecoveryReachFraction:
    """Tests for the pure helper that computes seat-travel fraction."""

    CATCH_ZONE = IDEAL_CATCH_ZONE  # (-33.0, -27.0), midpoint = -30.0

    def _make_recovery(self, n: int, start: float, end: float) -> tuple[list[float], list[float]]:
        """Linear ramp from start (finish angle) to end (next-catch angle) over n points.
        Seat travels from 400 mm down to 0 mm linearly.
        """
        rec_y = [start + (end - start) * i / (n - 1) for i in range(n)]
        rec_x = [400.0 - 400.0 * i / (n - 1) for i in range(n)]
        return rec_y, rec_x

    def test_reaches_catch_zone_at_mid_point(self):
        """Linear ramp from +15° to -30° over 100 points, catch mid = -30°.
        The trunk hits -30° at the very last point → reach_frac ≈ 1.0."""
        rec_y, rec_x = self._make_recovery(100, start=15.0, end=-30.0)
        frac = _recovery_reach_fraction(rec_y, self.CATCH_ZONE, rec_x, total_seat_travel=400.0)
        assert 0.0 <= frac <= 1.0

    def test_never_reaches_zone_returns_one(self):
        """Trunk stays at +15° throughout — never reaches -30° catch zone."""
        rec_y = [15.0] * 50
        rec_x = [400.0 - 400.0 * i / 49 for i in range(50)]
        frac = _recovery_reach_fraction(rec_y, self.CATCH_ZONE, rec_x, total_seat_travel=400.0)
        assert frac == pytest.approx(1.0)

    def test_immediate_reach_returns_near_zero(self):
        """Trunk immediately at -30° from the first point → fraction ≈ 0."""
        rec_y = [-30.0] * 50
        rec_x = [400.0 - 400.0 * i / 49 for i in range(50)]
        frac = _recovery_reach_fraction(rec_y, self.CATCH_ZONE, rec_x, total_seat_travel=400.0)
        assert frac == pytest.approx(0.0, abs=1e-3)

    def test_fraction_is_between_zero_and_one(self):
        """Trunk reaches zone at ~50% of recovery."""
        # Flat at +15° for 50 points, then instantly at -30°
        rec_y = [15.0] * 50 + [-30.0] * 50
        rec_x = [400.0 - 400.0 * i / 99 for i in range(100)]
        frac = _recovery_reach_fraction(rec_y, self.CATCH_ZONE, rec_x, total_seat_travel=400.0)
        assert 0.0 < frac < 1.0

    def test_zero_seat_travel_returns_one(self):
        """Guard against division by zero when total_seat_travel=0."""
        rec_y = [15.0, -30.0]
        rec_x = [400.0, 400.0]
        frac = _recovery_reach_fraction(rec_y, self.CATCH_ZONE, rec_x, total_seat_travel=0.0)
        assert frac == pytest.approx(1.0)

    def test_single_point_returns_one(self):
        frac = _recovery_reach_fraction([-30.0], self.CATCH_ZONE, [400.0], total_seat_travel=400.0)
        assert frac == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# recovery_separation_tip — scenario coverage
# ---------------------------------------------------------------------------


class TestRecoverySeparationTip:
    def test_rushes_over_immediately_returns_warning(self):
        """reach_frac < 0.10 → trunk rushes forward; check balance."""
        tip = recovery_separation_tip(0.05)
        assert 'immediately' in tip or 'rushes' in tip or 'rush' in tip

    def test_ideal_early_returns_positive(self):
        """reach_frac = 0.30 → good separation."""
        tip = recovery_separation_tip(0.30)
        assert 'Good' in tip or '\u2713' in tip

    def test_ideal_boundary_low_is_ok(self):
        """reach_frac = 0.10 → just inside ideal window."""
        tip = recovery_separation_tip(0.10)
        assert 'Good' in tip or '\u2713' in tip

    def test_ideal_boundary_high_is_ok(self):
        """reach_frac = 0.50 → upper edge of ideal window."""
        tip = recovery_separation_tip(0.50)
        assert 'Good' in tip or '\u2713' in tip

    def test_late_returns_warning(self):
        """reach_frac = 0.70 → late, body still moving when seat arrives."""
        tip = recovery_separation_tip(0.70)
        assert 'Late' in tip or 'late' in tip

    def test_very_late_returns_no_separation_warning(self):
        """reach_frac = 0.95 → no separation at all."""
        tip = recovery_separation_tip(0.95)
        assert 'last moment' in tip or 'no separation' in tip.lower() or 'arrives' in tip

    def test_boundary_0_90_is_late(self):
        """reach_frac = 0.90 → upper edge of late window, still 'Late'."""
        tip = recovery_separation_tip(0.90)
        assert 'Late' in tip or 'late' in tip

    def test_boundary_above_0_90_is_very_late(self):
        """reach_frac = 0.91 → into very-late territory."""
        tip = recovery_separation_tip(0.91)
        assert 'last moment' in tip or 'arrives' in tip or 'no separation' in tip.lower()

    def test_returns_string(self):
        assert isinstance(recovery_separation_tip(0.50), str)

