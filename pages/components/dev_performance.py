import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import altair as alt
from rowing_catch.ui.annotations import DIAGRAM_ANNOTATIONS
from rowing_catch.ui.utils import (
    setup_premium_plot, COLOR_MAIN, COLOR_LEGS, COLOR_TRUNK, COLOR_ARMS, 
    COLOR_HANDLE, COLOR_SEAT, COLOR_CATCH, COLOR_FINISH, COLOR_COMPARE, 
    BG_COLOR_FIGURE, BG_COLOR_AXES, COLOR_TEXT_MAIN, COLOR_TEXT_SUB
)

def _apply_annotations(ax, diagram_key, data, catch_idx=None, finish_idx=None, y_data=None, scenario_name="None"):
    """
    Helper to apply markers and text from DIAGRAM_ANNOTATIONS to an axis.
    Only applies if a scenario is selected.
    """
    if scenario_name == "None" or scenario_name not in DIAGRAM_ANNOTATIONS:
        return

    scenario_configs = DIAGRAM_ANNOTATIONS[scenario_name]
    if diagram_key not in scenario_configs:
        return

    annotations = scenario_configs[diagram_key]
    
    # Get common data characteristics
    n_points = len(data)
    
    # Determine the y-range for normalized placement if y_data is not provided
    y_min, y_max = ax.get_ylim()
    y_range = y_max - y_min
    
    for ann in annotations:
        x_pos = 0
        y_pos = 0
        
        # Calculate X position
        if ann['x_type'] == 'percentage_of_cycle':
            x_idx = int((ann['x'] / 100) * (n_points - 1))
            x_pos = data.index[x_idx]
        elif ann['x_type'] == 'percentage_of_drive':
            if catch_idx is not None and finish_idx is not None:
                drive_len = finish_idx - catch_idx
                x_idx = int(catch_idx + (ann['x'] / 100) * drive_len)
                x_pos = data.index[x_idx] if x_idx < len(data) else data.index[-1]
            else:
                continue
        elif ann['x_type'] == 'percentage_of_recovery':
            if finish_idx is not None:
                rec_len = n_points - finish_idx
                x_idx = int(finish_idx + (ann['x'] / 100) * rec_len)
                x_pos = data.index[x_idx] if x_idx < len(data) else data.index[-1]
            else:
                continue
        elif ann['x_type'] == 'point':
            if ann['point_name'] == 'catch' and catch_idx is not None:
                x_pos = data.index[catch_idx] if catch_idx < len(data) else data.index[-1]
            elif ann['point_name'] == 'finish' and finish_idx is not None:
                x_pos = data.index[finish_idx] if finish_idx < len(data) else data.index[-1]
            else:
                continue
        
        # SPECIAL CASE: For Handle Trajectory diagram, X-axis is Handle_X_Smooth
        if diagram_key == "handle_trajectory" and "Handle_X_Smooth" in data.columns:
            try:
                x_pos = data.loc[x_pos, 'Handle_X_Smooth']
            except:
                pass
        # SPECIAL CASE: For Trunk Angle diagram, X-axis is Seat_X_Smooth
        elif diagram_key == "trunk_angle_separation" and "Seat_X_Smooth" in data.columns:
            # Map the index-based x_pos to the actual Seat Position value
            try:
                x_pos = data.loc[x_pos, 'Seat_X_Smooth']
            except:
                pass
        # Handle cases where X-axis is percentage (Power Accumulation, Recovery)
        elif isinstance(ax.get_xlabel(), str) and "%" in ax.get_xlabel():
            if ann['x_type'] == 'percentage_of_drive' or ann['x_type'] == 'percentage_of_recovery':
                x_pos = ann['x']
            elif ann['x_type'] == 'point':
                x_pos = 0 if ann['point_name'] == 'catch' else 100

        # Calculate Y position (if y_data provided, use it, else pick mid-range)
        if y_data is not None:
            try:
                # Use the original index-based position (which x_idx should contain)
                y_pos = y_data.iloc[int(x_idx)] if 'x_idx' in locals() else y_max - (y_range * 0.1)
            except:
                y_pos = y_max - (y_range * 0.1)
        else:
            y_pos = y_max - (y_range * 0.2)

        # Apply the annotation
        color = ann.get('color', '#333333')
        offset = ann.get('offset', (20, 20))
        
        ax.annotate(
            ann['text'],
            xy=(x_pos, y_pos),
            xytext=offset,
            textcoords='offset points',
            arrowprops=dict(arrowstyle='->', color=color, connectionstyle='arc3,rad=.2', lw=1.5),
            fontsize=10,
            fontweight='bold',
            color=color,
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=color, alpha=0.9, lw=1.5),
            zorder=10
        )

