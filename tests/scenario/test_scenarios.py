import numpy as np
import pandas as pd
import pytest
from rowing_catch.scenario.scenarios import (
    get_stroke_phase,
    _trunk_angle_legs_first_progression,
    generate_cycle_df,
    get_trunk_scenarios,
    get_coordination_scenarios,
    get_trajectory_scenarios,
    get_consistency_scenarios,
    create_scenario_data
)

def test_get_stroke_phase():
    """Test time warping for drive_ratio."""
    num_points = 101
    drive_ratio = 1/3
    phase = get_stroke_phase(num_points, drive_ratio=drive_ratio)
    
    assert len(phase) == num_points
    assert phase[0] == 0.0
    assert phase[-1] == 1.0
    
    # At index corresponding to drive_ratio, phase should be 0.5
    mid_idx = int(num_points * drive_ratio)
    assert np.isclose(phase[mid_idx], 0.5, atol=0.05)

def test_trunk_angle_legs_first_progression():
    """Test the sequencing-aware trunk angle trace."""
    phase = np.linspace(0, 1, 100)
    catch_angle = -30.0
    finish_angle = 15.0
    
    angles = _trunk_angle_legs_first_progression(
        phase, catch_angle, finish_angle, drive_hold=0.35, finish_hold=0.05, rec_return=0.25
    )
    
    assert len(angles) == 100
    assert np.isclose(angles[0], catch_angle)
    # At phase=0.5 (end of drive), it should be finish_angle
    assert np.isclose(angles[49], finish_angle, atol=1.0)
    
    # Recovery return check
    # phase=0.5 + 0.5*0.25 = 0.625 should be back to catch_angle
    assert np.isclose(angles[75], catch_angle, atol=1.0)

def test_generate_cycle_df_basic():
    """Test generating a single cycle DataFrame."""
    num_points = 50
    df = generate_cycle_df(num_points=num_points)
    
    expected_cols = [
        'Handle/0/X', 'Handle/0/Y',
        'Shoulder/0/X', 'Shoulder/0/Y',
        'Seat/0/X', 'Seat/0/Y'
    ]
    for col in expected_cols:
        assert col in df.columns
    
    assert len(df) == num_points
    
    # Check ranges
    assert df['Seat/0/X'].min() >= 0
    assert df['Seat/0/X'].max() <= 300
    assert df['Handle/0/X'].max() <= 400

def test_get_scenarios_functions():
    """Verify scenario dictionaries are returned correctly."""
    assert isinstance(get_trunk_scenarios(), dict)
    assert "Ideal Technique" in get_trunk_scenarios()
    
    assert isinstance(get_coordination_scenarios(), dict)
    assert isinstance(get_trajectory_scenarios(), dict)
    assert isinstance(get_consistency_scenarios(), dict)

@pytest.mark.parametrize("scenario_type, subtype", [
    ("Trunk", "Ideal Technique"),
    ("Trunk", "No Separation"),
    ("Trunk", "Rigid Trunk"),
    ("Trunk", "Slow Hand Away"),
    ("Coordination", "Shooting the Slide"),
    ("Coordination", "Arm-Only Drive"),
    ("Trajectory", "Digging Deep"),
    ("Trajectory", "Skying the Catch"),
    ("Consistency", "Professional (Robotic)"),
    ("Consistency", "Inconsistent Length"),
    ("Consistency", "Rushed Recovery"),
    ("Unknown", "Default")
])
def test_create_scenario_data(scenario_type, subtype):
    """Test data generation for all scenario types and subtypes."""
    df = create_scenario_data(scenario_type, subtype)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 100 # Should have multiple cycles + padding
    
    expected_cols = [
        'Handle/0/X', 'Handle/0/Y',
        'Shoulder/0/X', 'Shoulder/0/Y',
        'Seat/0/X', 'Seat/0/Y'
    ]
    for col in expected_cols:
        assert col in df.columns

def test_generate_cycle_df_with_custom_angles():
    """Test generate_cycle_df with explicit trunk_angles array."""
    num_points = 20
    custom_angles = np.full(num_points, 10.0)
    df = generate_cycle_df(num_points=num_points, trunk_angles=custom_angles)
    
    # Calculate trunk angle from shoulder and seat to verify it matches input
    # In generate_cycle_df: 
    # shoulder_x = seat_x + L * sin(rad)
    # shoulder_y = seat_y + L * cos(rad)
    # trunk_angle = atan2(dx, dy)
    dx = df['Shoulder/0/X'] - df['Seat/0/X']
    dy = df['Shoulder/0/Y'] - df['Seat/0/Y']
    calc_angles = np.degrees(np.arctan2(dx, dy))
    
    np.testing.assert_allclose(calc_angles, custom_angles, atol=1e-5)
