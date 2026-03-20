import numpy as np
import pandas as pd

from rowing_catch.algo.analysis import process_rowing_data, _detect_catches_by_seat_reversal, _detect_finishes_by_seat_reversal
from rowing_catch.algo.scenarios import create_scenario_data


def test_finish_line_aligns_with_end_of_draw_and_near_peaks_ideal_scenario():
    df = create_scenario_data("Trunk", "Ideal Technique")
    results = process_rowing_data(df, pre_catch_window=100)
    assert results is not None

    avg = results["avg_cycle"]
    catch_idx = int(results["catch_idx"])
    finish_idx = int(results["finish_idx"])

    seat = avg["Seat_X_Smooth"].to_numpy(dtype=float)
    handle = avg["Handle_X_Smooth"].to_numpy(dtype=float)
    trunk = avg["Trunk_Angle"].to_numpy(dtype=float)

    # Catch shouldn't be the first sample when we request a pre-catch window.
    assert catch_idx >= 50

    # Finish should be after catch.
    assert finish_idx > catch_idx

    # Finish should be close to the peaks *after catch* (ignore the pre-catch segment).
    tol = 5
    seat_peak = catch_idx + int(np.argmax(seat[catch_idx:]))
    handle_peak = catch_idx + int(np.argmax(handle[catch_idx:]))
    trunk_peak = catch_idx + int(np.argmax(trunk[catch_idx:]))

    assert abs(finish_idx - seat_peak) <= tol
    assert abs(finish_idx - handle_peak) <= tol
    assert abs(finish_idx - trunk_peak) <= tol

    # And it should occur at/just before handle reversal (handle stops increasing).
    hvel = np.gradient(handle)
    assert hvel[finish_idx] <= hvel[max(finish_idx - 1, 0)]


def test_detect_catches_chooses_deepest_minimum_in_close_cluster():
    """Regression test for noisy local minima near a catch."""
    seat = pd.Series([
        0.0, 0.5, 1.0, 0.2, 0.0, 0.3, 0.8, 1.2, 0.1, -0.5, -0.4, 0.0,
        0.6, 1.0, 0.7, 0.1, -0.3, -0.2, 0.0
    ])

    # Here we have two candidate minima near indexes 4 and 9 for first stroke.
    catches = _detect_catches_by_seat_reversal(seat, min_separation=6)

    assert len(catches) == 2
    assert catches[0] == 9  # deepest trough should be selected in first cluster
    assert catches[1] == 16  # second stroke trough remains


def test_detect_finishes_chooses_highest_peak_in_close_cluster():
    """Regression test for noisy local maxima near a finish."""
    seat = pd.Series([
        -0.2, 0.0, 0.3, 1.0, 0.7, 0.35, 0.2, 0.4, 1.8, 1.1, 0.7, 0.4,
        0.1, 0.5, 2.0, 1.0, 0.0
    ])

    # Here we have two close candidate maxima at 3 and 8 (cluster) then one at 14.
    finishes = _detect_finishes_by_seat_reversal(seat, min_separation=6)

    assert len(finishes) == 2
    assert finishes[0] == 8  # highest peak should be selected in first cluster
    assert finishes[1] == 14  # second stroke peak remains
