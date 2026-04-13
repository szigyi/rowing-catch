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

All threshold parameters are **mandatory** — they must be derived from a
``CoachingProfile`` instance by the caller (Layer 2 transformer).
"""


def catch_separation_tip(
    catch_angle: float,
    catch_zone: tuple[float, float],
) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for the trunk angle at the catch.

    Args:
        catch_angle: Measured trunk angle at catch (degrees).
        catch_zone: (low, high) ideal catch lean range (both negative values).

    Returns:
        Tuple of (coaching cue string ≤ 12 words, is_ideal bool)
    """
    z_low, z_high = catch_zone
    if catch_angle > z_high:
        deficit = abs(catch_angle - z_high)
        return f'Rock over more — {deficit:.1f}° short of ideal lean', False
    if catch_angle < z_low:
        excess = abs(catch_angle - z_low)
        return f'Reduce lean — {excess:.1f}° past ideal; hips may lag', False
    return 'Catch lean is within ideal range ✓', True


def finish_separation_tip(
    finish_angle: float,
    finish_zone: tuple[float, float],
) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for the trunk angle at the finish.

    Args:
        finish_angle: Measured trunk angle at finish (degrees).
        finish_zone: (low, high) ideal finish lean range (both positive values).

    Returns:
        Tuple of (coaching cue string ≤ 12 words, is_ideal bool)
    """
    z_low, z_high = finish_zone
    if finish_angle < z_low:
        deficit = abs(finish_angle - z_low)
        return f'Lay back more — {deficit:.1f}° short of ideal finish lean', False
    if finish_angle > z_high:
        excess = abs(finish_angle - z_high)
        return f'Reduce lay-back — {excess:.1f}° past ideal; back risk', False
    return 'Finish lean is within ideal range ✓', True


def recovery_separation_tip(
    reach_frac: float,
    ideal_low: float,
    ideal_high: float,
    very_late_threshold: float,
) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for recovery separation.

    The *reach_frac* is the fraction of recovery seat travel at which the trunk
    first enters the catch zone midpoint.  Ideal: body settles into the catch
    position well before the seat completes its return journey.

    Args:
        reach_frac: Fraction of seat travel (0–1) when trunk reaches catch zone.
        ideal_low: Lower bound (0–1) — below this the trunk rushes forward.
                   Derived from ``CoachingProfile.separation_reach_ideal_low / 100``.
        ideal_high: Upper bound (0–1) — above this the rock-over is late.
                    Derived from ``CoachingProfile.separation_reach_ideal_high / 100``.
        very_late_threshold: Above this fraction the situation is very late / no separation.
                             Derived from ``CoachingProfile.separation_very_late_threshold / 100``.

    Returns:
        Tuple of (coaching cue string ≤ 14 words, is_ideal bool)
    """
    if reach_frac < ideal_low:
        pct = round(reach_frac * 100)
        return (f'Body rocks over immediately ({pct}% of seat travel done) — trunk rushes forward; check balance'), False
    if reach_frac <= ideal_high:
        pct = round(reach_frac * 100)
        return (f'Good separation: body settled at {pct}% of seat travel — seat returns freely ✓'), True
    if reach_frac <= very_late_threshold:
        pct = round(reach_frac * 100)
        return (f'Late rock-over: body still moving at {pct}% of seat travel — trunk arrives with the seat, not before it'), False
    return ('Body reaches catch angle as seat arrives — no separation; whiplash/overreach risk'), False


__all__ = [
    'catch_separation_tip',
    'finish_separation_tip',
    'recovery_separation_tip',
]
