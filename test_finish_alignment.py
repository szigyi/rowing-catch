import numpy as np

from rowing_catch.algo.analysis import process_rowing_data
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
