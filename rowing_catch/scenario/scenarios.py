import numpy as np
import pandas as pd


def _trunk_angle_legs_first_progression(
    phase: np.ndarray,
    catch_angle: float,
    finish_angle: float,
    drive_hold: float = 0.35,
    finish_hold: float = 0.05,
    rec_return: float = 0.25,
) -> np.ndarray:
    """Return a simple sequencing-aware trunk-angle trace.

    Model (very simplified, coaching-oriented):
    - Early drive: trunk remains "set" while legs push (angle ~ constant at catch)
    - Late drive: trunk opens smoothly toward finish angle
    - Finish hold: brief hold at the finish to avoid peak dampening from smoothing
    - Recovery: *quick* return to the catch/trunk-forward angle ("body over"),
      then hold that angle for much of recovery.

    phase: 0..1 across the whole stroke (0..0.5 drive, 0.5..1 recovery)
    """
    drive_phase = phase / 0.5
    rec_phase = (phase - 0.5) / 0.5

    # Drive: Opens linearly from drive_hold to (1.0 - finish_hold)
    drive_open_start = drive_hold
    drive_open_end = max(drive_hold + 0.01, 1.0 - finish_hold)

    drive_open = (drive_phase - drive_open_start) / (drive_open_end - drive_open_start)
    drive_open = np.clip(drive_open, 0.0, 1.0)
    drive_angle = catch_angle + (finish_angle - catch_angle) * drive_open

    # Recovery: Holds at finish for finish_hold, then returns to catch over rec_return,
    # then holds at catch for the rest.
    rec_drop = np.zeros_like(rec_phase)

    # Hold at finish angle initially.
    finishing = rec_phase <= finish_hold
    rec_drop[finishing] = 0.0

    # Linear return from finish to catch over rec_return window.
    returning = (rec_phase > finish_hold) & (rec_phase <= rec_return)
    rec_drop[returning] = (rec_phase[returning] - finish_hold) / max(1e-6, rec_return - finish_hold)

    # Hold at catch once return window completes.
    after_return = rec_phase > rec_return
    rec_drop[after_return] = 1.0

    rec_angle = finish_angle + (catch_angle - finish_angle) * rec_drop

    return np.where(phase <= 0.5, drive_angle, rec_angle)


def get_stroke_phase(num_points: int, drive_ratio: float = 1 / 3) -> np.ndarray:
    """Warps a linear time array so that phase=0.5 occurs at the specified drive_ratio."""
    t = np.linspace(0, 1, num_points)
    with np.errstate(divide='ignore', invalid='ignore'):
        result = np.where(t <= drive_ratio, 0.5 * (t / drive_ratio), 0.5 + 0.5 * ((t - drive_ratio) / (1.0 - drive_ratio)))
    return result


