"""Tests for rhythm consistency coaching tip functions.

All tip functions are pure functions returning (str, bool) — fully testable
without any UI or DataFrame dependencies.
"""

import pytest

from rowing_catch.plot_transformer.rhythm.tip.rhythm_consistency_tips import (
    DRIVE_PCT_ACCEPTABLE_THRESHOLD,
    DRIVE_STD_TIGHT_THRESHOLD,
    SPM_STD_CONSISTENT_THRESHOLD,
    drive_pct_spread_coach_tip,
    drive_pct_vs_ideal_coach_tip,
    spm_spread_coach_tip,
)

# ---------------------------------------------------------------------------
# drive_pct_vs_ideal_coach_tip — [P1]
# ---------------------------------------------------------------------------


class TestDrivePctVsIdealCoachTip:
    """Tests for the mean drive% vs ideal curve tip function."""

    def test_at_ideal_is_ideal(self):
        """Exactly at the ideal benchmark → is_ideal=True."""
        _, is_ideal = drive_pct_vs_ideal_coach_tip(
            mean_drive_pct=40.0,
            ideal_drive_pct=40.0,
            mean_spm=28.0,
        )
        assert is_ideal is True

    def test_below_ideal_is_ideal(self):
        """Drive% below ideal (shorter drive) → is_ideal=True."""
        _, is_ideal = drive_pct_vs_ideal_coach_tip(
            mean_drive_pct=38.0,
            ideal_drive_pct=40.0,
            mean_spm=28.0,
        )
        assert is_ideal is True

    def test_below_ideal_contains_checkmark(self):
        """Cue text for ideal case must contain ✓."""
        tip, _ = drive_pct_vs_ideal_coach_tip(
            mean_drive_pct=38.0,
            ideal_drive_pct=40.0,
            mean_spm=28.0,
        )
        assert '✓' in tip

    def test_acceptable_above_is_not_ideal(self):
        """Drive% just above ideal within ACCEPTABLE threshold → is_ideal=False."""
        diff = DRIVE_PCT_ACCEPTABLE_THRESHOLD - 0.1  # e.g. 1.9%
        _, is_ideal = drive_pct_vs_ideal_coach_tip(
            mean_drive_pct=40.0 + diff,
            ideal_drive_pct=40.0,
            mean_spm=28.0,
        )
        assert is_ideal is False

    def test_acceptable_boundary_is_not_ideal(self):
        """Exactly at the acceptable threshold → still is_ideal=False."""
        _, is_ideal = drive_pct_vs_ideal_coach_tip(
            mean_drive_pct=40.0 + DRIVE_PCT_ACCEPTABLE_THRESHOLD,
            ideal_drive_pct=40.0,
            mean_spm=28.0,
        )
        assert is_ideal is False

    def test_above_acceptable_threshold_is_not_ideal(self):
        """Drive% well above ideal → is_ideal=False."""
        _, is_ideal = drive_pct_vs_ideal_coach_tip(
            mean_drive_pct=40.0 + DRIVE_PCT_ACCEPTABLE_THRESHOLD + 1.0,
            ideal_drive_pct=40.0,
            mean_spm=28.0,
        )
        assert is_ideal is False

    def test_needs_work_tip_mentions_drive_and_recovery(self):
        """'Needs work' cue must mention both speeding the drive and slowing the recovery."""
        tip, _ = drive_pct_vs_ideal_coach_tip(
            mean_drive_pct=46.0,
            ideal_drive_pct=40.0,
            mean_spm=28.0,
        )
        tip_lower = tip.lower()
        assert 'drive' in tip_lower
        assert 'recovery' in tip_lower

    def test_cue_contains_actual_drive_pct(self):
        """Cue text must include the rower's actual drive% value."""
        tip, _ = drive_pct_vs_ideal_coach_tip(
            mean_drive_pct=43.7,
            ideal_drive_pct=40.0,
            mean_spm=28.0,
        )
        assert '43.7' in tip

    def test_cue_contains_ideal_drive_pct(self):
        """Cue text must include the ideal drive% value."""
        tip, _ = drive_pct_vs_ideal_coach_tip(
            mean_drive_pct=43.0,
            ideal_drive_pct=40.0,
            mean_spm=28.0,
        )
        assert '40.0' in tip

    def test_cue_contains_mean_spm(self):
        """Cue text must include the rower's mean SPM."""
        tip, _ = drive_pct_vs_ideal_coach_tip(
            mean_drive_pct=43.0,
            ideal_drive_pct=40.0,
            mean_spm=32.5,
        )
        assert '32.5' in tip

    def test_returns_tuple_of_str_and_bool(self):
        """Return type must be (str, bool) for all branches."""
        for mean_pct, ideal_pct in [(38.0, 40.0), (41.0, 40.0), (46.0, 40.0)]:
            result = drive_pct_vs_ideal_coach_tip(mean_pct, ideal_pct, 28.0)
            assert isinstance(result, tuple) and len(result) == 2
            assert isinstance(result[0], str)
            assert isinstance(result[1], bool)


# ---------------------------------------------------------------------------
# drive_pct_spread_coach_tip — [Z1]
# ---------------------------------------------------------------------------


