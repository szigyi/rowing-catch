import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

def plot_trunk_angle(avg_cycle, catch_idx, finish_idx):
    fig, ax = plt.subplots()
    ax.plot(avg_cycle.index, avg_cycle['Trunk_Angle'], color='purple', label='Trunk Angle')
    ax.axvline(catch_idx, color='green', linestyle='--', label='Catch')
    ax.axvline(finish_idx, color='red', linestyle='--', label='Finish')
    
    # Ideal Zones (approximate based on plan)
    ax.axhspan(-30, -25, color='green', alpha=0.2, label='Ideal Catch Zone')
    ax.axhspan(10, 15, color='blue', alpha=0.2, label='Ideal Finish Zone')
    
    ax.set_ylabel('Degrees from Vertical')
    ax.set_xlabel('Stroke Progress')
    ax.legend()
    st.pyplot(fig)
    
    catch_lean = avg_cycle.loc[catch_idx, 'Trunk_Angle']
    finish_lean = avg_cycle.loc[finish_idx, 'Trunk_Angle']
    st.info(f"**Coach's Tip:** You are achieving {abs(finish_lean - catch_lean):.1f}° of range. "
            f"Catch lean: {catch_lean:.1f}°, Finish lean: {finish_lean:.1f}°. "
            "Aim for the shaded zones to optimize power.")

def plot_velocity_coordination(avg_cycle, catch_idx, finish_idx):
    fig, ax = plt.subplots()
    ax.plot(avg_cycle.index, avg_cycle['Handle_X_Vel'], label='Handle Velocity', color='blue')
    ax.plot(avg_cycle.index, avg_cycle['Seat_X_Vel'], label='Seat Velocity', color='orange')
    ax.axvline(catch_idx, color='green', linestyle='--')
    ax.axvline(finish_idx, color='red', linestyle='--')
    ax.set_ylabel('Velocity')
    ax.legend()
    st.pyplot(fig)
    st.info("**Coach's Tip:** The goal is for your legs and handle to accelerate together. "
            "Gaps between these peaks mean you are losing power (shooting the slide).")

def plot_handle_trajectory(avg_cycle, catch_idx, finish_idx):
    fig, ax = plt.subplots()
    
    # Ideal Handle Path Calculation
    h_x_min = avg_cycle['Handle_X_Smooth'].min()
    h_x_max = avg_cycle['Handle_X_Smooth'].max()
    h_y_min = avg_cycle['Handle_Y_Smooth'].min()
    h_y_max = avg_cycle['Handle_Y_Smooth'].max()
    
    ideal_y_drive = h_y_max + (h_y_max - h_y_min) * 0.1 
    ideal_y_recovery = h_y_min - (h_y_max - h_y_min) * 0.1 
    
    ideal_x = [h_x_min, h_x_max, h_x_max, h_x_min, h_x_min]
    ideal_y = [ideal_y_drive, ideal_y_drive, ideal_y_recovery, ideal_y_recovery, ideal_y_drive]
    
    ax.plot(ideal_x, ideal_y, color='gray', linestyle='--', alpha=0.3, label='Ideal Path', linewidth=1)
    ax.scatter([h_x_min, h_x_max], [ideal_y_drive, ideal_y_drive], color='gray', s=30, alpha=0.3, label='Ideal Catch/Finish')
    
    ax.plot(avg_cycle['Handle_X_Smooth'], avg_cycle['Handle_Y_Smooth'], color='black', label='Handle Path')
    ax.scatter(avg_cycle.loc[catch_idx, 'Handle_X_Smooth'], avg_cycle.loc[catch_idx, 'Handle_Y_Smooth'], color='green', s=100, label='Catch')
    ax.scatter(avg_cycle.loc[finish_idx, 'Handle_X_Smooth'], avg_cycle.loc[finish_idx, 'Handle_Y_Smooth'], color='red', s=100, label='Finish')
    ax.set_xlabel('Horizontal Position')
    ax.set_ylabel('Vertical Position')
    ax.invert_yaxis()
    ax.legend()
    st.pyplot(fig)
    st.info("**Coach's Tip:** A flatter top line on the drive means a more consistent depth in the water.")

def plot_consistency_rhythm(cv, drive_p, rec_p):
    st.write(f"Your current variability: **{cv:.2f}%**")
    if cv < 2:
        st.success("Excellent! You have a very stable, robotic rhythm.")
    elif cv < 5:
        st.warning("Good consistency, but room to find a more repeatable rhythm.")
    else:
        st.error("High variability detected. Focus on making every stroke identical.")

    labels = ['Drive', 'Recovery']
    sizes = [drive_p, rec_p]
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#ff9999','#66b3ff'])
    ax.axis('equal')
    st.pyplot(fig)
    st.info(f"**Coach's Tip:** {'You are rushing the recovery.' if drive_p > 35 else 'Good rhythm.'} "
            "Slower movement on the slide (recovery) allows your muscles to recover.")