def plot_trunk_angle_separation(avg_cycle, catch_idx, finish_idx, scenario_data=None, scenario_name="None"):
    """Trunk angle vs Seat Position to show separation/timing."""
    fig, ax = setup_premium_plot("Trunk Angle vs Stroke Progress", "Seat Position (mm)", "Trunk Angle (deg)")
    
    # Main Plot
    ax.plot(avg_cycle['Seat_X_Smooth'], avg_cycle['Trunk_Angle'], color=COLOR_TRUNK, linewidth=3, label="Your Data", zorder=5)
    
    # Mark catch/finish
    ax.scatter(avg_cycle.loc[catch_idx, 'Seat_X_Smooth'], avg_cycle.loc[catch_idx, 'Trunk_Angle'], color=COLOR_CATCH, s=100, label="Catch", zorder=6)
    ax.scatter(avg_cycle.loc[finish_idx, 'Seat_X_Smooth'], avg_cycle.loc[finish_idx, 'Trunk_Angle'], color=COLOR_FINISH, s=100, label="Finish", zorder=6)

    if scenario_data is not None:
        ax.plot(scenario_data['Seat_X_Smooth'], scenario_data['Trunk_Angle'], color=COLOR_COMPARE, linestyle='--', alpha=0.7, label=f"Comparison: {scenario_name}", zorder=4)

    ax.legend()
    
    # Apply Annotations
    _apply_annotations(ax, "trunk_angle_separation", avg_cycle, catch_idx, finish_idx, y_data=avg_cycle['Trunk_Angle'], scenario_name=scenario_name)
    
    st.pyplot(fig)
    st.info("**Developing Advice:** Watch for 'Body Over' before the knees come up in recovery. "
            "The angle should drop towards the catch while the seat is still moving backwards.")

def plot_handle_seat_distance(avg_cycle, catch_idx, finish_idx, scenario_data=None, scenario_name="None"):
    """Plots the distance (compression) between handle and seat."""
    fig, ax = setup_premium_plot("Handle-Seat Separation", "Stroke Index", "Distance (mm)")
    
    dist = np.abs(avg_cycle['Handle_X_Smooth'] - avg_cycle['Seat_X_Smooth'])
    ax.plot(avg_cycle.index, dist, color=COLOR_HANDLE, linewidth=2.5, label="Distance")
    ax.fill_between(avg_cycle.index, dist, color=COLOR_HANDLE, alpha=0.1)
    
    if scenario_data is not None:
        s_dist = np.abs(scenario_data['Handle_X_Smooth'] - scenario_data['Seat_X_Smooth'])
        ax.plot(scenario_data.index, s_dist, color=COLOR_COMPARE, linestyle=':', alpha=0.5, label=f"Comparison: {scenario_name}")

    ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', alpha=0.5)
    ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', alpha=0.5)
    ax.legend()
    
    _apply_annotations(ax, "handle_seat_distance", avg_cycle, catch_idx, finish_idx, y_data=dist, scenario_name=scenario_name)
    
    st.pyplot(fig)
    st.info("**Developing Advice:** Maximizing this distance at the catch (compression) without 'over-reaching' "
            "is key to a long effective stroke.")

def plot_handle_trajectory(avg_cycle, catch_idx, finish_idx, scenario_data=None, scenario_name="None"):
    """Vertical vs Horizontal Handle Path (The Box Plot)."""
    fig, ax = setup_premium_plot("Handle Trajectory Path", "Horizontal Position (mm)", "Vertical Position (mm)")
    
    # Calculate Box
    h_x = avg_cycle['Handle_X_Smooth']
    h_y = avg_cycle['Handle_Y_Smooth']
    h_x_min, h_x_max = h_x.min(), h_x.max()
    h_y_min, h_y_max = h_y.min(), h_y.max()
    
    # Standard depth markers (typical 20mm blade depth)
    box_padding = (h_y_max - h_y_min) * 0.1
    ideal_y_drive = h_y_max + box_padding
    ideal_y_recovery = h_y_min - box_padding
    
    # Plot Ideal Box
    ideal_x = [h_x_min, h_x_max, h_x_max, h_x_min, h_x_min]
    ideal_y = [ideal_y_drive, ideal_y_drive, ideal_y_recovery, ideal_y_recovery, ideal_y_drive]
    ax.plot(ideal_x, ideal_y, color=COLOR_COMPARE, linestyle='--', alpha=0.4, label="Reference Path", linewidth=1.5, zorder=1)
    
    # Plot Actual Trajectory
    ax.plot(h_x, h_y, color=COLOR_HANDLE, linewidth=3, label="Your Data", zorder=3)
    
    # Comparison
    if scenario_data is not None:
        ax.plot(scenario_data['Handle_X_Smooth'], scenario_data['Handle_Y_Smooth'], color=COLOR_COMPARE, linestyle=':', alpha=0.6, label=f"Comparison: {scenario_name}", zorder=2)
        
    # Mark catch/finish
    ax.scatter(h_x.iloc[catch_idx], h_y.iloc[catch_idx], color=COLOR_CATCH, s=100, label="Catch", zorder=4)
    ax.scatter(h_x.iloc[finish_idx], h_y.iloc[finish_idx], color=COLOR_FINISH, s=100, label="Finish", zorder=4)
    
    ax.invert_yaxis() # Up is higher, down is deeper
    ax.legend()
    
    # Apply Annotations
    _apply_annotations(ax, "handle_trajectory", avg_cycle, catch_idx, finish_idx, y_data=h_y, scenario_name=scenario_name)
    
    st.pyplot(fig)
    st.info("**Coach's Tip:** A 'rectangular' box means you are extracting the blade cleanly and depth is stable throughout the drive.")