def generate_cycle_df(
    num_points=100,
    handle_x_range=(150, 550),
    handle_y_range=(-50, -10),
    seat_x_range=(250, 550),
    trunk_angles=None,
    handle_y_noise=0,
    seat_finish_lag: float = 0.03,
):
    """
    Generates a single cycle of rowing data (drive and recovery).

    Notes on trunk angle sequencing (simplified):
    - In good sequencing the trunk angle is *nearly stable* at the start of the drive ("legs down")
      and opens later as the legs run out, rather than changing immediately from the catch.

    seat_finish_lag:
        Fraction of the drive duration (0..~0.1) by which the seat reaches its maximum
        *after* the handle does. This helps align the detected finish (Seat_X max)
        with the trunk-angle peak at the end of the drive.
    """
    # Phase mapping: 0 to 0.5 is drive, 0.5 to 1.0 is recovery.
    # To get a 1:2 ratio, we use get_stroke_phase to map the physical array indices
    # so that the midpoint (0.5) occurs at 1/3 of the array points.
    phase = get_stroke_phase(num_points)

    # Seat X: 0 (catch) -> max (finish) -> 0 (catch)
    # We allow a small lag so Seat_X reaches max slightly after Handle_X.
    seat_finish_lag = float(np.clip(seat_finish_lag, 0.0, 0.10))
    drive_end = 0.5
    seat_drive_end = min(0.5 + seat_finish_lag, 0.6)

    seat_x = np.where(
        phase <= seat_drive_end,
        seat_x_range[0] + (seat_x_range[1] - seat_x_range[0]) * (phase / max(seat_drive_end, 1e-6)),
        seat_x_range[1] - (seat_x_range[1] - seat_x_range[0]) * ((phase - seat_drive_end) / max(1.0 - seat_drive_end, 1e-6)),
    )

    # Handle X: 0 (catch) -> max (finish) -> 0 (catch)
    handle_x = np.where(
        phase <= drive_end,
        handle_x_range[0] + (handle_x_range[1] - handle_x_range[0]) * (phase / drive_end),
        handle_x_range[1] - (handle_x_range[1] - handle_x_range[0]) * ((phase - drive_end) / (1.0 - drive_end)),
    )

    # Trunk Angle (Degrees from Vertical)
    if trunk_angles is None:
        # Default "ideal" progression with legs-first sequencing.
        # Catch -30°, Finish 15°.
        catch_angle, finish_angle = -30.0, 15.0

        # Align trunk peak with the *seat-defined* finish moment.
        # Map phase into a seat-timed stroke-phase where:
        # - 0..seat_drive_end is drive
        # - seat_drive_end..1 is recovery
        seat_timed_phase = np.where(
            phase <= seat_drive_end,
            0.5 * (phase / max(seat_drive_end, 1e-6)),
            0.5 + 0.5 * ((phase - seat_drive_end) / max(1.0 - seat_drive_end, 1e-6)),
        )

        trunk_angle = _trunk_angle_legs_first_progression(seat_timed_phase, catch_angle, finish_angle, drive_hold=0.35)
    elif isinstance(trunk_angles, (tuple, list)):
        catch_angle, finish_angle = trunk_angles
        plateau = 0.05
        trunk_angle = np.where(
            phase <= 0.5 - plateau,
            catch_angle + (finish_angle - catch_angle) * (phase / (0.5 - plateau)),
            np.where(
                phase <= 0.5 + plateau,
                finish_angle,
                finish_angle - (finish_angle - catch_angle) * ((phase - (0.5 + plateau)) / (0.5 - plateau)),
            ),
        )
    else:
        # trunk_angles is already an array
        trunk_angle = trunk_angles

    # Y coordinates (camera frame, smaller Y is "higher" on screen, deeper in boat is larger Y)
    # But analysis.py calculates angle from dx, dy where dy = Shoulder_Y - Seat_Y
    # Shoulder_Y is usually above Seat_Y (smaller Y value)
    seat_y = np.zeros(num_points)  # Seat at baseline Y=0

    # Shoulder_X = Seat_X + L * sin(angle)
    # Shoulder_Y = Seat_Y + L * cos(angle)
    # Real data: Shoulder_Y is higher (more positive) than Seat_Y
    L = 100
    rad = np.radians(trunk_angle)
    shoulder_x = seat_x + L * np.sin(rad)
    shoulder_y = seat_y + L * np.cos(rad)  # Positive because shoulder is above seat

    # Handle Y (depth)
    # Ideal: flat drive (Y_drive), flat recovery (Y_recovery)
    # Drive phase: constant Y_drive. Recovery phase: constant Y_recovery.
    y_drive = float(handle_y_range[1])  # "Deeper"
    y_recovery = float(handle_y_range[0])  # "Higher"
    handle_y = np.where(phase <= 0.5, y_drive, y_recovery)
    if handle_y_noise != 0:
        handle_y += np.random.normal(0, handle_y_noise, num_points)

    data = {
        'Handle/0/X': handle_x,
        'Handle/0/Y': handle_y,
        'Shoulder/0/X': shoulder_x,
        'Shoulder/0/Y': shoulder_y,
        'Seat/0/X': seat_x,
        'Seat/0/Y': seat_y,
    }
    return pd.DataFrame(data)


