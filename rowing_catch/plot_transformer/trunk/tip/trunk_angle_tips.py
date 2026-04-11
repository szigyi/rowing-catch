"""Coaching tip functions for trunk angle plot annotations.

Each function is a pure function: takes floats/lists and returns a
``(cue_text, is_ideal)`` tuple.  ``is_ideal=True`` means the rower is
within the ideal range; ``is_ideal=False`` means an improvement is needed.
The boolean drives the background colour of the coach-tip cell in the
Streamlit toggle widget (green = ideal, red = needs improvement).
"""


def catch_lean_coach_tip(
    catch_lean: float,
    catch_zone: tuple[float, float],
) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for the catch lean angle.

    Thresholds (degrees from vertical, negative = forward lean):
        catch_lean > catch_zone[1]  → not enough lean (too upright at catch)
        catch_lean < catch_zone[0]  → over-leaning (hips may be left behind)
        within zone                 → ideal

    Args:
        catch_lean: Measured trunk angle at catch (degrees)
        catch_zone: (low, high) ideal range tuple, both negative values

    Returns:
        Tuple of (coaching cue string ≤ 12 words, is_ideal bool)
    """
    z_low, z_high = catch_zone
    if catch_lean > z_high:
        deficit = abs(catch_lean - z_high)
        return f'Rock over more — {deficit:.1f}° short of ideal lean', False
    if catch_lean < z_low:
        excess = abs(catch_lean - z_low)
        return f'Reduce lean — {excess:.1f}° past ideal; hips may lag', False
    return 'Catch lean is within ideal range ✓', True


def finish_lean_coach_tip(
    finish_lean: float,
    finish_zone: tuple[float, float],
) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for the finish lean angle.

    Thresholds (degrees from vertical, positive = backward lean):
        finish_lean < finish_zone[0] → not enough lay-back
        finish_lean > finish_zone[1] → over-extended (risk of back injury)
        within zone                  → ideal

    Args:
        finish_lean: Measured trunk angle at finish (degrees)
        finish_zone: (low, high) ideal range tuple, both positive values

    Returns:
        Tuple of (coaching cue string ≤ 12 words, is_ideal bool)
    """
    z_low, z_high = finish_zone
    if finish_lean < z_low:
        deficit = abs(finish_lean - z_low)
        return f'Lay back more — {deficit:.1f}° short of ideal finish lean', False
    if finish_lean > z_high:
        excess = abs(finish_lean - z_high)
        return f'Reduce lay-back — {excess:.1f}° past ideal; back risk', False
    return 'Finish lean is within ideal range ✓', True


