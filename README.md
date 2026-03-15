# The Rowing Catch - Rowing Analysis Report

## Overview
The Rowing Catch is an application for biomechanical and technical analysis of rowing strokes. It generates a comprehensive PDF-style report for rowers and coaches, focusing on actionable feedback: comparing current performance to ideal technique.

## Features

### 1. Biomechanical & Technical Efficiency (Coach Focused)
- **Trunk Angle & Range Analysis**: Measures the angle between shoulder and seat throughout the stroke. Visualizes ideal zones for catch and finish.
- **Seat vs. Handle Velocity Coordination**: Compares horizontal speed of seat (legs) and handle (arms/back) during the drive. Highlights peak overlap for power efficiency.
- **Handle Trajectory "Box" Plot**: 2D plot of handle’s vertical vs. horizontal path. Shows ideal vs. actual stroke shape, marking catch and finish.

### 2. Consistency & Rhythm (Rower Focused)
- **Stroke Consistency Score (CV)**: Measures variability in stroke length and duration. Visualizes stability vs. professional goal (<2%).
- **Dynamic Drive/Recovery Ratio**: Compares time spent on drive vs. recovery. Shows current vs. ideal ratio (33%/66% at low rates).

### 3. Suggested Future Features
- **Handle Jerk Analysis**: Quantify sudden changes in handle acceleration (requires high-frequency data).
- **Force-Curve Integration**: Overlay handle trajectory with force applied (requires additional hardware).
- **Hip/Knee Angle Biomechanics**: Analyze joint extension sequences (requires joint tracking).

## Usage
1. Launch the app with Streamlit:
   ```bash
   source .venv/bin/activate
   streamlit run app.py
   ```
2. Upload a CSV file from the `resources/` folder (e.g., `2023.12.27.Szabi_20strokesPerMinute_trajectory.csv`).
3. View the technical report and visualizations.

## Example Data
Example CSV files are available in the `resources/` folder:
- `2023.12.27.Szabi_20strokesPerMinute_trajectory.csv`
- `2023.12.27.Szabi_36strokesPerMinute_trajectory.csv`

## Installation
Install runtime dependencies:
   ```bash
   pip install -r requirements.txt
   ```

Optional (local/dev) extras:
   ```bash
   pip install -r requirements-dev.txt
   ```

## License
MIT License.

## Authors
Szabolcs Szilagyi and contributors.