def get_trunk_scenarios():
    return {
        'Ideal Technique': {
            'angles': (-30, 15),
            'short': 'Strong forward lean, stable finish.',
            'description': (
                'The rower achieves a strong forward lean at the catch (-30°) and a stable lean back at the finish (15°).'
            ),
        },
        'Slow Hand Away': {
            'angles': (-30, 15),
            'short': 'Trunk rocks over late at the end of recovery.',
            'description': (
                'Slow hand away: Slow body swing after finish (trunk rocks over just when '
                'arrives to the catch angle just at the end of recovery).'
            ),
        },
        'Short Catch (Limited Reach)': {
            'angles': (-15, 15),
            'short': 'Sitting too upright at the catch.',
            'description': (
                'The rower is sitting too upright at the catch. This limits the stroke length '
                'and prevents full power from the legs.'
            ),
        },
        'Over-lean at Finish': {
            'angles': (-30, 25),
            'short': 'Leaning back too far at the finish.',
            'description': (
                'The rower leans back too far at the finish (25°). This is unstable and makes '
                'it difficult to recover quickly for the next stroke.'
            ),
        },
        'No Separation': {
            'angles': (-30, 15),
            'short': 'Opening upper body immediately at catch.',
            'description': (
                'The rower opens the upper body immediately at the catch before the legs have finished their drive phase.'
            ),
        },
        'Rigid Trunk': {
            'angles': (0, 5),
            'short': 'Very little upper body motion.',
            'description': 'The rower has very little upper body motion throughout the stroke, missing out on power and length.',
        },
    }


def get_coordination_scenarios():
    # To simulate "shooting the slide", Seat_X should move fast while Handle_X stays behind.
    # This requires more complex generation than a simple 0-1 phase.
    return {
        'Ideal Coordination': 'Legs and arms connected. Seat and handle accelerate together.',
        'Shooting the Slide': 'Seat moves early while handle lags. Loss of core connection.',
        'Arm-Only Drive': 'Handle moves while seat stays back. No leg power used.',
    }


def get_trajectory_scenarios():
    return {
        'Ideal Path': 'A clean rectangular path with consistent depth and clean extraction.',
        'Digging Deep': 'The handle goes too deep in the middle of the drive phase.',
        'Skying the Catch': "The handle is too high before the catch, missing the 'front' of the stroke.",
    }


def get_consistency_scenarios():
    return {
        'Professional (Robotic)': 'Every stroke is identical in length and timing.',
        'Inconsistent Length': 'Variation in how far the rower goes back or forward each stroke.',
        'Rushed Recovery': 'The time spent on recovery is too short compared to the drive.',
    }


def create_scenario_data(scenario_type, subtype, handle_x_range=None, seat_x_range=None):
    num_cycles = 5
    cycle_points = 100

    cycles = []

    if scenario_type == 'Trunk':
        cycles = _generate_trunk_scenario(subtype, handle_x_range, seat_x_range, num_cycles, cycle_points)
    elif scenario_type == 'Coordination':
        cycles = _generate_coordination_scenario(subtype, handle_x_range, seat_x_range, num_cycles, cycle_points)
    elif scenario_type == 'Trajectory':
        cycles = _generate_trajectory_scenario(subtype, handle_x_range, seat_x_range, num_cycles, cycle_points)
    elif scenario_type == 'Consistency':
        cycles = _generate_consistency_scenario(subtype, handle_x_range, seat_x_range, num_cycles, cycle_points)
    if not cycles:
        # Default to Trunk - Ideal if unknown
        cycles = _generate_trunk_scenario('Ideal Technique', None, None, num_cycles, cycle_points)

    full_df: pd.DataFrame = pd.concat(cycles).reset_index(drop=True)

    # process_rowing_data uses a rolling(10).mean() window which dampens peaks
    # near the edges of cyclic data. We can pre-pad and post-pad the dataframe
    # with cycle data to ensure that when it gets smoothed, the internal peaks
    # are preserved properly, especially the catch/finish angles.
    buffer_start = full_df.iloc[-20:].copy()  # Use end of stroke to pad start
    buffer_end = full_df.iloc[:20].copy()  # Use start of stroke to pad end

    full_df = pd.concat([buffer_start, full_df, buffer_end]).reset_index(drop=True)

    return full_df