def drive_trunk_opening_coach_tip(
    drive_y: list[float],
) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for trunk opening timing during the drive.

    Ideal pattern: trunk stays near catch angle for ~25–40% of the drive
    (legs driving, trunk held), then rotates quickly in the final 60–75%.

    Algorithm:
        1. Total range = drive_y[-1] - drive_y[0]  (signed)
        2. 15% threshold crossing: first index where the trunk has moved
           ≥ 15% of total range. This marks "opening starts".
        3. Opening start fraction = that index / total drive length
           - < 0.20  → trunk opens too early (legs not yet loaded)
           - 0.20–0.45 → ideal hold window
           - > 0.45  → trunk holds too long (opening too late / too slow)
        4. Steepness (80% crossing): first index where ≥ 80% of range moved,
           expressed as a fraction of drive length.
           steepness_window = 80pct_fraction - 15pct_fraction
           - < 0.20  → very rapid swing (powerful, ideal)
           - 0.20–0.40 → acceptable
           - > 0.40  → slow/gradual opening throughout (no acceleration burst)

    Args:
        drive_y: Trunk angle values over the drive phase (catch to finish).
                 drive_y[0] = angle at catch, drive_y[-1] = angle at finish.

    Returns:
        Tuple of (coaching cue string, is_ideal bool)
    """
    if len(drive_y) < 4:
        return 'Drive too short to assess trunk opening', False

    n = len(drive_y)
    total = drive_y[-1] - drive_y[0]
    if abs(total) < 1.0:
        return 'Minimal trunk rotation in drive', False

    fractions = [(v - drive_y[0]) / total for v in drive_y]

    open_start_idx = next((i for i, f in enumerate(fractions) if f >= 0.15), n - 1)
    open_start_frac = open_start_idx / (n - 1)

    open_80_idx = next((i for i, f in enumerate(fractions) if f >= 0.80), n - 1)
    open_80_frac = open_80_idx / (n - 1)

    steepness_window = open_80_frac - open_start_frac

    if open_start_frac < 0.20:
        pct = round(open_start_frac * 100)
        return f'Trunk opens too early ({pct}% into drive) — sequence legs first', False

    if open_start_frac > 0.45:
        pct = round(open_start_frac * 100)
        return f'Trunk opens too late ({pct}% into drive) — begin swing earlier', False

    if steepness_window > 0.45:
        return 'Trunk swings slowly — accelerate the opening burst', False

    hold_pct = round(open_start_frac * 100)
    return f'Good trunk sequencing: held for {hold_pct}% then quick swing \u2713', True


def recovery_rock_over_coach_tip(
    recovery_y: list[float],
    catch_zone: tuple[float, float],
) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for trunk rock-over timing during recovery.

    Ideal pattern: after the finish the trunk swings forward promptly and
    reaches the catch angle well before the next catch (~70–85% of recovery).

    Algorithm:
        1. total_range = recovery_y[-1] - recovery_y[0]  (signed, always negative)
        2. reach_frac = first index where trunk ≤ catch_zone_mid / total points
           - reach_frac < 0.40  → rocks over very early (rushed, may lose balance)
           - 0.40–0.80 → ideal: settled at catch position with time to spare
           - 0.80–0.95 → late: barely reaches catch angle before the next catch
           - > 0.95 or never reached → arrives at catch still upright (whiplash risk)
        3. Steepness: how gradual the forward swing is.
           steepness_window = 80pct_frac - 15pct_frac
           - > 0.60  → very slow rock-over; rower drifts forward rather than swings

    Args:
        recovery_y: Trunk angle values from finish to next catch.
                    recovery_y[0] = angle at finish, recovery_y[-1] = angle at next catch.
        catch_zone: (low, high) ideal catch angle range, both negative values.

    Returns:
        Tuple of (coaching cue string ≤ 14 words, is_ideal bool)
    """
    if len(recovery_y) < 4:
        return 'Recovery too short to assess rock-over', False

    n = len(recovery_y)
    total = recovery_y[-1] - recovery_y[0]
    if abs(total) < 1.0:
        return 'Trunk barely moves in recovery — rock over more', False

    catch_zone_mid = (catch_zone[0] + catch_zone[1]) / 2

    fractions = [(v - recovery_y[0]) / total for v in recovery_y]

    reach_idx = next(
        (i for i, v in enumerate(recovery_y) if v <= catch_zone_mid),
        n - 1,
    )
    reach_frac = reach_idx / (n - 1)

    start_15_idx = next((i for i, f in enumerate(fractions) if f >= 0.15), n - 1)
    start_80_idx = next((i for i, f in enumerate(fractions) if f >= 0.80), n - 1)
    steepness_window = (start_80_idx - start_15_idx) / (n - 1)

    if reach_frac < 0.35:
        pct = round(reach_frac * 100)
        return f'Rocks over very early ({pct}% into recovery) — risk of rushing', False

    if reach_frac <= 0.80:
        if steepness_window > 0.60:
            return 'Forward swing is gradual — accelerate the rock-over', False
        pct = round(reach_frac * 100)
        return f'Good rock-over: catch angle reached at {pct}% of recovery \u2713', True

    if reach_frac <= 0.95:
        pct = round(reach_frac * 100)
        return f'Late rock-over ({pct}% of recovery) — risk of whiplash at catch', False

    return 'Trunk arrives at catch angle last moment — whiplash/overreach risk', False


__all__ = [
    'catch_lean_coach_tip',
    'finish_lean_coach_tip',
    'drive_trunk_opening_coach_tip',
    'recovery_rock_over_coach_tip',
]