def plot_ratio_consistency(stats):
    """Scatter plot of SPM vs Ratio for all cycles."""
    if 'cycle_details' not in stats or not stats['cycle_details']:
        st.warning("No individual cycle data available for ratio consistency.")
        return

    df = pd.DataFrame(stats['cycle_details']).dropna(subset=['spm', 'drive_recovery_ratio'])
    
    if df.empty:
        st.warning("Insufficient data points for consistency plot.")
        return

    chart = alt.Chart(df).mark_circle(size=100, opacity=0.7, color=COLOR_MAIN).encode(
        x=alt.X('spm:Q', title='Strokes Per Minute (SPM)', scale=alt.Scale(zero=False)),
        y=alt.Y('drive_recovery_ratio:Q', title='Drive/Recovery Ratio', scale=alt.Scale(zero=False)),
        tooltip=['cycle_idx', 'spm', 'drive_recovery_ratio']
    ).properties(
        title="Rhythm Consistency (SPM vs Ratio)",
        width=700,
        height=400,
        background=BG_COLOR_FIGURE
    ).configure_view(
        fill=BG_COLOR_AXES,
        strokeWidth=0
    ).configure_axis(
        grid=True,
        gridColor='#F0F0F0',
        domainColor='#DDDDDD',
        tickColor='#DDDDDD',
        labelColor=COLOR_TEXT_SUB,
        titleColor=COLOR_TEXT_SUB
    ).configure_title(
        color=COLOR_TEXT_MAIN,
        fontSize=14
    )
    
    st.altair_chart(chart, width='stretch')
    st.info("**Performance Insight:** Elite rowers maintain a tight cluster. "
            "A vertical spread means inconsistent rhythm at the same speed. "
            "A horizontal spread means the ratio changes too much with rate.")

def plot_power_accumulation(avg_cycle, catch_idx, finish_idx, scenario_data=None, scenario_name="None"):
    """Stacked power curve: Legs -> Trunk -> Arms."""
    fig, ax = setup_premium_plot("Segmental Power Accumulation", "Drive Progress (%)", "Power Proxy (Watts-like)")
    
    # Only plot drive phase
    drive = avg_cycle.loc[catch_idx:finish_idx].copy()
    if len(drive) < 2:
        st.warning("Drive phase too short for power analysis.")
        return
        
    drive_progress = np.linspace(0, 100, len(drive))
    
    p_legs = drive['Power_Legs'].clip(lower=0)
    p_trunk = drive['Power_Trunk'].clip(lower=0)
    p_arms = drive['Power_Arms'].clip(lower=0)
    
    ax.stackplot(drive_progress, p_legs, p_trunk, p_arms, 
                 labels=['Legs', 'Trunk', 'Arms'], 
                 colors=[COLOR_LEGS, COLOR_TRUNK, COLOR_ARMS],
                 alpha=0.8)
    
    if scenario_data is not None:
        # Show total power of scenario as a dashed line
        s_drive = scenario_data.loc[catch_idx:finish_idx] if len(scenario_data) > finish_idx else scenario_data
        s_total = s_drive['Power_Total'].clip(lower=0)
        s_prog = np.linspace(0, 100, len(s_total))
        ax.plot(s_prog, s_total, color='#333333', linestyle='--', linewidth=1.5, label=f"Comparison: {scenario_name}", alpha=0.6)

    ax.legend(loc='upper right')
    
    # Power accumulation usually uses 0-100% as X
    _apply_annotations(ax, "power_accumulation", drive, catch_idx=0, finish_idx=100, scenario_name=scenario_name)
    
    st.pyplot(fig)
    st.info("**Performance Insight:** The 'Power Curve' should be smooth and convex. "
            "Legs should dominate the first 50%, followed by a smooth handover to the Trunk and finally Arms.")