def _generate_trunk_scenario(subtype, h_range, s_range, num_cycles, cycle_points):
    scenarios = get_trunk_scenarios()
    angles = scenarios[subtype]['angles']
    cycles = []
    h_range = h_range if h_range else (150, 550)
    s_range = s_range if s_range else (250, 550)

    for _ in range(num_cycles):
        angles_with_noise = (angles[0] + np.random.normal(0, 0.5), angles[1] + np.random.normal(0, 0.5))
        phase = get_stroke_phase(cycle_points)

        if subtype == 'No Separation':
            trunk_angle = np.where(
                phase <= 0.25,
                angles_with_noise[0] + (angles_with_noise[1] - angles_with_noise[0]) * (phase / 0.25),
                np.where(
                    phase <= 0.55,
                    angles_with_noise[1],
                    angles_with_noise[1] - (angles_with_noise[1] - angles_with_noise[0]) * ((phase - 0.55) / 0.45),
                ),
            )
        elif subtype == 'Rigid Trunk':
            trunk_angle = angles_with_noise
        elif subtype == 'Slow Hand Away':
            trunk_angle = _trunk_angle_legs_first_progression(
                phase,
                catch_angle=float(angles_with_noise[0]),
                finish_angle=float(angles_with_noise[1]),
                drive_hold=0.40,
                finish_hold=0.1,
                rec_return=0.8,
            )
        else:
            trunk_angle = _trunk_angle_legs_first_progression(
                phase, catch_angle=float(angles_with_noise[0]), finish_angle=float(angles_with_noise[1]), drive_hold=0.35
            )

        cycles.append(
            generate_cycle_df(num_points=cycle_points, trunk_angles=trunk_angle, handle_x_range=h_range, seat_x_range=s_range)
        )
    return cycles


def _generate_coordination_scenario(subtype, h_range, s_range, num_cycles, cycle_points):
    h_range = h_range if h_range else (150, 550)
    s_range = s_range if s_range else (250, 550)
    cycles = []
    for _ in range(num_cycles):
        df = generate_cycle_df(num_points=cycle_points, handle_x_range=h_range, seat_x_range=s_range)
        drive_points = int(cycle_points / 3)
        if subtype == 'Shooting the Slide':
            phase = np.linspace(0, 1, drive_points)
            s_start, s_end = s_range[0], s_range[1]
            seat_x_drive = s_start + (s_end - s_start) * (phase**0.4)
            df.iloc[:drive_points, df.columns.get_loc('Seat/0/X')] = seat_x_drive
        elif subtype == 'Arm-Only Drive':
            wait_points = int(drive_points * 0.4)
            s_start, s_end = s_range[0], s_range[1]
            seat_x_drive = np.full(drive_points, s_start)
            seat_x_drive[wait_points:] = np.linspace(s_start, s_end, drive_points - wait_points)
            df.iloc[:drive_points, df.columns.get_loc('Seat/0/X')] = seat_x_drive
        cycles.append(df)
    return cycles


def _generate_trajectory_scenario(subtype, h_range, s_range, num_cycles, cycle_points):
    h_range = h_range if h_range else (150, 550)
    s_range = s_range if s_range else (250, 550)
    cycles = []
    for _ in range(num_cycles):
        df = generate_cycle_df(num_points=cycle_points, handle_x_range=h_range, seat_x_range=s_range)
        drive_points = int(cycle_points / 3)
        if subtype == 'Digging Deep':
            depth = 30 * np.sin(np.linspace(0, np.pi, drive_points))
            df.iloc[:drive_points, df.columns.get_loc('Handle/0/Y')] += depth
        elif subtype == 'Skying the Catch':
            recovery_points = cycle_points - drive_points
            height = -40 * np.sin(np.linspace(0, np.pi, recovery_points))
            df.iloc[drive_points:, df.columns.get_loc('Handle/0/Y')] += height
        cycles.append(df)
    return cycles


def _generate_consistency_scenario(subtype, h_range, s_range, num_cycles, _cycle_points):
    s_start = s_range[0] if s_range else 250
    s_end = s_range[1] if s_range else 550
    h_range = h_range if h_range else (s_start - 100, s_end)
    cycles = []
    for _ in range(num_cycles):
        s_end_var = s_end + np.random.normal(0, 30) if subtype == 'Inconsistent Length' else s_end
        if subtype == 'Rushed Recovery':
            df_drive = generate_cycle_df(num_points=100, seat_x_range=(s_start, s_end_var), handle_x_range=h_range)
            df = pd.concat([df_drive.iloc[:33], df_drive.iloc[67:100]]).reset_index(drop=True)
        else:
            df = generate_cycle_df(num_points=100, seat_x_range=(s_start, s_end_var), handle_x_range=h_range)
        cycles.append(df)
    return cycles
