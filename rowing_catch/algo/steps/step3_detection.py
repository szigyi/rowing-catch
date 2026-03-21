import numpy as np
import pandas as pd

from rowing_catch.algo.helpers import _detect_catches_by_seat_reversal, _interpolate_small_gaps


def step3_detect_catches(df: pd.DataFrame,
                         min_separation: int | None = None,
                         window: int = 10) -> tuple[pd.DataFrame, np.ndarray]:
    """Detect catch indices as local minima of Seat_X_Smooth.

    The catch is the point where the seat reaches its most forward position
    (minimum X) and reverses direction — the standard rowing catch definition.
    ``Seat_X_Smooth`` has exactly **one** local minimum per stroke, so this
    produces one catch detection per stroke cycle.

    ``Stroke_Compression`` (|Seat_X − Handle_X|) is also computed and stored
    on the DataFrame for diagnostic / visualisation purposes, but is **not**
    used for detection.  It was previously used for detection, which caused
    spurious double-detections because the compression is near-zero at both
    the catch *and* the finish (handle drawn back to seat level), yielding
    two minima per stroke.

    Args:
        df: Smoothed DataFrame (output of :func:`step2_smooth`).
        min_separation: Minimum number of samples between consecutive catches.
            Defaults to ``max(40, window * 4)``.
        window: Smoothing window used previously (needed to compute the default
            ``min_separation``).

    Returns:
        A tuple ``(df, catch_indices)`` where *df* has a new
        ``'Stroke_Compression'`` column (diagnostic only) and *catch_indices*
        is an integer ndarray of row positions within *df*.
    """
    if min_separation is None:
        min_separation = max(40, window * 4)

    df = df.copy()
    # Interpolate small gaps to avoid derivative spikes/missed reversals.
    df['Seat_X_Smooth'] = _interpolate_small_gaps(df['Seat_X_Smooth'].to_numpy())
    if 'Seat_Y_Smooth' in df.columns:
        df['Seat_Y_Smooth'] = _interpolate_small_gaps(df['Seat_Y_Smooth'].to_numpy())

    # Keep Stroke_Compression for diagnostic visualisation only.
    df['Stroke_Compression'] = np.abs(df['Seat_X_Smooth'] - df['Handle_X_Smooth'])

    # Use Seat_X_Smooth for detection: one minimum per stroke, exactly at the catch.
    # Pass Seat_Y_Smooth as secondary signal for robust validation.
    catch_indices = _detect_catches_by_seat_reversal(
        df['Seat_X_Smooth'],
        min_separation=min_separation,
        seat_y=df.get('Seat_Y_Smooth', None),
    )
    return df, catch_indices