"""Coaching profile — coach-configurable thresholds for the rowing analysis app.

This module is pure Python with no Streamlit or UI dependencies so it can be
imported and tested freely from any layer.
"""

from dataclasses import dataclass


@dataclass
class CoachingProfile:
    """All coach-configurable thresholds that drive diagram annotations and coaching tips.

    The profile uses a two-layer model:

    1. **High-level philosophy**: one or two numbers that express the club's style,
       e.g. ``trunk_opening_ideal_pct = 33`` means the upper body should begin
       opening at roughly 1/3 of the drive.
    2. **Derived thresholds**: computed automatically from the high-level numbers
       via ``@property`` methods.  Advanced coaches can still construct a profile
       with any values they like.

    Default values match the hard-coded constants that previously lived in the
    respective transformer modules.
    """

    # ------------------------------------------------------------------ #
    # High-level coaching philosophy
    # ------------------------------------------------------------------ #

    trunk_opening_ideal_pct: float = 33.0
    """At what percentage of the drive should the upper body start to open.

    Expressed as a fraction of the drive (0–100 %).  Default 33 % means the
    coach expects legs to drive for roughly the first third before the trunk
    begins to swing.
    """

    trunk_open_tolerance_pct: float = 12.0
    """±tolerance (percentage points) around ``trunk_opening_ideal_pct`` that is
    still considered ideal.

    For example, with ideal=33 and tolerance=12 the ideal window is 21–45 % of
    the drive.
    """

    # ------------------------------------------------------------------ #
    # Ideal trunk-angle zones (degrees from vertical)
    # ------------------------------------------------------------------ #

    catch_lean_low: float = -33.0
    """Lower bound (more forward) of the ideal catch lean zone (°)."""

    catch_lean_high: float = -27.0
    """Upper bound (less forward) of the ideal catch lean zone (°)."""

    finish_lean_low: float = 12.0
    """Lower bound (less layback) of the ideal finish lean zone (°)."""

    finish_lean_high: float = 18.0
    """Upper bound (more layback) of the ideal finish lean zone (°)."""

    # ------------------------------------------------------------------ #
    # Recovery rock-over timing
    # ------------------------------------------------------------------ #

    recovery_reach_ideal_low: float = 40.0
    """Lower bound (% of recovery seat travel) for arriving at the catch angle.

    Reaching the catch zone midpoint before this fraction means the rower is
    rushing the forward body swing.
    """

    recovery_reach_ideal_high: float = 80.0
    """Upper bound (% of recovery seat travel) for arriving at the catch angle.

    Arriving after this fraction means the rock-over is dangerously late.
    """

    # ------------------------------------------------------------------ #
    # Trunk-angle separation (seat-position–based timing)
    # ------------------------------------------------------------------ #

    separation_reach_ideal_low: float = 10.0
    """Lower bound (% of recovery seat travel) for the separation diagnostic.

    Reaching the catch zone midpoint before this fraction → trunk rushing forward.
    """

    separation_reach_ideal_high: float = 50.0
    """Upper bound (% of recovery seat travel) for the separation diagnostic.

    After this fraction → late rock-over; body still moving as seat approaches.
    """

    separation_very_late_threshold: float = 90.0
    """If trunk reaches catch zone after this fraction → very late / no separation."""

    # ------------------------------------------------------------------ #
    # Handle-Seat Distance (intra-stroke compression)
    # ------------------------------------------------------------------ #

    handle_seat_rockover_pct: float = 30.0
    """By this percentage of the recovery phase the handle-seat distance should
    have reached at least 50 % of its maximum recovery value.

    A lower value means the coach expects a quicker early rock-over after the
    finish.  Default 30 % — the rower should rock over in the first third of
    the recovery.
    """

    handle_seat_compression_max_pct: float = 40.0
    """Maximum acceptable fraction of the drive phase during which the upper
    body draw (trunk and/or arm pull) is active, detected as the decreasing
    portion of the handle-seat distance curve.

    Above this value the draw is considered drawn out and slow.  Default 40 %
    of the drive.
    """

    # ------------------------------------------------------------------ #
    # Rhythm consistency — ideal curve offset
    # ------------------------------------------------------------------ #

    rhythm_drive_pct_offset: float = 0.0
    """Vertical offset (percentage points) applied to the biomechanical ideal drive%
    curve.  Positive values shift the curve up (more drive time expected);
    negative values shift it down (less drive time expected).  Default 0 uses
    the published biomechanics curve unchanged.
    """

    # ------------------------------------------------------------------ #
    # Derived properties (computed from the high-level philosophy)
    # ------------------------------------------------------------------ #

    @property
    def catch_zone(self) -> tuple[float, float]:
        """Ideal catch lean range as a ``(low, high)`` tuple (degrees)."""
        return (self.catch_lean_low, self.catch_lean_high)

    @property
    def finish_zone(self) -> tuple[float, float]:
        """Ideal finish lean range as a ``(low, high)`` tuple (degrees)."""
        return (self.finish_lean_low, self.finish_lean_high)

    @property
    def drive_open_low(self) -> float:
        """Lower bound of the ideal trunk-opening window (0–1 fraction of drive).

        Derived from ``trunk_opening_ideal_pct - trunk_open_tolerance_pct``.
        """
        return max(0.0, (self.trunk_opening_ideal_pct - self.trunk_open_tolerance_pct) / 100.0)

    @property
    def drive_open_high(self) -> float:
        """Upper bound of the ideal trunk-opening window (0–1 fraction of drive).

        Derived from ``trunk_opening_ideal_pct + trunk_open_tolerance_pct``.
        """
        return min(1.0, (self.trunk_opening_ideal_pct + self.trunk_open_tolerance_pct) / 100.0)

    @property
    def steepness_threshold(self) -> float:
        """Maximum acceptable steepness window (0–1 fraction) for trunk-opening burst.

        A generous default of 0.45 — the coach can tighten this separately via
        direct construction if needed.
        """
        return 0.45


# Singleton with all factory defaults — use this for testing and as the
# initial value in session state.
DEFAULT_COACHING_PROFILE: CoachingProfile = CoachingProfile()


__all__ = [
    'CoachingProfile',
    'DEFAULT_COACHING_PROFILE',
]
