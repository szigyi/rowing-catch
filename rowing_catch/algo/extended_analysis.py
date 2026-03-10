import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats

# 1. LOAD DATA
df = pd.read_csv('Szabi/2023.12.27.Szabi_20strokesPerMinute_trajectory.csv')
df = df.rename(columns={
    'Handle/0/X': 'Handle_X', 'Handle/0/Y': 'Handle_Y', 
    'Shoulder/0/X': 'Shoulder_X', 'Shoulder/0/Y': 'Shoulder_Y', 
    'Seat/0/X': 'Seat_X', 'Seat/0/Y': 'Seat_Y'
})
df.insert(0, 'Index', range(0, len(df)))
df = df.set_index('Index')

# 2. PREPROCESSING & SMOOTHING
window = 10
cols_to_smooth = ['Handle_X', 'Handle_Y', 'Shoulder_X', 'Shoulder_Y', 'Seat_X', 'Seat_Y']
for col in cols_to_smooth:
    df[f'{col}_Smooth'] = df[col].rolling(window).mean()

# 3. STROKE DETECTION (From Original Notebook)
def markStrokeStart(window):
    current = window[1]
    prev = window[0]
    if prev > 100 and current <= 100: # "Hands Away" roughly
        return 100
    else:
        return 0

df['Stroke_Start'] = df['Handle_X_Smooth'].rolling(2).apply(markStrokeStart, raw=True)
stroke_starts = df.loc[df['Stroke_Start'] == 100].index

# Split into individual cycles
cycles = []
for i in range(len(stroke_starts) - 1):
    cycle = df.loc[stroke_starts[i]:stroke_starts[i+1]-1].copy()
    cycle.reset_index(drop=True, inplace=True)
    cycle.index.name = 'Cycle_Index'
    cycles.append(cycle)

# Calculate Average Cycle (standardized length)
min_length = min(c.shape[0] for c in cycles)
avg_cycle = pd.concat([c.iloc[:min_length] for c in cycles]).groupby('Cycle_Index').mean()

# 4. NEW METRICS & ANALYSIS

# A. Biomechanics: Trunk Angle (Approximated from Shoulder and Seat)
# Assuming X is horizontal (positive away from catch) and Y is vertical (positive up)
# Trunk angle relative to vertical (0 deg = upright)
def calc_trunk_angle(row):
    dx = row['Shoulder_X_Smooth'] - row['Seat_X_Smooth']
    dy = row['Shoulder_Y_Smooth'] - row['Seat_Y_Smooth']
    return np.degrees(np.arctan2(dx, dy))

avg_cycle['Trunk_Angle'] = avg_cycle.apply(calc_trunk_angle, axis=1)

# B. Efficiency: Seat vs Handle Velocity (Coordination)
# In the drive, seat and handle should move together initially.
avg_cycle['Handle_X_Vel'] = np.gradient(avg_cycle['Handle_X_Smooth'])
avg_cycle['Seat_X_Vel'] = np.gradient(avg_cycle['Seat_X_Smooth'])
avg_cycle['Coordination_Index'] = avg_cycle['Handle_X_Vel'] - avg_cycle['Seat_X_Vel']

# C. Phase Detection (Catch and Finish)
# Catch: Seat at minimum X (closest to stern/catch)
catch_idx = avg_cycle['Seat_X_Smooth'].idxmin()
# Finish: Seat at maximum X (closest to bow/finish)
finish_idx = avg_cycle['Seat_X_Smooth'].idxmax()

# D. Consistency Metrics
stroke_lengths = [c['Seat_X_Smooth'].max() - c['Seat_X_Smooth'].min() for c in cycles]
stroke_durations = [len(c) for c in cycles]
mean_length = np.mean(stroke_lengths)
std_length = np.std(stroke_lengths)
mean_duration = np.mean(stroke_durations)
std_duration = np.std(stroke_durations)

# 5. VISUALIZATION

# Plot 1: Biomechanical Trunk Angle over Stroke
plt.figure(figsize=(12, 6))
plt.plot(avg_cycle.index, avg_cycle['Trunk_Angle'], label='Trunk Angle (deg)', color='purple')
plt.axvline(catch_idx, color='green', linestyle='--', label='Catch')
plt.axvline(finish_idx, color='red', linestyle='--', label='Finish')
plt.title('Trunk Lean (Biomechanics)')
plt.ylabel('Degrees from Vertical')
plt.xlabel('Stroke Progress (frames)')
plt.legend()
plt.grid(True)
plt.savefig('trunk_angle.png')

# Plot 2: Coordination Curve (Seat vs Handle Velocity)
plt.figure(figsize=(12, 6))
plt.plot(avg_cycle.index, avg_cycle['Handle_X_Vel'], label='Handle Velocity (X)', color='blue')
plt.plot(avg_cycle.index, avg_cycle['Seat_X_Vel'], label='Seat Velocity (X)', color='orange')
plt.axvline(catch_idx, color='green', linestyle='--')
plt.axvline(finish_idx, color='red', linestyle='--')
plt.title('Velocity Coordination (Rower Efficiency)')
plt.ylabel('Velocity (px/frame)')
plt.legend()
plt.grid(True)
plt.savefig('coordination.png')

# Plot 3: 2D Trajectory "Box" Plot (Handle Path)
plt.figure(figsize=(10, 6))
plt.plot(avg_cycle['Handle_X_Smooth'], avg_cycle['Handle_Y_Smooth'], label='Handle Path', color='black')
plt.scatter(avg_cycle.loc[catch_idx, 'Handle_X_Smooth'], avg_cycle.loc[catch_idx, 'Handle_Y_Smooth'], color='green', s=100, label='Catch Point')
plt.scatter(avg_cycle.loc[finish_idx, 'Handle_X_Smooth'], avg_cycle.loc[finish_idx, 'Handle_Y_Smooth'], color='red', s=100, label='Finish Point')
plt.title('Handle Trajectory (Vertical vs Horizontal)')
plt.xlabel('Horizontal Position')
plt.ylabel('Vertical Position')
plt.legend()
plt.gca().invert_yaxis() # Assuming Y increases downwards in some systems, or just for visual clarity
plt.grid(True)
plt.savefig('handle_path.png')

# 6. REPORTING
print(f"--- Consistency Analysis ---")
print(f"Mean Stroke Length: {mean_length:.2f} px (±{std_length:.2f})")
print(f"Mean Stroke Duration: {mean_duration:.2f} frames (±{std_duration:.2f})")
print(f"Variability (CV Length): {(std_length/mean_length)*100:.2f}%")
print(f"--- Timing ---")
drive_len = finish_idx - catch_idx
recovery_len = min_length - drive_len
print(f"Drive: {drive_len} frames ({ (drive_len/min_length)*100:.1f}%)")
print(f"Recovery: {recovery_len} frames ({ (recovery_len/min_length)*100:.1f}%)")
print(f"Ratio: 1:{recovery_len/drive_len:.2f}")

# Trunk Lean Stats
catch_lean = avg_cycle.loc[catch_idx, 'Trunk_Angle']
finish_lean = avg_cycle.loc[finish_idx, 'Trunk_Angle']
print(f"--- Biomechanics ---")
print(f"Trunk Lean at Catch: {catch_lean:.1f}°")
print(f"Trunk Lean at Finish: {finish_lean:.1f}°")
print(f"Total Trunk Range: {abs(finish_lean - catch_lean):.1f}°")
