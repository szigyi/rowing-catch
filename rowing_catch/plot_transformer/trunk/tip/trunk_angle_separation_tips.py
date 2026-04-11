"""Coaching tip functions for the Trunk Angle Separation plot.

Each function is a pure function: takes floats and returns a short coaching
cue string. They are independently testable with no side effects.

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
) -> str:
    """Return a coaching cue for the trunk angle at the catch.

    At the catch the seat is at its most-forward position.  A good rower
    arrives at the catch already leaning forward in their ideal angle zone,
    not still rocking over.

    Thresholds (degrees from vertical, negative = forward lean):
        catch_angle > catch_zone[1]  → too upright at catch (not enough reach)
        catch_angle < catch_zone[0]  → over-leaning (compression lost)
        within zone                  → ideal

    Args:
        catch_angle: Measured trunk angle at the catch (degrees)
        catch_zone: (low, high) ideal catch angle range (both negative)

    Returns:
        Short coaching cue string (≤ 12 words)
    """
    z_low, z_high = catch_zone
    if catch_angle > z_high:
        deficit = abs(catch_angle - z_high)
        return f'Rock over more \u2014 {deficit:.1f}\u00b0 short of ideal lean'
    if catch_angle < z_low:
        excess = abs(catch_angle - z_low)
        return f'Reduce lean \u2014 {excess:.1f}\u00b0 past ideal; hips may lag'
    return 'Catch lean is within ideal range \u2713'


def finish_separation_tip(
    finish_angle: float,
    finish_zone: tuple[float, float],
) -> str:
    """Return a coaching cue for the trunk angle at the finish.

    At the finish the seat is at its most-rearward position.  The rower should
    have achieved a full lay-back within the ideal zone.

    Thresholds (degrees from vertical, positive = backward lean):
        finish_angle < finish_zone[0] → not enough lay-back
        finish_angle > finish_zone[1] → over-extended (back injury risk)
        within zone                   → ideal

    Args:
        finish_angle: Measured trunk angle at finish (degrees)
        finish_zone: (low, high) ideal finish angle range (both positive)

    Returns:
        Short coaching cue string (≤ 12 words)
    """
    z_low, z_high = finish_zone
    if finish_angle < z_low:
        deficit = abs(finish_angle - z_low)
        return f'Lay back more \u2014 {deficit:.1f}\u00b0 short of ideal finish lean'
    if finish_angle > z_high:
        excess = abs(finish_angle - z_high)
        return f'Reduce lay-back \u2014 {excess:.1f}\u00b0 past ideal; back risk'
    return 'Finish lean is within ideal range \u2713'


def recovery_separation_tip(
    reach_frac: float,
) -> str:
    """Return a coaching cue for how early the trunk reaches the catch zone during recovery.

    On the Trunk Angle vs Seat Position plot, the recovery segment runs from
    the finish point (top-right: seat rearward, trunk laid back) back to the
    catch point (bottom-left: seat forward, trunk leaning forward).  The seat
    travels backward (X decreases) while the trunk rocks forward (Y decreases).

    ``reach_frac`` is the fraction of total recovery seat travel at which the
    trunk angle first enters the ideal catch zone midpoint.
    0.0 = seat has not moved at all from finish position yet.
    1.0 = seat has fully returned to the catch position.

    A rower who is well-separated will have their body settled (trunk in the
    catch zone) while the seat still has a significant distance left to travel —
    i.e. a LOW reach_frac.  A rower who is late will still be rocking over as
    the seat arrives — i.e. a HIGH reach_frac.

    Thresholds (agreed with developer):
        reach_frac < 0.10  → rocks over before the seat has barely moved;
                             trunk is rushing forward, possibly disturbing boat balance
        0.10–0.50          → ideal: body settled early, seat travels the rest alone
        0.50–0.90          → late: body still rocking as seat approaches catch;
                             risk of the trunk arriving late (whiplash/overreach)
        > 0.90 or never    → very late: body arrives at catch angle at the last moment;
                             no separation, high injury risk

    Args:
        reach_frac: Fraction of recovery seat travel at which the trunk first
                    reaches the catch zone midpoint. Pass 1.0 if the trunk never
                    reaches the catch zone during recovery.

    Returns:
        Short coaching cue string (≤ 14 words)
    """
    if reach_frac < 0.10:
        pct = round(reach_frac * 100)
        return (
            f'Body rocks over immediately ({pct}% of seat travel done) \u2014 '
            'trunk rushes forward; check balance'
        )
    if reach_frac <= 0.50:
        pct = round(reach_frac * 100)
        return (
            f'Good separation: body settled at {pct}% of seat travel \u2014 '
            'seat returns freely \u2713'
        )
    if reach_frac <= 0.90:
        pct = round(reach_frac * 100)
        return (
            f'Late rock-over: body still moving at {pct}% of seat travel \u2014 '
            'trunk arrives with the seat, not before it'
        )
    return (
        'Body reaches catch angle as seat arrives \u2014 '
        'no separation; whiplash/overreach risk'
    )


__all__ = [
    'catch_separation_tip',
    'finish_separation_tip',
    'recovery_separation_tip',
]
