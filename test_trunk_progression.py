import numpy as np

from rowing_catch.algo.scenarios import _trunk_angle_legs_first_progression


def test_recovery_body_over_then_hold():
    phase = np.linspace(0, 1, 101)
    catch_angle, finish_angle = -30.0, 15.0

    angles = _trunk_angle_legs_first_progression(
        phase,
        catch_angle=catch_angle,
        finish_angle=finish_angle,
        drive_hold=0.35,
        rec_return=0.25,
        rec_hold=0.50,
    )

    # Peak should be at the finish boundary (end of drive).
    finish_idx = int(np.searchsorted(phase, 0.5, side="left"))
    assert abs(angles[finish_idx] - finish_angle) < 1e-6
    assert angles[finish_idx] == angles.max()

    # After the return window (first sample at/after 0.625), should be at catch angle.
    return_phase = 0.5 + 0.25 * 0.5
    idx_return_end = int(np.searchsorted(phase, return_phase, side="left"))
    assert abs(angles[idx_return_end] - catch_angle) < 1e-6

    # Mid recovery should still be held at catch angle.
    idx_mid_hold = int(np.searchsorted(phase, 0.75, side="left"))
    assert abs(angles[idx_mid_hold] - catch_angle) < 1e-6

    # End of cycle should be at catch angle.
    assert abs(angles[-1] - catch_angle) < 1e-6
