"""Coaching tip functions for rhythm consistency plot annotations.

Each function is a pure function: takes floats and returns a
``(cue_text, is_ideal)`` tuple.  ``is_ideal=True`` means the rower is
within the ideal range; ``is_ideal=False`` means an improvement is needed.
The boolean drives the background colour of the coach-tip cell in the
Streamlit toggle widget (green = ideal, red = needs improvement).

Threshold summary
-----------------
[P1] Mean drive % vs ideal curve:
    diff_pct ≤ 0        → below or at ideal: perfect (green)
    0 < diff_pct ≤ 2 %  → slightly above ideal: acceptable (yellow → is_ideal=False)
    diff_pct > 2 %      → too high: needs correction (red)
    Action when too high: speed up the drive, slow the recovery.
    Action when too low / ideal: nothing to change.

[Z1] Drive% vertical spread (±1 SD across cycles):
    drive_std ≤ 3 %     → tight and consistent (green)
    drive_std > 3 %     → inconsistent (red) — same muscle feeling every drive

[Z2] SPM horizontal spread (±1 SD across cycles):
    spm_std ≤ 2 SPM     → consistent rate (green)
    spm_std > 2 SPM     → wandering rate (red) — same movements every stroke

All threshold values are kept as named constants at the module level so they
remain trivially adjustable and fully visible to the caller.
"""

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

DRIVE_PCT_ACCEPTABLE_THRESHOLD: float = 2.0  # % above ideal before "needs work"
DRIVE_STD_TIGHT_THRESHOLD: float = 3.0  # % 1-SD — below = consistent
SPM_STD_CONSISTENT_THRESHOLD: float = 2.0  # SPM 1-SD — below = consistent


# ---------------------------------------------------------------------------
# [P1] Mean drive % vs ideal curve
# ---------------------------------------------------------------------------


def drive_pct_vs_ideal_coach_tip(
    mean_drive_pct: float,
    ideal_drive_pct: float,
    mean_spm: float,
) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for the mean drive % vs the ideal curve.

    Thresholds:
        diff_pct ≤ 0                          → below/at ideal: perfect
        0 < diff_pct ≤ DRIVE_PCT_ACCEPTABLE   → acceptable, minor correction suggested
        diff_pct > DRIVE_PCT_ACCEPTABLE        → needs work: speed drive, slow recovery

    Args:
        mean_drive_pct: Rower's mean drive phase percentage across cycles.
        ideal_drive_pct: Ideal drive percentage at the rower's mean SPM.
        mean_spm: Rower's mean stroke rate (used for context in the cue text).

    Returns:
        Tuple of (coaching cue string, is_ideal bool)
    """
    diff_pct = mean_drive_pct - ideal_drive_pct

    if diff_pct <= 0:
        return (
            f'Your mean drive % ({mean_drive_pct:.1f}%) is at or below the ideal benchmark '
            f'({ideal_drive_pct:.1f}%) for {mean_spm:.1f} SPM — ideal rhythm. ✓'
        ), True

    if diff_pct <= DRIVE_PCT_ACCEPTABLE_THRESHOLD:
        return (
            f'Your mean drive % ({mean_drive_pct:.1f}%) is {diff_pct:.1f}% above the ideal '
            f'({ideal_drive_pct:.1f}%) for {mean_spm:.1f} SPM — acceptable, but consider '
            'speeding up the drive and slowing the recovery for better rhythm.'
        ), False

    return (
        f'Your mean drive % ({mean_drive_pct:.1f}%) is {diff_pct:.1f}% above the ideal '
        f'({ideal_drive_pct:.1f}%) for {mean_spm:.1f} SPM. Speed up the drive phase '
        'and slow down the recovery — put more power into the drive and control the slide back.'
    ), False


# ---------------------------------------------------------------------------
# [Z1] Drive% vertical spread
# ---------------------------------------------------------------------------


def drive_pct_spread_coach_tip(drive_std: float) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for the stroke-to-stroke drive% variability.

    Threshold: DRIVE_STD_TIGHT_THRESHOLD (default 3 %).

    Args:
        drive_std: Standard deviation of drive phase % across all cycles.

    Returns:
        Tuple of (coaching cue string, is_ideal bool)
    """
    if drive_std <= DRIVE_STD_TIGHT_THRESHOLD:
        return (
            f'Vertical spread of {drive_std:.1f}% — your drive/recovery balance is tight and consistent stroke-to-stroke. ✓'
        ), True

    return (
        f'Vertical spread of {drive_std:.1f}% — your drive/recovery balance '
        'is inconsistent stroke-to-stroke. Focus on the same muscle feeling '
        'during every drive — each stroke should feel identical.'
    ), False


# ---------------------------------------------------------------------------
# [Z2] SPM horizontal spread
# ---------------------------------------------------------------------------


def spm_spread_coach_tip(spm_std: float) -> tuple[str, bool]:
    """Return a coaching cue and ideal-flag for the stroke-to-stroke SPM variability.

    Threshold: SPM_STD_CONSISTENT_THRESHOLD (default 2 SPM).

    Args:
        spm_std: Standard deviation of strokes per minute across all cycles.

    Returns:
        Tuple of (coaching cue string, is_ideal bool)
    """
    if spm_std <= SPM_STD_CONSISTENT_THRESHOLD:
        return (f'Horizontal spread of {spm_std:.1f} SPM — your stroke rate is consistent throughout the piece. ✓'), True

    return (
        f'Horizontal spread of {spm_std:.1f} SPM — your stroke rate '
        'is wandering. Focus on the same movements and rhythm during '
        'every stroke to keep a steady rate.'
    ), False


__all__ = [
    'DRIVE_PCT_ACCEPTABLE_THRESHOLD',
    'DRIVE_STD_TIGHT_THRESHOLD',
    'SPM_STD_CONSISTENT_THRESHOLD',
    'drive_pct_vs_ideal_coach_tip',
    'drive_pct_spread_coach_tip',
    'spm_spread_coach_tip',
]