class TestDrivePctSpreadCoachTip:
    """Tests for the drive% vertical spread (consistency) tip function."""

    def test_zero_std_is_ideal(self):
        """Perfect consistency (std=0) → is_ideal=True."""
        _, is_ideal = drive_pct_spread_coach_tip(0.0)
        assert is_ideal is True

    def test_at_threshold_is_ideal(self):
        """Spread exactly at threshold → is_ideal=True (≤ threshold)."""
        _, is_ideal = drive_pct_spread_coach_tip(DRIVE_STD_TIGHT_THRESHOLD)
        assert is_ideal is True

    def test_just_above_threshold_is_not_ideal(self):
        """Spread just above threshold → is_ideal=False."""
        _, is_ideal = drive_pct_spread_coach_tip(DRIVE_STD_TIGHT_THRESHOLD + 0.01)
        assert is_ideal is False

    def test_high_spread_is_not_ideal(self):
        """Large spread → is_ideal=False."""
        _, is_ideal = drive_pct_spread_coach_tip(10.0)
        assert is_ideal is False

    def test_ideal_tip_contains_checkmark(self):
        """Ideal cue must contain ✓."""
        tip, _ = drive_pct_spread_coach_tip(1.5)
        assert '✓' in tip

    def test_non_ideal_tip_mentions_muscle_feeling(self):
        """Non-ideal cue must reference the correction cue (muscle feeling / identical)."""
        tip, _ = drive_pct_spread_coach_tip(5.0)
        tip_lower = tip.lower()
        assert 'muscle' in tip_lower or 'identical' in tip_lower or 'feeling' in tip_lower

    def test_cue_contains_std_value(self):
        """Cue text must include the actual std value."""
        tip, _ = drive_pct_spread_coach_tip(2.7)
        assert '2.7' in tip

    def test_returns_tuple_of_str_and_bool(self):
        """Return type must always be (str, bool)."""
        for std in [0.0, DRIVE_STD_TIGHT_THRESHOLD, 8.0]:
            result = drive_pct_spread_coach_tip(std)
            assert isinstance(result, tuple) and len(result) == 2
            assert isinstance(result[0], str)
            assert isinstance(result[1], bool)


# ---------------------------------------------------------------------------
# spm_spread_coach_tip — [Z2]
# ---------------------------------------------------------------------------


class TestSpmSpreadCoachTip:
    """Tests for the SPM horizontal spread (rate consistency) tip function."""

    def test_zero_std_is_ideal(self):
        """No rate variation → is_ideal=True."""
        _, is_ideal = spm_spread_coach_tip(0.0)
        assert is_ideal is True

    def test_at_threshold_is_ideal(self):
        """Spread exactly at threshold → is_ideal=True (≤ threshold)."""
        _, is_ideal = spm_spread_coach_tip(SPM_STD_CONSISTENT_THRESHOLD)
        assert is_ideal is True

    def test_just_above_threshold_is_not_ideal(self):
        """Spread just above threshold → is_ideal=False."""
        _, is_ideal = spm_spread_coach_tip(SPM_STD_CONSISTENT_THRESHOLD + 0.01)
        assert is_ideal is False

    def test_high_spread_is_not_ideal(self):
        """Large SPM variation → is_ideal=False."""
        _, is_ideal = spm_spread_coach_tip(6.0)
        assert is_ideal is False

    def test_ideal_tip_contains_checkmark(self):
        """Ideal cue must contain ✓."""
        tip, _ = spm_spread_coach_tip(1.0)
        assert '✓' in tip

    def test_non_ideal_tip_mentions_rhythm_or_movements(self):
        """Non-ideal cue must reference the correction (rhythm / movements / steady)."""
        tip, _ = spm_spread_coach_tip(4.0)
        tip_lower = tip.lower()
        assert any(word in tip_lower for word in ('rhythm', 'movements', 'steady', 'rate'))

    def test_cue_contains_std_value(self):
        """Cue text must include the actual std value."""
        tip, _ = spm_spread_coach_tip(3.2)
        assert '3.2' in tip

    def test_returns_tuple_of_str_and_bool(self):
        """Return type must always be (str, bool)."""
        for std in [0.0, SPM_STD_CONSISTENT_THRESHOLD, 5.0]:
            result = spm_spread_coach_tip(std)
            assert isinstance(result, tuple) and len(result) == 2
            assert isinstance(result[0], str)
            assert isinstance(result[1], bool)


# ---------------------------------------------------------------------------
# Threshold constants sanity
# ---------------------------------------------------------------------------


class TestThresholdConstants:
    def test_drive_pct_acceptable_threshold_is_positive(self):
        assert DRIVE_PCT_ACCEPTABLE_THRESHOLD > 0

    def test_drive_std_tight_threshold_is_positive(self):
        assert DRIVE_STD_TIGHT_THRESHOLD > 0

    def test_spm_std_consistent_threshold_is_positive(self):
        assert SPM_STD_CONSISTENT_THRESHOLD > 0

    def test_expected_threshold_values(self):
        """Guard against accidental threshold changes."""
        assert DRIVE_PCT_ACCEPTABLE_THRESHOLD == pytest.approx(2.0)
        assert DRIVE_STD_TIGHT_THRESHOLD == pytest.approx(3.0)
        assert SPM_STD_CONSISTENT_THRESHOLD == pytest.approx(2.0)
