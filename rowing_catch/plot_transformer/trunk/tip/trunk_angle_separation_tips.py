"""Coaching tip functions for the Trunk Angle Separation plot.

Each function is a pure function: takes floats and returns a
``(cue_text, is_ideal)`` tuple.  ``is_ideal=True`` means the rower is
within the ideal range; ``is_ideal=False`` means an improvement is needed.
The boolean drives the background colour of the coach-tip cell in the
Streamlit toggle widget (green = ideal, red = needs improvement).

The 'Trunk Angle Separation' plot shows trunk angle (Y) vs. seat position (X).
The coaching focus is on *when* the body rocks over relative to seat travel —
i.e. does the body lean forward while the seat is still moving back (recovery)?

Coordinate system reminder
--------------------------
X-axis = seat position (mm).  During the **drive** the seat travels forward
(X increases: catch-seat → finish-seat).  During **recovery** the seat travels
backward (X decreases: finish-seat → catch-seat).  Y-axis = trunk angle (°
from vertical, negative = forward lean, positive = backward lay-back).
"""


def catch_separation_tip(
    catch_angle: float,
    catch_zone: tuple[float, float],
) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for the trunk angle at the catch.

    Returns:
        Tuple of (coaching cue string ≤ 12 words, is_ideal bool)
    """
    z_low, z_high = catch_zone
    if catch_angle > z_high:
        deficit = abs(catch_angle - z_high)
        return f'Rock over more \u2014 {deficit:.1f}\u00b0 short of ideal lean', False
    if catch_angle < z_low:
        excess = abs(catch_angle - z_low)
        return f'Reduce lean \u2014 {excess:.1f}\u00b0 past ideal; hips may lag', False
    return 'Catch lean is within ideal range \u2713', True


def finish_separation_tip(
    finish_angle: float,
    finish_zone: tuple[float, float],
) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for the trunk angle at the finish.

    Returns:
        Tuple of (coaching cue string ≤ 12 words, is_ideal bool)
    """
    z_low, z_high = finish_zone
    if finish_angle < z_low:
        deficit = abs(finish_angle - z_low)
        return f'Lay back more \u2014 {deficit:.1f}\u00b0 short of ideal finish lean', False
    if finish_angle > z_high:
        excess = abs(finish_angle - z_high)
        return f'Reduce lay-back \u2014 {excess:.1f}\u00b0 past ideal; back risk', False
    return 'Finish lean is within ideal range \u2713', True


def recovery_separation_tip(
    reach_frac: float,
) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for recovery separation.

    Thresholds (agreed with developer):
        reach_frac < 0.10  → rushes over; trunk rushing forward, check balance
        0.10–0.50          → ideal: body settled early, seat travels the rest alone
        0.50–0.90          → late: body still rocking as seat approaches catch
        > 0.90 or never    → very late: no separation, high injury risk

    Returns:
        Tuple of (coaching cue string ≤ 14 words, is_ideal bool)
    """
    if reach_frac < 0.10:
        pct = round(reach_frac * 100)
        return (f'Body rocks over immediately ({pct}% of seat travel done) \u2014 trunk rushes forward; check balance'), False
    if reach_frac <= 0.50:
        pct = round(reach_frac * 100)
        return (f'Good separation: body settled at {pct}% of seat travel \u2014 seat returns freely \u2713'), True
    if reach_frac <= 0.90:
        pct = round(reach_frac * 100)
        return (
            f'Late rock-over: body still moving at {pct}% of seat travel \u2014 trunk arrives with the seat, not before it'
        ), False
    return ('Body reaches catch angle as seat arrives \u2014 no separation; whiplash/overreach risk'), False


__all__ = [
    'catch_separation_tip',
    'finish_separation_tip',
    'recovery_separation_tip',
]
