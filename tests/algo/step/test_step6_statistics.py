import numpy as np
import pandas as pd

from rowing_catch.algo.step.step6_statistics import _compute_phase_volume, step6_statistics

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_realistic_cycle(
    pre_catch_samples: int = 10,
    drive_samples: int = 20,
    recovery_samples: int = 40,
    sample_rate_hz: float = 25.0,
) -> pd.DataFrame:
    """Build a synthetic cycle with a pre-catch window, mirroring step4 output.

    Seat_X is at its global minimum at index `pre_catch_samples` (the real catch).
    Handle_X is high at the start (tail of the previous draw), low at the catch,
    peaks at the finish, and returns forward during recovery.

    This is the shape that exposed the catch_idx=0 bug: the old code would look
    for the Handle_X peak starting from index 0 and find the high pre-catch handle
    values as the "finish", inflating drive_dur and collapsing rec_dur.
    """
    dt = 1.0 / sample_rate_hz
    n = pre_catch_samples + drive_samples + recovery_samples + 1

    t = np.arange(n) * dt
    catch_pos = pre_catch_samples

    # Seat_X: global minimum at catch_pos
    seat_x = np.empty(n)
    seat_x[:catch_pos] = np.linspace(50.0, 5.0, catch_pos)
    seat_x[catch_pos] = 0.0
    seat_x[catch_pos : catch_pos + drive_samples] = np.linspace(0.0, 80.0, drive_samples)
    seat_x[catch_pos + drive_samples :] = np.linspace(80.0, 0.0, recovery_samples + 1)

    # Handle_X: high pre-catch (tail of previous draw), peaks at finish
    finish_pos = catch_pos + drive_samples
    handle_x = np.empty(n)
    handle_x[:catch_pos] = np.linspace(200.0, 50.0, catch_pos)  # previous draw tail
    handle_x[catch_pos] = 10.0
    handle_x[catch_pos:finish_pos] = np.linspace(10.0, 250.0, drive_samples)
    handle_x[finish_pos:] = np.linspace(250.0, 10.0, recovery_samples + 1)

    return pd.DataFrame(
        {
            'Time': t,
            'Seat_X_Smooth': seat_x,
            'Handle_X_Smooth': handle_x,
        }
    )


def test_step6_statistics_basic():
    """Test statistics computation with 3 identical clean cycles."""
    # Create 3 identical cycles
    # 51 samples, dt = 0.02s (50 Hz)
    # Total duration = 50 * 0.02 = 1.0s
    t = np.linspace(0, 1.0, 51)
    # Seat moves from 0 to 100 and back to 0.
    # Catch at 0, Finish at 25, Total length 51 samples.
    seat_x = 50 - 50 * np.cos(2 * np.pi * t)

    df = pd.DataFrame(
        {
            'Time': t,
            'Seat_X_Smooth': seat_x,
            'Handle_X_Smooth': seat_x * 1.5,
            'Shoulder_X_Smooth': seat_x * 1.2,
            'Handle_X_Vel': np.diff(seat_x * 1.5, prepend=seat_x[0] * 1.5),
            'Seat_X_Vel': np.diff(seat_x, prepend=seat_x[0]),
            'Shoulder_X_Vel': np.diff(seat_x * 1.2, prepend=seat_x[0] * 1.2),
        }
    )

    cycles = [df.copy(), df.copy(), df.copy()]
    min_length = 51
    catch_idx = 0
    finish_idx = 25

    stats = step6_statistics(cycles, min_length, catch_idx, finish_idx, df)

    assert stats['cv_length'] == 0.0  # Identical cycles
    # Note: drive_len is now computed from per-cycle ratios (using time-based ratio),
    # not from the averaged cycle's finish_idx. For these identical cycles with
    # continuous time, the ratio is 0.5 (50% drive), so drive_len = round(0.5 * 51) = 26
    assert stats['drive_len'] == 26
    assert stats['recovery_len'] == 25  # 51 - 26 = 25
    assert stats['mean_duration'] == 51.0

    # Temporal checks (from former Step 7)
    assert np.isclose(stats['sample_rate_hz'], 50.0)
    assert np.isclose(stats['cycle_duration_s'], 1.0)
    assert np.isclose(stats['drive_duration_s'], 0.5)
    assert np.isclose(stats['stroke_rate_spm'], 60.0)


def test_step6_statistics_no_time():
    """Test statistics without a Time column."""
    df = pd.DataFrame(
        {
            'Seat_X_Smooth': np.zeros(10),
            'Handle_X_Smooth': np.zeros(10),
            'Shoulder_X_Smooth': np.zeros(10),
        }
    )
    stats = step6_statistics([df, df, df], 10, 0, 5, df)

    assert stats['sample_rate_hz'] is None
    assert stats['stroke_rate_spm'] is None


def test_compute_phase_volume():
    """Test the internal volume integration logic."""
    # positions: 0, 10, 20, 30
    # times: 0, 1, 2, 3
    # diffs: 10, 10, 10. dts: 1, 1, 1.
    # volume = 10*1 + 10*1 + 10*1 = 30.
    pos = np.array([0, 10, 20, 30], dtype=float)
    times = np.array([0, 1, 2, 3], dtype=float)

    vol = _compute_phase_volume(pos, times, 0, 4)
    assert vol == 30.0

    # Sinusoidal data
    t = np.linspace(0, 2, 101)
    seat_x = 50 + 50 * np.sin(2 * np.pi * t)
    # 0 to 1 second is drive (idx 0-50), 1 to 2 is recovery (50-100)
    # Total points 101.
    # We expect positive volume for both.
    vol_sin = _compute_phase_volume(seat_x, t, 0, 51)
    assert vol_sin > 0

    # Without times (defaults to dt=1)
    vol_no_times = _compute_phase_volume(pos, None, 0, 4)
    assert vol_no_times == 30.0


