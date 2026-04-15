"""
Scenario-driven configuration for diagram markers and explanations.
These annotations only appear when a Global Scenario Overlay is selected.
"""

DIAGRAM_ANNOTATIONS = {
    'Ideal Technique': {
        'trunk_angle_separation_plot': [
            {
                'x_type': 'point',
                'point_name': 'catch',
                'text': 'Optimal Reach',
                'description': 'Full forward lean with core stability.',
                'color': 'green',
                'offset': (-20, 30),
            },
            {
                'x_type': 'percentage_of_cycle',
                'x': 15,
                'text': 'Early Body Over',
                'description': 'Posture set before the legs rise in recovery.',
                'color': '#636EFA',
            },
            {
                'x_type': 'point',
                'point_name': 'finish',
                'text': 'Stable Finish',
                'description': 'Held angle provides a platform for the hands.',
                'color': '#EF553B',
            },
        ],
        'power_accumulation_plot': [
            {
                'x_type': 'percentage_of_drive',
                'x': 25,
                'text': 'Legs Drive',
                'description': 'Heavy contribution early in the stroke.',
                'color': 'green',
            },
            {
                'x_type': 'percentage_of_drive',
                'x': 60,
                'text': 'Smooth Swing',
                'description': 'Body takes over as legs reach full extension.',
                'color': 'green',
            },
        ],
    },
    'Slow Hand Away': {
        'trunk_angle_separation_plot': [
            {
                'x_type': 'percentage_of_cycle',
                'x': 70,
                'text': 'Late Rock-over',
                'description': 'Body still leaning back while moving up the slide.',
                'color': 'orange',
            },
            {
                'x_type': 'point',
                'point_name': 'finish',
                'text': 'Hands Stuck',
                'description': 'Pausing at the finish breaks the rhythm.',
                'color': 'red',
            },
        ],
        'recovery_control': [
            {
                'x_type': 'percentage_of_recovery',
                'x': 30,
                'text': 'No Hands Lead',
                'description': 'Hands must move away before the body swings.',
                'color': 'red',
            }
        ],
    },
    'Short Catch (Limited Reach)': {
        'trunk_angle_separation_plot': [
            {
                'x_type': 'point',
                'point_name': 'catch',
                'text': 'Limited Reach',
                'description': 'Sitting too upright; losing stroke length.',
                'color': 'red',
                'offset': (-10, 40),
            }
        ],
        'handle_seat_distance_plot': [
            {
                'x_type': 'point',
                'point_name': 'catch',
                'text': 'Short Stroke',
                'description': 'Missing effective length at the catch.',
                'color': 'red',
            }
        ],
    },
    'Over-lean at Finish': {
        'trunk_angle_separation_plot': [
            {
                'x_type': 'point',
                'point_name': 'finish',
                'text': 'Extreme Lean Back',
                'description': 'Unstable posture; inefficient recovery.',
                'color': 'red',
            }
        ]
    },
    'No Separation': {
        'trunk_angle_separation_plot': [
            {
                'x_type': 'percentage_of_drive',
                'x': 20,
                'text': 'Opening Early',
                'description': 'Body swinging before legs halfway down.',
                'color': 'red',
            }
        ],
        'power_accumulation_plot': [
            {
                'x_type': 'percentage_of_drive',
                'x': 20,
                'text': 'Lost Leg Potential',
                'description': 'Trunk takes over too soon; leg drive cut short.',
                'color': 'orange',
            }
        ],
    },
    'Rigid Trunk': {
        'trunk_angle_separation_plot': [
            {
                'x_type': 'percentage_of_cycle',
                'x': 50,
                'text': 'Static Posture',
                'description': 'Missing power from hip swing.',
                'color': 'orange',
            }
        ]
    },
    # --- Trajectory Scenarios ---
    'Ideal Path': {
        'handle_trajectory': [
            {
                'x_type': 'percentage_of_drive',
                'x': 10,
                'text': 'Sharp Catch',
                'description': 'Blade enters water early and cleanly.',
                'color': 'green',
                'offset': (0, -40),
            },
            {
                'x_type': 'percentage_of_drive',
                'x': 50,
                'text': 'Consistent Depth',
                'description': 'Blade stays at optimal depth throughout drive.',
                'color': '#333333',
                'offset': (0, -40),
            },
            {
                'x_type': 'percentage_of_drive',
                'x': 90,
                'text': 'Clean Extraction',
                'description': 'Lifting handle away from finish.',
                'color': 'red',
                'offset': (0, -40),
            },
        ]
    },
    'Digging Deep': {
        'handle_trajectory': [
            {
                'x_type': 'percentage_of_drive',
                'x': 50,
                'text': 'Too Deep (Dragging)',
                'description': 'Handle too low; blade dragging through water.',
                'color': 'red',
                'offset': (0, 40),
            },
            {
                'x_type': 'percentage_of_drive',
                'x': 80,
                'text': 'Heavy Finish',
                'description': 'Blade buried too deep to exit cleanly.',
                'color': 'red',
                'offset': (20, 40),
            },
        ]
    },
    'Skying the Catch': {
        'handle_trajectory': [
            {
                'x_type': 'percentage_of_drive',
                'x': 5,
                'text': 'Handle Too High',
                'description': 'Reaching handle up before catch; skying blade.',
                'color': 'red',
                'offset': (-40, -40),
            },
            {
                'x_type': 'percentage_of_drive',
                'x': 15,
                'text': 'Late Blade Entry',
                'description': 'Missing the front of the catch.',
                'color': 'red',
                'offset': (20, -40),
            },
        ]
    },
    # --- Coordination Scenarios ---
    'Ideal Coordination': {
        'kinetic_chain_plot': [
            {
                'x_type': 'percentage_of_drive',
                'x': 10,
                'text': 'Connected Drive',
                'description': 'Seat and handle move in unison.',
                'color': 'green',
            },
        ]
    },
    'Shooting the Slide': {
        'kinetic_chain_plot': [
            {
                'x_type': 'percentage_of_drive',
                'x': 20,
                'text': 'Seat Rushing',
                'description': 'Seat moving way faster than handle.',
                'color': 'red',
                'offset': (-20, 30),
            },
            {
                'x_type': 'percentage_of_drive',
                'x': 40,
                'text': 'Disconnected',
                'description': 'Leg power not reaching the handle.',
                'color': 'red',
                'offset': (20, 30),
            },
        ]
    },
    'Arm-Only Drive': {
        'kinetic_chain_plot': [
            {
                'x_type': 'percentage_of_drive',
                'x': 20,
                'text': 'Static Seat',
                'description': 'No leg drive detected.',
                'color': 'red',
            },
        ],
        'power_accumulation_plot': [
            {
                'x_type': 'percentage_of_drive',
                'x': 30,
                'text': 'Missing Legs',
                'description': 'First 50% of stroke should be legs.',
                'color': 'red',
            },
        ],
    },
    # --- Consistency Scenarios ---
    'Professional (Robotic)': {
        'recovery_control': [
            {
                'x_type': 'percentage_of_recovery',
                'x': 50,
                'text': 'Perfect Control',
                'description': 'Stable, repeatable slide speed.',
                'color': 'green',
            },
        ]
    },
    'Rushed Recovery': {
        'recovery_control': [
            {
                'x_type': 'percentage_of_recovery',
                'x': 30,
                'text': 'Rushing!',
                'description': 'Too fast early in the recovery.',
                'color': 'red',
                'offset': (0, 30),
            },
        ]
    },
}
