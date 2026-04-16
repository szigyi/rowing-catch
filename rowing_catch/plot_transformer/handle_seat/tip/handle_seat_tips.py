"""Coaching tip functions for the Handle-Seat Distance plot annotations.

Each function is a pure function: takes floats/bools and returns a
``(cue_text, is_ideal)`` tuple.  ``is_ideal=True`` means the rower is
within the ideal range; ``is_ideal=False`` means an improvement is needed.

Threshold summary
-----------------
[P1] Upper body engagement timing (compression start % of drive):
    compression_start_pct within ideal_pct ± tolerance_pct  → ideal (green)
    compression_start_pct < ideal_pct - tolerance_pct        → too early (red)
    compression_start_pct > ideal_pct + tolerance_pct        → too late (red)

[S1] Compression duration (% of drive spent in compression):
    duration_pct ≤ COMPRESSION_MAX_PCT  → quick, decisive (green)
    duration_pct >  COMPRESSION_MAX_PCT → dragged out (red)

[P2] Recovery rock-over speed:
    rockover_achieved_pct ≤ target_pct  → rocks over quickly (green)
    rockover_achieved_pct > target_pct  → slow rock-over (red)

[P3] Still rocking over close to catch:
    still_increasing = False  → handle stable approaching catch (green)
    still_increasing = True   → still moving close to catch (red)
"""

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# Fraction of max recovery distance that should be reached by the target window.
ROCKOVER_DISTANCE_FRACTION: float = 0.50


# ---------------------------------------------------------------------------
# [P1] Upper body engagement timing
# ---------------------------------------------------------------------------


def compression_timing_coach_tip(
    compression_start_pct: float,
    ideal_pct: float,
    tolerance_pct: float,
) -> tuple[str, bool]:
    """Coaching cue for when the upper body begins engaging during the drive.

    The compression start is detected from the handle-seat distance: the
    moment the distance starts to decrease is when the upper body (trunk
    and/or arms) begins to draw toward the finish position.

    Args:
        compression_start_pct: When compression starts as % of the drive (0–100).
        ideal_pct: Coach-configured ideal opening time (% of drive).
        tolerance_pct: Acceptable deviation around the ideal (percentage points).

    Returns:
        Tuple of (coaching cue string, is_ideal bool)
    """
    low = ideal_pct - tolerance_pct
    high = ideal_pct + tolerance_pct

    if compression_start_pct < low:
        return (
            f'Upper body engagement detected at {compression_start_pct:.0f}% of the drive '
            f'— earlier than ideal ({ideal_pct:.0f}% ± {tolerance_pct:.0f}%). '
            'Keep the handle out longer and let the legs finish driving before '
            'the upper body (trunk and arms) begins to engage.'
        ), False

    if compression_start_pct > high:
        return (
            f'Upper body engagement detected late at {compression_start_pct:.0f}% of the drive '
            f'(ideal: {ideal_pct:.0f}% ± {tolerance_pct:.0f}%). '
            'The upper body — trunk and arms — is slow to engage after the legs. '
            'Begin the draw earlier to stay connected through the finish.'
        ), False

    return (
        f'Upper body engagement at {compression_start_pct:.0f}% of the drive '
        f'— within the ideal window ({low:.0f}%–{high:.0f}%). ✓'
    ), True


# ---------------------------------------------------------------------------
# [S1] Compression duration
# ---------------------------------------------------------------------------


def compression_duration_coach_tip(
    compression_duration_pct: float,
    max_pct: float,
) -> tuple[str, bool]:
    """Coaching cue for how long the compression phase lasts within the drive.

    A long compression phase means the upper body draw (trunk swing and/or
    arm pull) was slow and drawn out rather than decisive.

    Args:
        compression_duration_pct: Compression phase length as % of the drive.
        max_pct: Coach-configured maximum acceptable duration (% of drive).

    Returns:
        Tuple of (coaching cue string, is_ideal bool)
    """
    if compression_duration_pct > max_pct:
        return (
            f'The upper body draw lasted {compression_duration_pct:.0f}% of the drive '
            f'— drawn out (ideal: under {max_pct:.0f}%). '
            'Focus on a quicker, more decisive draw of the upper body and arms '
            'toward the finish position.'
        ), False

    return (
        f'Upper body draw duration: {compression_duration_pct:.0f}% of the drive — quick and decisive (under {max_pct:.0f}%). ✓'
    ), True


# ---------------------------------------------------------------------------
# [P2] Recovery rock-over speed
# ---------------------------------------------------------------------------


def recovery_rockover_coach_tip(
    rockover_achieved_pct: float,
    target_pct: float,
) -> tuple[str, bool]:
    """Coaching cue for how quickly the handle separates from the seat in recovery.

    Measured as: by what % of the recovery phase has the handle-seat distance
    reached 50% of its maximum recovery value.

    Args:
        rockover_achieved_pct: % of recovery at which distance reached 50% of max.
        target_pct: Coach-configured target window (% of recovery, e.g. 30).

    Returns:
        Tuple of (coaching cue string, is_ideal bool)
    """
    if rockover_achieved_pct > target_pct:
        return (
            f'Handle separation reached 50% of recovery distance at {rockover_achieved_pct:.0f}% '
            f'of the recovery (ideal: by {target_pct:.0f}%). '
            'Rock over more quickly after the finish — get the body forward early '
            'before the seat starts to travel.'
        ), False

    return (
        f'Handle well separated by {rockover_achieved_pct:.0f}% of the recovery '
        f'(target: {target_pct:.0f}%) — strong early rock-over. ✓'
    ), True


# ---------------------------------------------------------------------------
# [P3] Still rocking over close to catch
# ---------------------------------------------------------------------------


def late_rockover_coach_tip(
    still_increasing: bool,
    late_window_pct: float,
) -> tuple[str, bool]:
    """Coaching cue for handle still moving away from the seat close to the catch.

    If the handle-seat distance is still increasing in the last portion of the
    recovery, the rower has not completed the forward body swing before the catch.

    Args:
        still_increasing: True if distance still has positive slope in the last
                          late_window_pct % of recovery.
        late_window_pct: The window size checked (% of recovery from the end).

    Returns:
        Tuple of (coaching cue string, is_ideal bool)
    """
    if still_increasing:
        return (
            f'Handle-seat distance still increasing in the last {late_window_pct:.0f}% '
            'of the recovery — the forward body swing is not complete before the catch. '
            'Finish the rock-over earlier so the body is set and stable at the catch.'
        ), False

    return ('Handle-seat distance stable approaching the catch — body swing completed well before the catch. ✓'), True


__all__ = [
    'ROCKOVER_DISTANCE_FRACTION',
    'compression_timing_coach_tip',
    'compression_duration_coach_tip',
    'recovery_rockover_coach_tip',
    'late_rockover_coach_tip',
]