# ---------------------------------------------------------------------------
# Tests for the pre-catch-window bug (catch_idx=0 regression)
# ---------------------------------------------------------------------------


class TestStep6StatisticsWithPreCatchWindow:
    """The existing test_step6_statistics_basic accidentally avoided the bug because
    its synthetic Seat_X minimum is at index 0 (no pre-catch window).  These tests
    use cycles that include a pre-catch window, which is what step4 always produces
    in practice.  Under the OLD code (catch_idx=0 hardcoded), every test here would
    fail because drive_dur ≈ full cycle and ratio >> 1.
    """

    def _build_cycles_and_avg(
        self,
        pre: int = 10,
        drive: int = 20,
        recovery: int = 40,
        hz: float = 25.0,
        n_cycles: int = 3,
    ):
        """Return (cycles, avg_cycle, catch_idx_on_avg, finish_idx_on_avg, min_length)."""
        cycles = [_make_realistic_cycle(pre, drive, recovery, hz) for _ in range(n_cycles)]
        min_length = min(len(c) for c in cycles)
        # avg_cycle: same shape as any cycle (they're identical here)
        avg_cycle = cycles[0].copy()
        # On the avg cycle the catch is also at 'pre' and finish at 'pre + drive'
        catch_idx_avg = pre
        finish_idx_avg = pre + drive
        return cycles, avg_cycle, catch_idx_avg, finish_idx_avg, min_length

    def test_per_cycle_ratio_is_below_one(self):
        """drive:recovery ratio must be < 1 (drive is always shorter than recovery)."""
        cycles, avg, ci, fi, ml = self._build_cycles_and_avg(pre=10, drive=20, recovery=40)
        stats = step6_statistics(cycles, ml, ci, fi, avg)
        ratio = stats['avg_drive_recovery_ratio']
        assert ratio < 1.0, f'ratio={ratio:.3f} ≥ 1 — old catch_idx=0 bug may be back'
        assert ratio > 0.0

    def test_per_cycle_ratio_regression_old_bug_would_give_ratio_above_one(self):
        """Explicit regression: with pre_catch=10, drive=20, recovery=40,
        the old code (catch_idx=0) would compute:
            drive_dur ≈ t[finish] - t[0]  (includes pre-catch window)
            rec_dur   ≈ t[-1] - t[finish] (only true recovery)
        which gives ratio >> 1.  The fix must produce ratio < 1.
        """
        cycles, avg, ci, fi, ml = self._build_cycles_and_avg(pre=10, drive=20, recovery=40, hz=25.0)
        stats = step6_statistics(cycles, ml, ci, fi, avg)
        assert stats['avg_drive_recovery_ratio'] < 1.0

    def test_cycle_details_spm_is_correct(self):
        """SPM in cycle_details should reflect catch-to-next-catch, not full cycle."""
        pre, drive, recovery, hz = 10, 20, 40, 25.0
        expected_stroke_period = (drive + recovery) / hz  # seconds, catch-to-next-catch
        expected_spm = 60.0 / expected_stroke_period

        cycles, avg, ci, fi, ml = self._build_cycles_and_avg(pre, drive, recovery, hz)
        stats = step6_statistics(cycles, ml, ci, fi, avg)

        for detail in stats['cycle_details']:
            if 'spm' in detail:
                assert abs(detail['spm'] - expected_spm) < 1.0, f'SPM={detail["spm"]:.1f} far from expected {expected_spm:.1f}'

    def test_cycle_details_ratio_stored_per_cycle(self):
        """All cycle_details entries should have a drive_recovery_ratio < 1."""
        cycles, avg, ci, fi, ml = self._build_cycles_and_avg(pre=10, drive=15, recovery=45)
        stats = step6_statistics(cycles, ml, ci, fi, avg)
        ratios = [d['drive_recovery_ratio'] for d in stats['cycle_details'] if 'drive_recovery_ratio' in d]
        assert len(ratios) > 0, 'No per-cycle ratios recorded'
        for r in ratios:
            assert r < 1.0, f'Per-cycle ratio={r:.3f} ≥ 1'

    def test_drive_len_plus_recovery_len_equals_min_length(self):
        """drive_len + recovery_len must always equal min_length."""
        cycles, avg, ci, fi, ml = self._build_cycles_and_avg()
        stats = step6_statistics(cycles, ml, ci, fi, avg)
        assert stats['drive_len'] + stats['recovery_len'] == ml

    def test_no_pre_catch_window_is_unchanged(self):
        """With pre=0 (catch at index 0), the fix must give the same answer as the
        old code — catching that the argmin path still works correctly."""
        cycles, avg, ci, fi, ml = self._build_cycles_and_avg(pre=0, drive=20, recovery=40)
        stats = step6_statistics(cycles, ml, ci, fi, avg)
        ratio = stats['avg_drive_recovery_ratio']
        expected = 20 / 40  # drive/recovery = 0.5
        assert abs(ratio - expected) < 0.1, f'ratio={ratio:.3f}, expected≈{expected:.3f}'
