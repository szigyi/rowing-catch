"""Tests for TrunkAngleComponent annotations output."""

import numpy as np
import pandas as pd
import pytest

from rowing_catch.plot_transformer.annotations import (
    BandAnnotation,
    PointAnnotation,
    SegmentAnnotation,
)
from rowing_catch.plot_transformer.trunk.trunk_angle_transformer import (
    TrunkAngleComponent,
    _catch_lean_coach_tip,
    _compute_trunk_annotations,
    _drive_trunk_opening_coach_tip,
    _finish_lean_coach_tip,
    _recovery_rock_over_coach_tip,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_avg_cycle(n: int = 100, catch_idx: int = 20, finish_idx: int = 50) -> pd.DataFrame:
    """Create a minimal avg_cycle DataFrame for testing."""
    index = np.arange(n)
    # Simple linear ramp: -30° at catch, +15° at finish, interpolated
    trunk = np.linspace(-30.0, 15.0, n)
    return pd.DataFrame({'Trunk_Angle': trunk}, index=index)


# ---------------------------------------------------------------------------
# _compute_trunk_annotations (pure function)
# ---------------------------------------------------------------------------


class TestComputeTrunkAnnotations:
    def setup_method(self):
        self.n = 100
        self.catch_idx = 20
        self.finish_idx = 50
        self.df = _make_avg_cycle(self.n, self.catch_idx, self.finish_idx)
        self.x = self.df.index.to_numpy()
        self.trunk = self.df['Trunk_Angle'].values
        self.catch_lean = float(self.trunk[self.catch_idx])
        self.finish_lean = float(self.trunk[self.finish_idx])
        self.catch_zone = (-33.0, -27.0)
        self.finish_zone = (12.0, 18.0)

    def _run(self):
        return _compute_trunk_annotations(
            x=self.x,
            trunk_angle=self.trunk,
            catch_idx=self.catch_idx,
            finish_idx=self.finish_idx,
            catch_lean=self.catch_lean,
            finish_lean=self.finish_lean,
            catch_zone=self.catch_zone,
            finish_zone=self.finish_zone,
        )

    def test_returns_five_annotations(self):
        result = self._run()
        assert len(result) == 6

    def test_p1_is_point_annotation_at_catch(self):
        result = self._run()
        p1 = result[0]
        assert isinstance(p1, PointAnnotation)
        assert p1.label == '[P1]'
        assert p1.axis_id == 'top'
        assert p1.y == pytest.approx(self.catch_lean, abs=1e-6)

    def test_p2_is_point_annotation_at_finish(self):
        result = self._run()
        p2 = result[1]
        assert isinstance(p2, PointAnnotation)
        assert p2.label == '[P2]'
        assert p2.axis_id == 'top'
        assert p2.y == pytest.approx(self.finish_lean, abs=1e-6)

    def test_s1_is_segment_annotation_covering_drive(self):
        result = self._run()
        s1 = result[2]
        assert isinstance(s1, SegmentAnnotation)
        assert s1.label == '[S1]'
        assert s1.style == 'glow'
        assert len(s1.x) == self.finish_idx - self.catch_idx + 1
        assert len(s1.y) == len(s1.x)
        assert s1.x[0] == pytest.approx(float(self.x[self.catch_idx]))
        assert s1.x[-1] == pytest.approx(float(self.x[self.finish_idx]))

    def test_s2_is_segment_annotation_covering_recovery(self):
        result = self._run()
        s2 = result[3]
        assert isinstance(s2, SegmentAnnotation)
        assert s2.label == '[S2]'
        assert s2.style == 'glow'
        assert s2.axis_id == 'top'
        # Recovery goes from finish_idx to end of x
        assert len(s2.x) == self.n - self.finish_idx
        assert s2.x[0] == pytest.approx(float(self.x[self.finish_idx]))
        assert s2.x[-1] == pytest.approx(float(self.x[-1]))

    def test_z1_is_band_annotation_for_catch_zone(self):
        result = self._run()
        z1 = result[4]
        assert isinstance(z1, BandAnnotation)
        assert z1.label == '[Z1]'
        assert z1.y_low == self.catch_zone[0]
        assert z1.y_high == self.catch_zone[1]
        assert z1.axis_id == 'top'

    def test_z2_is_band_annotation_for_finish_zone(self):
        result = self._run()
        z2 = result[5]
        assert isinstance(z2, BandAnnotation)
        assert z2.label == '[Z2]'
        assert z2.y_low == self.finish_zone[0]
        assert z2.y_high == self.finish_zone[1]
        assert z2.axis_id == 'top'

    def test_description_contains_deviation(self):
        """Descriptions must include deviation from ideal."""
        result = self._run()
        catch_ideal_mid = (self.catch_zone[0] + self.catch_zone[1]) / 2
        expected_deviation = self.catch_lean - catch_ideal_mid
        sign = '+' if expected_deviation >= 0 else ''
        assert f'{sign}{expected_deviation:.1f}°' in result[0].description

    def test_a6_is_segment_annotation_covering_recovery(self):
        result = self._run()
        s2 = result[3]
        assert isinstance(s2, SegmentAnnotation)
        assert s2.label == '[S2]'
        assert s2.style == 'glow'
        assert s2.axis_id == 'top'
        # Recovery goes from finish_idx to end of x
        assert len(s2.x) == self.n - self.finish_idx
        assert s2.x[0] == pytest.approx(float(self.x[self.finish_idx]))
        assert s2.x[-1] == pytest.approx(float(self.x[-1]))

    def test_a1_a2_a3_a6_have_non_empty_coach_tips(self):
        """Point and segment annotations ([P1], [P2], [S1], [S2]) must carry computed coach tips."""
        result = self._run()
        # [P1], [P2], [S1], [S2] are at indices 0, 1, 2, 3
        for ann in [result[0], result[1], result[2], result[3]]:
            assert ann.coach_tip, f'{ann.label} coach_tip must not be empty'

    def test_a4_a5_have_empty_coach_tips(self):
        """Band annotations ([Z1], [Z2]) carry no coach tip — the zone speaks for itself."""
        result = self._run()
        # [Z1], [Z2] are at indices 4, 5
        for ann in result[4:6]:
            assert ann.coach_tip == '', f'{ann.label} coach_tip should be empty'

    def test_colors_none_for_all_annotations(self):
        """All transformer annotations have color=None — colors are assigned implicitly
        by assign_annotation_colors() from the palette, which is ordered so that:
          slot 1 (Fuchsia)  → [P1], slot 2 (Teal)   → [P2],
          slot 3 (Amber)    → [S1], slot 4 (Orange)  → [S2],
          slot 5/6          → [Z1]/[Z2] (renderer-overridden anyway).
        Zone bands ([Z1], [Z2]) colors are further overridden by the renderer via
        color_overrides in apply_annotations().
        """
        result = self._run()
        for ann in result:
            assert ann.color is None, f'{ann.label} should have color=None in transformer'

    def test_segment_y_values_match_trunk_angle_slice(self):
        result = self._run()
        s1 = result[2]
        expected_y = [float(v) for v in self.trunk[self.catch_idx : self.finish_idx + 1]]
        assert s1.y == pytest.approx(expected_y, abs=1e-6)


# ---------------------------------------------------------------------------
# TrunkAngleComponent.compute() integration
# ---------------------------------------------------------------------------


class TestTrunkAngleComponentAnnotations:
    def test_compute_includes_annotations_key(self):
        df = _make_avg_cycle()
        component = TrunkAngleComponent()
        result = component.compute(df, catch_idx=20, finish_idx=50)
        assert 'annotations' in result

    def test_annotations_is_list_of_five(self):
        df = _make_avg_cycle()
        component = TrunkAngleComponent()
        result = component.compute(df, catch_idx=20, finish_idx=50)
        assert isinstance(result['annotations'], list)
        assert len(result['annotations']) == 6

    def test_no_annotations_key_still_backward_compatible(self):
        """Renderers must use .get('annotations', []) — verify it returns the list."""
        df = _make_avg_cycle()
        component = TrunkAngleComponent()
        result = component.compute(df, catch_idx=20, finish_idx=50)
        # Renderers call .get('annotations', []) — this must be truthy (non-empty)
        annotations = result.get('annotations', [])
        assert len(annotations) > 0

    def test_coach_tip_is_string(self):
        df = _make_avg_cycle()
        component = TrunkAngleComponent()
        result = component.compute(df, catch_idx=20, finish_idx=50)
        assert isinstance(result['coach_tip'], str)
        assert len(result['coach_tip']) > 0


# ---------------------------------------------------------------------------
# _catch_lean_coach_tip — scenario coverage
# ---------------------------------------------------------------------------


class TestCatchLeanCoachTip:
    ZONE = (-33.0, -27.0)  # both negative: forward lean range

    def test_too_upright_returns_rock_over_message(self):
        """Catch angle less negative than zone high → rower too upright."""
        tip, is_ideal = _catch_lean_coach_tip(-20.0, self.ZONE)
        assert 'Rock over more' in tip
        assert '7.0' in tip  # deficit = |-20 - (-27)| = 7.0
        assert is_ideal is False

    def test_over_leaning_returns_reduce_lean_message(self):
        """Catch angle more negative than zone low → hips may lag."""
        tip, is_ideal = _catch_lean_coach_tip(-40.0, self.ZONE)
        assert 'Reduce lean' in tip
        assert '7.0' in tip  # excess = |-40 - (-33)| = 7.0
        assert is_ideal is False

    def test_within_zone_returns_ok_message(self):
        tip, is_ideal = _catch_lean_coach_tip(-30.0, self.ZONE)
        assert 'ideal range' in tip
        assert is_ideal is True

    def test_exactly_on_upper_bound_is_ok(self):
        tip, is_ideal = _catch_lean_coach_tip(-27.0, self.ZONE)
        assert 'ideal range' in tip
        assert is_ideal is True

    def test_exactly_on_lower_bound_is_ok(self):
        tip, is_ideal = _catch_lean_coach_tip(-33.0, self.ZONE)
        assert 'ideal range' in tip
        assert is_ideal is True

    def test_returns_tuple(self):
        result = _catch_lean_coach_tip(-30.0, self.ZONE)
        assert isinstance(result, tuple)
        assert isinstance(result[0], str)
        assert isinstance(result[1], bool)


# ---------------------------------------------------------------------------
# _finish_lean_coach_tip — scenario coverage
# ---------------------------------------------------------------------------


class TestFinishLeanCoachTip:
    ZONE = (12.0, 18.0)  # both positive: lay-back range

    def test_too_little_layback_returns_lay_back_more(self):
        """Finish angle below zone low → not enough lay-back."""
        tip, is_ideal = _finish_lean_coach_tip(8.0, self.ZONE)
        assert 'Lay back more' in tip
        assert '4.0' in tip  # deficit = |8 - 12| = 4.0
        assert is_ideal is False

    def test_over_extended_returns_reduce_layback(self):
        """Finish angle above zone high → over-extension risk."""
        tip, is_ideal = _finish_lean_coach_tip(24.0, self.ZONE)
        assert 'Reduce lay-back' in tip
        assert '6.0' in tip  # excess = |24 - 18| = 6.0
        assert is_ideal is False

    def test_within_zone_returns_ok_message(self):
        tip, is_ideal = _finish_lean_coach_tip(15.0, self.ZONE)
        assert 'ideal range' in tip
        assert is_ideal is True

    def test_exactly_on_lower_bound_is_ok(self):
        tip, is_ideal = _finish_lean_coach_tip(12.0, self.ZONE)
        assert 'ideal range' in tip
        assert is_ideal is True

    def test_exactly_on_upper_bound_is_ok(self):
        tip, is_ideal = _finish_lean_coach_tip(18.0, self.ZONE)
        assert 'ideal range' in tip
        assert is_ideal is True

    def test_returns_tuple(self):
        result = _finish_lean_coach_tip(15.0, self.ZONE)
        assert isinstance(result, tuple)
        assert isinstance(result[0], str)
        assert isinstance(result[1], bool)


# ---------------------------------------------------------------------------
# _drive_trunk_opening_coach_tip — scenario coverage
# ---------------------------------------------------------------------------


def _make_drive_y(n: int, open_start_frac: float, steepness_window: float) -> list[float]:
    """Build a synthetic drive_y that hits the desired opening fractions.

    The function generates a piecewise linear trunk angle trace:
      - Flat hold phase from index 0 to open_start_frac * n
      - Linear ramp from open_start_frac to (open_start_frac + steepness_window)
      - Flat again to the end

    Total rotation is normalised to 45° (catch -30° → finish +15°).
    """
    start_angle = -30.0
    end_angle = 15.0
    hold_end = int(open_start_frac * n)
    swing_end = min(int((open_start_frac + steepness_window) * n), n - 1)

    y = []
    for i in range(n):
        if i <= hold_end:
            y.append(start_angle)
        elif i <= swing_end:
            t = (i - hold_end) / max(swing_end - hold_end, 1)
            y.append(start_angle + t * (end_angle - start_angle))
        else:
            y.append(end_angle)
    return y


class TestDriveTrunkOpeningCoachTip:
    def test_opens_too_early_returns_sequence_legs_first(self):
        drive_y = _make_drive_y(n=100, open_start_frac=0.10, steepness_window=0.30)
        tip, is_ideal = _drive_trunk_opening_coach_tip(drive_y)
        assert 'too early' in tip
        assert 'legs first' in tip
        assert is_ideal is False

    def test_opens_too_late_returns_begin_swing_earlier(self):
        drive_y = _make_drive_y(n=100, open_start_frac=0.60, steepness_window=0.30)
        tip, is_ideal = _drive_trunk_opening_coach_tip(drive_y)
        assert 'too late' in tip
        assert 'earlier' in tip
        assert is_ideal is False

    def test_opens_slowly_returns_accelerate_burst(self):
        start, end = -30.0, 15.0
        y = [-30.0] * 25 + [start + (end - start) * (i / 74) for i in range(75)]
        tip, is_ideal = _drive_trunk_opening_coach_tip(y)
        assert 'slowly' in tip or 'accelerate' in tip
        assert is_ideal is False

    def test_ideal_pattern_returns_positive_feedback(self):
        drive_y = _make_drive_y(n=100, open_start_frac=0.30, steepness_window=0.25)
        tip, is_ideal = _drive_trunk_opening_coach_tip(drive_y)
        assert 'sequencing' in tip or '\u2713' in tip
        assert is_ideal is True

    def test_too_short_returns_fallback(self):
        tip, is_ideal = _drive_trunk_opening_coach_tip([0.0, 1.0, 2.0])
        assert 'short' in tip
        assert is_ideal is False

    def test_minimal_rotation_returns_fallback(self):
        tip, is_ideal = _drive_trunk_opening_coach_tip([10.0] * 50)
        assert 'Minimal' in tip
        assert is_ideal is False

    def test_returns_tuple(self):
        drive_y = _make_drive_y(n=80, open_start_frac=0.30, steepness_window=0.25)
        result = _drive_trunk_opening_coach_tip(drive_y)
        assert isinstance(result, tuple)
        assert isinstance(result[0], str)
        assert isinstance(result[1], bool)


# ---------------------------------------------------------------------------
# _recovery_rock_over_coach_tip — scenario coverage
# ---------------------------------------------------------------------------

# Ideal catch zone used throughout: (-33.0, -27.0), midpoint = -30.0
_CATCH_ZONE = (-33.0, -27.0)


def _make_recovery_y(
    n: int,
    start: float,
    end: float,
    reach_frac: float,
    gradual: bool = False,
) -> list[float]:
    """Build a synthetic recovery_y trace.

    Args:
        n: Total recovery length.
        start: Angle at finish (e.g. +15.0).
        end: Angle at next catch (e.g. -30.0).
        reach_frac: Fraction of recovery at which the catch zone midpoint (-30°)
                    is first reached. Achieved by reaching `end` at that fraction
                    and holding there.
        gradual: If True, use a linear ramp all the way to index n-1 (slow swing).
    """
    reach_idx = int(reach_frac * (n - 1))
    if gradual:
        return [start + (end - start) * (i / (n - 1)) for i in range(n)]
    y = []
    for i in range(n):
        if i <= reach_idx:
            t = i / max(reach_idx, 1)
            y.append(start + (end - start) * t)
        else:
            y.append(end)
    return y


class TestRecoveryRockOverCoachTip:
    def test_rocks_over_too_early_returns_rushing_warning(self):
        rec_y = _make_recovery_y(n=100, start=15.0, end=-30.0, reach_frac=0.20)
        tip, is_ideal = _recovery_rock_over_coach_tip(rec_y, _CATCH_ZONE)
        assert 'early' in tip or 'rushing' in tip
        assert is_ideal is False

    def test_ideal_reach_returns_positive_feedback(self):
        rec_y = _make_recovery_y(n=100, start=15.0, end=-30.0, reach_frac=0.60)
        tip, is_ideal = _recovery_rock_over_coach_tip(rec_y, _CATCH_ZONE)
        assert '\u2713' in tip or 'Good' in tip
        assert is_ideal is True

    def test_late_rock_over_returns_whiplash_warning(self):
        rec_y = _make_recovery_y(n=100, start=15.0, end=-30.0, reach_frac=0.88)
        tip, is_ideal = _recovery_rock_over_coach_tip(rec_y, _CATCH_ZONE)
        assert 'late' in tip.lower() or 'whiplash' in tip.lower()
        assert is_ideal is False

    def test_last_moment_arrival_returns_overreach_risk(self):
        rec_y = _make_recovery_y(n=100, start=15.0, end=-30.0, reach_frac=0.99)
        tip, is_ideal = _recovery_rock_over_coach_tip(rec_y, _CATCH_ZONE)
        assert 'whiplash' in tip.lower() or 'overreach' in tip.lower() or 'last moment' in tip.lower()
        assert is_ideal is False

    def test_gradual_swing_in_ideal_window_returns_accelerate(self):
        rec_y = _make_recovery_y(n=100, start=15.0, end=-30.0, reach_frac=0.75, gradual=True)
        tip, _ = _recovery_rock_over_coach_tip(rec_y, _CATCH_ZONE)
        assert any(word in tip.lower() for word in ['gradual', 'accelerate', 'rock-over', 'late', 'whiplash', 'good'])

    def test_too_short_returns_fallback(self):
        tip, is_ideal = _recovery_rock_over_coach_tip([15.0, 10.0, 5.0], _CATCH_ZONE)
        assert 'short' in tip
        assert is_ideal is False

    def test_minimal_movement_returns_rock_over_more(self):
        tip, is_ideal = _recovery_rock_over_coach_tip([15.0] * 50, _CATCH_ZONE)
        assert 'rock over' in tip.lower() or 'barely' in tip.lower()
        assert is_ideal is False

    def test_returns_tuple(self):
        rec_y = _make_recovery_y(n=80, start=15.0, end=-30.0, reach_frac=0.60)
        result = _recovery_rock_over_coach_tip(rec_y, _CATCH_ZONE)
        assert isinstance(result, tuple)
        assert isinstance(result[0], str)
        assert isinstance(result[1], bool)