def plot_kinetic_chain(avg_cycle, catch_idx, finish_idx, scenario_name="None"):
    """Velocities and Acceleration Coordination."""
    fig, ax = setup_premium_plot("Kinetic Chain Coordination", "Stroke Index", "Velocity / Accel")
    
    ax.plot(avg_cycle.index, avg_cycle['Handle_X_Vel'], color=COLOR_HANDLE, label='Handle Vel', linewidth=2.5)
    ax.plot(avg_cycle.index, avg_cycle['Seat_X_Vel'], color=COLOR_SEAT, label='Seat Vel', linewidth=2)
    
    # Secondary axis for Acceleration
    ax2 = ax.twinx()
    ax2.plot(avg_cycle.index, avg_cycle['Handle_X_Accel'], color='#EB55DE', linestyle=':', alpha=0.4, label='Handle Accel')
    ax2.set_ylabel("Acceleration", color='#EB55DE', alpha=0.7)
    ax2.spines['right'].set_visible(True)
    ax2.spines['right'].set_color('#EB55DE')
    
    ax.axvline(catch_idx, color=COLOR_CATCH, linestyle='--', alpha=0.3)
    ax.axvline(finish_idx, color=COLOR_FINISH, linestyle='--', alpha=0.3)
    
    ax.legend(loc='upper left')
    
    _apply_annotations(ax, "kinetic_chain", avg_cycle, catch_idx, finish_idx, y_data=avg_cycle['Handle_X_Vel'], scenario_name=scenario_name)
    
    st.pyplot(fig)

def plot_recovery_control(avg_cycle, finish_idx, scenario_name="None"):
    """Seat velocity during recovery - looking for 'rushing' or 'pausing'."""
    fig, ax = setup_premium_plot("Recovery Slide Control", "Recovery Progress (%)", "Seat Velocity")
    
    # Recovery is from finish to end of cycle
    rec = avg_cycle.loc[finish_idx:].copy()
    if len(rec) < 2:
        st.warning("Recovery phase data missing.")
        return
        
    rec_progress = np.linspace(0, 100, len(rec))
    # Seat velocity is negative during recovery in our coord system usually, let's plot absolute for "speed"
    ax.plot(rec_progress, np.abs(rec['Seat_X_Vel']), color=COLOR_SEAT, linewidth=3, label="Seat Speed")
    ax.fill_between(rec_progress, np.abs(rec['Seat_X_Vel']), color=COLOR_SEAT, alpha=0.1)
    
    ax.set_ylim(bottom=0)
    ax.legend()
    
    _apply_annotations(ax, "recovery_control", rec, finish_idx=0, catch_idx=100, y_data=np.abs(rec['Seat_X_Vel']), scenario_name=scenario_name)
    
    st.pyplot(fig)
    st.info("**Coach's Tip:** Look for a symmetric 'bell curve' on the slide. "
            "A sharp peak early in recovery indicates 'rushing' the slide.")

def plot_performance_metrics(avg_cycle, catch_idx, finish_idx, scenario_name="None"):
    """Jerk, Handle Height, and precise Catch Timing."""
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### Handle Jerk (Smoothness)")
        fig, ax = setup_premium_plot(ylabel="Jerk (mm/s³)", figsize=(5, 4))
        ax.plot(avg_cycle.index, avg_cycle['Handle_X_Jerk'], color='#FF4B4B', linewidth=1.5)
        ax.axvline(catch_idx, color=COLOR_CATCH, alpha=0.3)
        _apply_annotations(ax, "handle_jerk", avg_cycle, catch_idx, finish_idx, y_data=avg_cycle['Handle_X_Jerk'], scenario_name=scenario_name)
        st.pyplot(fig)
    
    with col2:
        st.write("#### Handle Height Stability")
        fig, ax = setup_premium_plot(ylabel="Handle Y (mm)", figsize=(5, 4))
        # High-low during drive
        drive_y = avg_cycle.loc[catch_idx:finish_idx, 'Handle_Y_Smooth']
        ax.boxplot(drive_y, patch_artist=True, boxprops=dict(facecolor=COLOR_HANDLE, alpha=0.5))
        ax.set_xticks([])
        st.pyplot(fig)
    
    st.info("**High Performance:** Minimizing Jerk means a more 'fluid' connection. "
            "Tight Handle Height boxplots indicate stable blade depth.")
