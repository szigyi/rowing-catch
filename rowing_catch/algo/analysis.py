import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def process_rowing_data(df):
    # Column mapping
    column_map = {
        'Handle/0/X': 'Handle_X', 'Handle/0/Y': 'Handle_Y', 
        'Shoulder/0/X': 'Shoulder_X', 'Shoulder/0/Y': 'Shoulder_Y', 
        'Seat/0/X': 'Seat_X', 'Seat/0/Y': 'Seat_Y'
    }
    df = df.rename(columns=column_map)
    
    # Preprocessing & Smoothing
    window = 10
    cols_to_smooth = ['Handle_X', 'Handle_Y', 'Shoulder_X', 'Shoulder_Y', 'Seat_X', 'Seat_Y']
    for col in cols_to_smooth:
        if col in df.columns:
            df[f'{col}_Smooth'] = df[col].rolling(window).mean()
    
    # Drop rows with NaN from smoothing
    df = df.dropna(subset=[f'{col}_Smooth' for col in cols_to_smooth])
    
    # Stroke Detection
    def mark_stroke_start(window):
        current = window[1]
        prev = window[0]
        if prev > 100 and current <= 100:
            return 100
        else:
            return 0

    df['Stroke_Start'] = df['Handle_X_Smooth'].rolling(2).apply(mark_stroke_start, raw=True)
    stroke_starts = df.loc[df['Stroke_Start'] == 100].index
    
    if len(stroke_starts) < 2:
        return None # Not enough data for cycles

    # Split into individual cycles
    cycles = []
    for i in range(len(stroke_starts) - 1):
        cycle = df.loc[stroke_starts[i]:stroke_starts[i+1]-1].copy()
        cycle.reset_index(drop=True, inplace=True)
        cycle.index.name = 'Cycle_Index'
        cycles.append(cycle)
        
    # Standardize length for average cycle
    min_length = min(c.shape[0] for c in cycles)
    avg_cycle = pd.concat([c.iloc[:min_length] for c in cycles]).groupby('Cycle_Index').mean()
    
    # Metrics
    # Trunk Angle
    def calc_trunk_angle(row):
        dx = row['Shoulder_X_Smooth'] - row['Seat_X_Smooth']
        dy = row['Shoulder_Y_Smooth'] - row['Seat_Y_Smooth']
        return np.degrees(np.arctan2(dx, dy))

    avg_cycle['Trunk_Angle'] = avg_cycle.apply(calc_trunk_angle, axis=1)
    
    # Velocities
    avg_cycle['Handle_X_Vel'] = np.gradient(avg_cycle['Handle_X_Smooth'])
    avg_cycle['Seat_X_Vel'] = np.gradient(avg_cycle['Seat_X_Smooth'])
    
    # Catch and Finish
    catch_idx = avg_cycle['Seat_X_Smooth'].idxmin()
    finish_idx = avg_cycle['Seat_X_Smooth'].idxmax()
    
    # Consistency
    stroke_lengths = [c['Seat_X_Smooth'].max() - c['Seat_X_Smooth'].min() for c in cycles]
    stroke_durations = [len(c) for c in cycles]
    cv_length = (np.std(stroke_lengths) / np.mean(stroke_lengths)) * 100
    
    # Drive/Recovery
    drive_len = finish_idx - catch_idx
    recovery_len = min_length - drive_len
    
    results = {
        'avg_cycle': avg_cycle,
        'cycles': cycles,
        'catch_idx': catch_idx,
        'finish_idx': finish_idx,
        'cv_length': cv_length,
        'drive_len': drive_len,
        'recovery_len': recovery_len,
        'min_length': min_length,
        'mean_duration': np.mean(stroke_durations)
    }
    return results

def get_traffic_light(value, ideal, yellow_threshold=15, green_threshold=5):
    deviation = abs(value - ideal) / ideal * 100
    if deviation <= green_threshold:
        return "Green", "✅"
    elif deviation <= yellow_threshold:
        return "Yellow", "⚠️"
    else:
        return "Red", "🚨"
