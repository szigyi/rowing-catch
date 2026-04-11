"""Tests for rhythm consistency transform — specifically the drive phase % calculation.

The key bug this covers: per-cycle DataFrames include a pre_catch_window of samples
*before* the actual catch. Using catch_idx=0 caused the finish of the *previous*
stroke to be detected as the current stroke's finish, yielding drive phase percentages
above 50% (physically impossible for normal rowing where drive < recovery).

The fix: locate the real catch in each cycle via a search in the first 35% of the
cycle (where the catch always lives), then compute drive/recovery durations from
that point forward to t[-1] (the next catch).
"""

import numpy as np
import pandas as pd

from rowing_catch.plot_transformer.rhythm.drive_recovery_balance_transformer import (
    _find_catch_idx_in_cycle,
    compute_drive_recovery_balance,
    compute_rhythm_spread,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_cycle(
    pre_catch_samples: int = 10,
    drive_samples: int = 20,
    recovery_samples: int = 40,
    sample_rate_hz: float = 25.0,
) -> pd.DataFrame:
    """Build a synthetic per-cycle DataFrame that mirrors what step4 produces.

    Layout:
        [0 .. pre_catch_samples-1]                  — recovery tail of previous stroke
        [pre_catch_samples]                         — catch (Seat_X minimum)
        [pre_catch_samples .. pre_catch_samples+drive_samples]  — drive phase
        [pre_catch_samples+drive_samples .. end]    — recovery phase, ends at next catch

    Seat_X goes:
        • pre-catch window: linear decrease toward the minimum (approaching catch)
        • catch: global minimum
        • drive: seat moves backward (increases)
        • recovery: seat moves forward again (decreases back to next catch level)

    Handle_X goes:
        • pre-catch: high (tail of previous draw)
        • catch: at seat level (compressed)
        • drive: handle pulled back (maximum at finish)
        • recovery: handle returns forward
    """
    dt = 1.0 / sample_rate_hz
    n = pre_catch_samples + drive_samples + recovery_samples + 1  # +1 = next catch sample

    t = np.arange(n) * dt

    # Seat_X: minimum at catch index, symmetric-ish around catch
    catch_pos = pre_catch_samples
    seat_x = np.zeros(n)
    # Pre-catch: seat moving toward catch (decreasing to 0)
    seat_x[:catch_pos] = np.linspace(50.0, 5.0, catch_pos)
    seat_x[catch_pos] = 0.0  # global minimum — the catch
    # Drive: seat moves back
    seat_x[catch_pos : catch_pos + drive_samples] = np.linspace(0.0, 80.0, drive_samples)
    # Recovery: seat returns forward toward next catch
    seat_x[catch_pos + drive_samples :] = np.linspace(80.0, 0.0, recovery_samples + 1)

    # Handle_X: high at start (previous finish), low at catch, peaks at finish
    handle_x = np.zeros(n)
    handle_x[:catch_pos] = np.linspace(200.0, 50.0, catch_pos)  # tail of previous draw
    handle_x[catch_pos] = 10.0  # catch — handle close to seat
    finish_pos = catch_pos + drive_samples
    handle_x[catch_pos:finish_pos] = np.linspace(10.0, 250.0, drive_samples)  # draw
    handle_x[finish_pos:] = np.linspace(250.0, 10.0, recovery_samples + 1)  # recovery

    df = pd.DataFrame(
        {
            'Time': t,
            'Seat_X_Smooth': seat_x,
            'Handle_X_Smooth': handle_x,
        }
    )
    df.index.name = 'Cycle_Index'
    return df


# ---------------------------------------------------------------------------
# _find_catch_idx_in_cycle
# ---------------------------------------------------------------------------


class TestFindCatchIdxInCycle:
    def test_returns_min_in_first_portion_of_cycle(self):
        df = _make_cycle(pre_catch_samples=10)
        idx = _find_catch_idx_in_cycle(df)
        assert idx == 10  # catch is at sample 10

    def test_fallback_without_seat_x_smooth(self):
        df = pd.DataFrame({'Handle_X_Smooth': [1.0, 2.0, 3.0]})
        assert _find_catch_idx_in_cycle(df) == 0

    def test_different_pre_catch_window(self):
        df = _make_cycle(pre_catch_samples=5)
        assert _find_catch_idx_in_cycle(df) == 5

    def test_no_pre_catch_window(self):
        df = _make_cycle(pre_catch_samples=0)
        assert _find_catch_idx_in_cycle(df) == 0

    def test_ignores_global_minimum_at_end_of_cycle(self):
        """Regression: global argmin returns the last index when the next catch
        (end of cycle) is lower than the current catch.  The fix restricts the
        search to the first 35% of the cycle."""
        df = _make_cycle(pre_catch_samples=10, drive_samples=20, recovery_samples=40)
        # Make the last sample (= next catch) the global minimum
        df = df.copy()
        df.loc[df.index[-1], 'Seat_X_Smooth'] = -999.0
        idx = _find_catch_idx_in_cycle(df)
        # Must find the catch near the start, NOT the end
        assert idx < len(df) // 2, f'catch_idx={idx} looks like end-of-cycle (next catch)'
        assert idx == 10


# ---------------------------------------------------------------------------
# compute_rhythm_spread — ratio validity
# ---------------------------------------------------------------------------


class TestComputeRhythmSpread:
    def test_drive_pct_is_below_50_for_standard_stroke(self):
        """Drive phase must be < 50% for any realistic stroke (drive < recovery)."""
        cycle = _make_cycle(pre_catch_samples=10, drive_samples=20, recovery_samples=40)
        result = compute_rhythm_spread([cycle])
        assert len(result) == 1
        pct = result[0]['Drive_Pct']
        assert pct < 50.0, f'Expected Drive_Pct < 50, got {pct}'
        assert pct > 0.0, f'Expected Drive_Pct > 0, got {pct}'

    def test_drive_pct_matches_expected_value(self):
        """Drive_Pct must equal drive/(drive+recovery)*100 for clean synthetic data."""
        cycle = _make_cycle(pre_catch_samples=10, drive_samples=20, recovery_samples=40)
        result = compute_rhythm_spread([cycle])
        pct = result[0]['Drive_Pct']
        expected = 20 / (20 + 40) * 100  # 33.3%
        assert abs(pct - expected) < 2.0, f'Drive_Pct={pct:.1f}%, expected≈{expected:.1f}%'

    def test_drive_pct_approaches_50_for_equal_drive_recovery(self):
        """When drive == recovery, Drive_Pct should be close to 50%."""
        cycle = _make_cycle(pre_catch_samples=10, drive_samples=30, recovery_samples=30)
        result = compute_rhythm_spread([cycle])
        pct = result[0]['Drive_Pct']
        assert abs(pct - 50.0) < 5.0, f'Expected Drive_Pct ≈ 50%, got {pct}'

    def test_drive_pct_not_above_50_for_drive_shorter_than_recovery(self):
        """Drive_Pct must never exceed 50% when drive < recovery."""
        cycle = _make_cycle(pre_catch_samples=10, drive_samples=15, recovery_samples=45)
        result = compute_rhythm_spread([cycle])
        assert result[0]['Drive_Pct'] < 50.0

    def test_spm_is_plausible_for_36_spm(self):
        """At 36 SPM the stroke period is 60/36 ≈ 1.667 s."""
        sample_rate = 25.0
        cycle = _make_cycle(
            pre_catch_samples=10,
            drive_samples=12,
            recovery_samples=30,
            sample_rate_hz=sample_rate,
        )
        result = compute_rhythm_spread([cycle])
        spm = result[0]['SPM']
        assert 30 < spm < 45, f'SPM out of expected range: {spm}'

    def test_drive_plus_recovery_equals_stroke_duration(self):
        """Drive (s) + Recovery (s) must sum to the catch-to-next-catch duration."""
        pre = 10
        drive = 20
        recovery = 40
        sample_rate = 25.0
        cycle = _make_cycle(pre, drive, recovery, sample_rate)
        result = compute_rhythm_spread([cycle])
        row = result[0]
        expected_duration = (drive + recovery) / sample_rate
        actual_sum = row['Drive (s)'] + row['Recovery (s)']
        assert abs(actual_sum - expected_duration) < 0.01, (
            f'Drive+Recovery={actual_sum:.3f} != expected stroke duration {expected_duration:.3f}'
        )

    def test_multiple_cycles_all_valid_drive_pct(self):
        """All cycles should produce physically valid drive percentages."""
        cycles = [
            _make_cycle(pre_catch_samples=10, drive_samples=d, recovery_samples=r) for d, r in [(15, 45), (20, 40), (18, 42)]
        ]
        result = compute_rhythm_spread(cycles)
        assert len(result) == 3
        for row in result:
            assert 0 < row['Drive_Pct'] < 50.0, f'Invalid Drive_Pct: {row["Drive_Pct"]}'

    def test_empty_cycles_returns_empty_list(self):
        result = compute_rhythm_spread([])
        assert result == []

    def test_cycle_without_time_column_is_skipped(self):
        df = pd.DataFrame({'Seat_X_Smooth': [0.0, 1.0, 2.0]})
        result = compute_rhythm_spread([df])
        assert result == []

    def test_cycle_numbers_are_one_based(self):
        cycles = [_make_cycle() for _ in range(3)]
        result = compute_rhythm_spread(cycles)
        assert [r['Cycle'] for r in result] == [1, 2, 3]

    def test_old_bug_catch_idx_zero_would_give_drive_pct_above_50(self):
        """Regression: the old code used catch_idx=0, which would pick up the
        high Handle_X at the start of the pre-catch window as the 'finish',
        making drive_dur ≈ full cycle and Drive_Pct far above 50%.
        With the fix, Drive_Pct must be < 50%.
        """
        cycle = _make_cycle(pre_catch_samples=10, drive_samples=20, recovery_samples=40)
        result = compute_rhythm_spread([cycle])
        pct = result[0]['Drive_Pct']
        assert pct < 50.0, f'Regression: Drive_Pct={pct:.1f}% ≥ 50% suggests the old catch_idx=0 bug is back'

    def test_no_ratio_dr_key_in_output(self):
        """Ratio_DR must no longer appear in output — Drive_Pct is the authoritative field."""
        cycle = _make_cycle()
        result = compute_rhythm_spread([cycle])
        assert 'Ratio_DR' not in result[0], 'Ratio_DR should have been removed; use Drive_Pct'
        assert 'Drive_Pct' in result[0]

    def test_drive_pct_is_in_percent_scale(self):
        """Drive_Pct must be in 0–100 scale, not 0–1."""
        cycle = _make_cycle(pre_catch_samples=10, drive_samples=20, recovery_samples=40)
        result = compute_rhythm_spread([cycle])
        pct = result[0]['Drive_Pct']
        assert pct > 1.0, f'Drive_Pct={pct} looks like a 0–1 fraction, not a percentage'


# ---------------------------------------------------------------------------
# compute_drive_recovery_balance — percentage denominator fix
# ---------------------------------------------------------------------------


class TestComputeDriveRecoveryBalance:
    """The drive and recovery percentages must be relative to the catch-to-end
    span of the averaged cycle, NOT to the full min_length (which includes the
    pre-catch window prepended by step4).

    Old bug: drive_pct = drive_len / min_length
             recovery_len = min_length - drive_len  (always sums to min_length, ignoring pre-catch)

    Fix:     stroke_len = min_length - catch_idx
             drive_pct = drive_len / stroke_len
             recovery_len = min_length - finish_idx  (samples from finish to end)
    """

    def test_drive_plus_recovery_pct_equals_100(self):
        """drive_pct + rec_pct must always equal 100%."""
        result = compute_drive_recovery_balance([], min_length=71, catch_idx=10, finish_idx=30)
        assert abs(result['drive_pct'] + result['rec_pct'] - 100.0) < 0.01

    def test_no_pre_catch_window_gives_expected_pct(self):
        """With catch at 0, percentages reduce to the simple drive/total ratio."""
        # catch=0, finish=20, total=60 → drive=20, rec=40, drive_pct = 20/60 = 33.3%
        result = compute_drive_recovery_balance([], min_length=60, catch_idx=0, finish_idx=20)
        expected_drive_pct = 20 / 60 * 100
        assert abs(result['drive_pct'] - expected_drive_pct) < 0.01

    def test_pre_catch_window_excluded_from_denominator(self):
        """With a 10-sample pre-catch window the denominator must be min_length - catch_idx,
        not min_length.  Old code: drive_pct = 20/71 ≈ 28.2%.
        Correct:       drive_pct = 20/61 ≈ 32.8%.
        """
        # catch=10, finish=30, min_length=71 → stroke_len=61, drive=20
        result = compute_drive_recovery_balance([], min_length=71, catch_idx=10, finish_idx=30)
        correct_drive_pct = 20 / 61 * 100
        wrong_drive_pct = 20 / 71 * 100
        assert abs(result['drive_pct'] - correct_drive_pct) < 0.1, (
            f'drive_pct={result["drive_pct"]:.2f}%, expected {correct_drive_pct:.2f}%'
        )
        assert abs(result['drive_pct'] - wrong_drive_pct) > 1.0, (
            'drive_pct matches the old wrong value — pre-catch denominator bug may be back'
        )

    def test_recovery_pct_is_finish_to_end(self):
        """recovery_pct must count samples from finish to min_length (not min_length - drive_len)."""
        # catch=10, finish=30, min_length=71 → recovery = 71-30 = 41 samples, rec_pct = 41/61
        result = compute_drive_recovery_balance([], min_length=71, catch_idx=10, finish_idx=30)
        correct_rec_pct = 41 / 61 * 100
        assert abs(result['rec_pct'] - correct_rec_pct) < 0.1

    def test_drive_pct_below_50_for_typical_rowing(self):
        """Drive phase is typically < 50% of the stroke for recreational-to-elite rowing."""
        # Typical 36 SPM: ~24 drive samples, ~40 recovery, pre-catch=10, total=74
        result = compute_drive_recovery_balance([], min_length=74, catch_idx=10, finish_idx=34)
        assert result['drive_pct'] < 50.0, f'drive_pct={result["drive_pct"]:.1f}% unexpectedly ≥ 50%'
        assert result['drive_pct'] > 10.0

    def test_ideal_drive_pct_is_percentage_not_ratio(self):
        """ideal_drive_pct must be in 0–100 scale. ideal_ratio must not be in the output."""
        result = compute_drive_recovery_balance([], min_length=71, catch_idx=10, finish_idx=30)
        assert 'ideal_ratio' not in result, 'ideal_ratio should be removed; use ideal_drive_pct'
        assert 20 < result['ideal_drive_pct'] < 60, (
            f'ideal_drive_pct={result["ideal_drive_pct"]:.1f} — expected a percentage in 20–60%'
        )
