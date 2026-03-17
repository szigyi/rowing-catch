# Signal Smoothing Improvement Plan: Butterworth Filter

## Objective
Replace the naive `rolling().mean()` in `process_rowing_data` (in `rowing_catch/algo/analysis.py`) with a biomechanically standard **zero-phase low-pass Butterworth filter**. 

## Why a Butterworth Filter?
The current approach (`df.rolling(10).mean()`) introduces two major distortions:
1. **Amplitude Dampening:** Sharp peaks (such as the finish layback or the catch reach) are artificially flattened because the rolling window incorporates surrounding, lower-amplitude points.
2. **Phase Shift (Lag):** A trailing rolling average shifts data forward in time. This means the algorithm detects catch and finish moments *after* they theoretically happen in reality.

A **zero-phase Butterworth filter** (applied forwards and backwards using `scipy.signal.filtfilt`) solves both:
- It eliminates the time delay completely (zero phase shift).
- It allows genuine low-frequency stroke mechanics through without heavily suppressing peaks, while successfully rejecting high-frequency camera or sensor noise.

## Proposed Implementation Details

### 1. Update Dependencies
We need to ensure `scipy` is available in the project for the signal processing module.

### 2. Implement Filter Function
Add a new utility function in `rowing_catch/algo/analysis.py`:

```python
from scipy.signal import butter, filtfilt
import pandas as pd

def apply_butterworth_filter(series: pd.Series, cutoff_freq: float = 3.0, sample_rate: float = 30.0, order: int = 4) -> pd.Series:
    """
    Applies a zero-phase low-pass Butterworth filter.
    
    Args:
        series: The noisy raw data.
        cutoff_freq: Frequency above which noise is filtered (e.g., 3 Hz).
        sample_rate: Frames per second of the raw data (e.g., 30 FPS).
        order: Order of the filter.
    """
    if series.isna().all():
        return series
        
    nyquist = 0.5 * sample_rate
    normal_cutoff = cutoff_freq / nyquist
    
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    
    # Fill NAs briefly to avoid filtfilt errors, or drop them
    filled = series.interpolate(method='linear').fillna(method='bfill').fillna(method='ffill')
    smoothed = filtfilt(b, a, filled)
    
    return pd.Series(smoothed, index=series.index)
```

### 3. Replace Rolling Mean
Update the preprocessing step in `process_rowing_data`:

```python
    # Preprocessing & Smoothing
    # Assuming video is recorded at ~30 fps, a cutoff of 2-4 Hz is standard for rowing kinematics.
    cols_to_smooth = ['Handle_X', 'Handle_Y', 'Shoulder_X', 'Shoulder_Y', 'Seat_X', 'Seat_Y']
    for col in cols_to_smooth:
        if col in df.columns:
            # df[f'{col}_Smooth'] = df[col].rolling(window).mean() # OLD METHOD
            df[f'{col}_Smooth'] = apply_butterworth_filter(df[col], cutoff_freq=3.0, sample_rate=30.0)
```

## Parameter Considerations (Tuning)
- **`sample_rate`**: This needs to match the actual FPS of the upstream video input for the filter to behave predictably. If the app handles variable framerates, this value might need to be passed down dynamically rather than hardcoded.
- **`cutoff_freq`**: A typical rowing stroke takes 2-3 seconds (< 1Hz fundamental frequency). A cutoff around `2.0 Hz - 4.0 Hz` generally leaves the true biomechanics intact while stripping rapid camera shake or AI tracking jitter. We should experiment with this value once real data is available.
