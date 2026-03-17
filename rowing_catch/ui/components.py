import streamlit as st
import matplotlib.pyplot as plt

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

def plot_trunk_angle_with_stage_stickfigures(avg_cycle, catch_idx, finish_idx, stage_points=None, ghost_cycle=None):
    """Plot trunk angle (top) and stage stick figures (bottom) with a shared X axis.

    The bottom pane uses small inset axes per stage so each stick figure has a
    local, equal-aspect coordinate system (no squashed head, clear lean), while
    still being anchored to the correct stroke-progress x-position.

    Args:
        avg_cycle: pandas DataFrame representing the averaged stroke.
        catch_idx: index (int-like) of catch in avg_cycle.
        finish_idx: index (int-like) of finish in avg_cycle.
        stage_points: optional list of (label, x_index) pairs. If None, uses
                      Catch, 3/4 slide, 1/2 slide, 1/4 slide, Finish interpolated
                      between catch_idx and finish_idx.
        ghost_cycle: optional pandas DataFrame of a comparison scenario to plot behind the main trunk angle.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    x = avg_cycle.index.to_numpy()

    if stage_points is None:
        drive_len = max(1, int(finish_idx) - int(catch_idx))
        rec_end = int(x.max())
        rec_len = max(1, rec_end - int(finish_idx))
        stage_points = [
            ("Catch", int(catch_idx)),
            ("3/4 Slide", int(catch_idx + 0.25 * drive_len)),
            ("1/2 Slide", int(catch_idx + 0.50 * drive_len)),
            ("1/4 Slide", int(catch_idx + 0.75 * drive_len)),
            ("Finish", int(finish_idx)),
            ("1/4 Slide", int(finish_idx + 0.25 * rec_len)),
            ("1/2 Slide", int(finish_idx + 0.50 * rec_len)),
            ("3/4 Slide", int(finish_idx + 0.75 * rec_len)),
            ("Next Catch", rec_end),
        ]

    x_min = int(x.min())
    x_max = int(x.max())
    stage_points = [(label, int(np.clip(ix, x_min, x_max))) for label, ix in stage_points]

    fig, (ax_top, ax_bot) = plt.subplots(
        2,
        1,
        figsize=(10, 7),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 2]},
        constrained_layout=True,
    )
    
    # Modern Styling
    fig.patch.set_facecolor('#F8F9FA')  # Light gray background for the whole figure
    ax_top.set_facecolor('#FFFFFF')     # White for the data area
    ax_bot.set_facecolor('#F8F9FA')
    
    # Clean up spines on top plot
    ax_top.spines['top'].set_visible(False)
    ax_top.spines['right'].set_visible(False)
    ax_top.spines['left'].set_color('#DDDDDD')
    ax_top.spines['bottom'].set_color('#DDDDDD')
    ax_top.grid(axis='y', linestyle='-', linewidth=0.5, color='#F0F0F0', zorder=0)

    # Add a little extra padding around the whole figure to avoid Streamlit cropping at edges.
    try:
        fig.set_constrained_layout_pads(w_pad=0.04, h_pad=0.04, wspace=0.02, hspace=0.02)
    except Exception:
        pass

    # --- Top: trunk angle trace ---
    ax_top.plot(avg_cycle.index, avg_cycle['Trunk_Angle'], color='#636EFA', label='Trunk Angle', linewidth=2.5, zorder=5)
    
    # Fill under the curve slightly for dynamic effect
    ax_top.fill_between(avg_cycle.index, avg_cycle['Trunk_Angle'], 0, where=(avg_cycle['Trunk_Angle'] > 0), color='#636EFA', alpha=0.1, zorder=4)
    ax_top.fill_between(avg_cycle.index, avg_cycle['Trunk_Angle'], 0, where=(avg_cycle['Trunk_Angle'] <= 0), color='#636EFA', alpha=0.1, zorder=4)
    
    if ghost_cycle is not None:
        ax_top.plot(ghost_cycle.index, ghost_cycle['Trunk_Angle'], color='#A8B2C1', linestyle=':', linewidth=2, alpha=0.8, label='Compare', zorder=4)

    # Upright reference (0° from vertical)
    ax_top.axhline(0, color='#888888', linestyle='dashed', linewidth=1, alpha=0.5, zorder=2)
    ax_top.text(
        avg_cycle.index.min() + 2,
        0,
        'Upright (0°)',
        color='#666666',
        fontsize=9,
        fontweight='medium',
        va='bottom',
        ha='left',
        bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.8, pad=0.6),
        zorder=6
    )

    ax_top.axvline(catch_idx, color='#00CC96', linestyle='--', linewidth=1.5, zorder=2)
    ax_top.axvline(finish_idx, color='#EF553B', linestyle='--', linewidth=1.5, zorder=2)
    ax_top.axvline(x_max, color='#00CC96', linestyle='--', linewidth=1.5, zorder=2)

    catch_zone = (-33, -27)
    finish_zone = (12, 18)
    ax_top.axhspan(catch_zone[0], catch_zone[1], color='#00CC96', alpha=0.08, zorder=1)
    ax_top.axhspan(finish_zone[0], finish_zone[1], color='#EF553B', alpha=0.08, zorder=1)
    ax_top.set_ylabel('Degrees from Vertical', color='#444444', fontweight='bold', labelpad=10)
    ax_top.tick_params(axis='y', colors='#666666')

    y_min, y_max = ax_top.get_ylim()
    y_label = y_max - (y_max - y_min) * 0.05
    ax_top.text(catch_idx, y_label, 'Catch', color='#00CC96', ha='center', va='top', fontsize=10, fontweight='bold',
                bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.9, pad=1.5), zorder=6)
    ax_top.text(finish_idx, y_label, 'Finish', color='#EF553B', ha='center', va='top', fontsize=10, fontweight='bold',
                bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.9, pad=1.5), zorder=6)
    ax_top.text(x_max, y_label, 'Catch', color='#00CC96', ha='center', va='top', fontsize=10, fontweight='bold',
                bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.9, pad=1.5), zorder=6)

    x_right = (avg_cycle.index.min() + avg_cycle.index.max()) * 0.85
    ax_top.text(x_right, sum(catch_zone) / 2, 'Ideal Catch', color='#00CC96', ha='center', va='center', fontsize=9, fontweight='medium',
                bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.7, pad=1.5), zorder=6)
    ax_top.text(x_right, sum(finish_zone) / 2, 'Ideal Finish', color='#EF553B', ha='center', va='center', fontsize=9, fontweight='medium',
                bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.7, pad=1.5), zorder=6)

    legend_kwargs = dict(loc='center right', frameon=True, facecolor='#FFFFFF', edgecolor='#DDDDDD', fontsize=9, borderpad=0.8)
    if not any(spine.get_visible() for spine in ax_top.spines.values()):
        pass
    ax_top.legend(**legend_kwargs)

    # --- Bottom: anchor axis for alignment only ---
    ax_bot.axvline(catch_idx, color='#00CC96', linestyle='--', linewidth=1.5, alpha=0.2)
    ax_bot.axvline(finish_idx, color='#EF553B', linestyle='--', linewidth=1.5, alpha=0.2)
    ax_bot.axvline(x_max, color='#00CC96', linestyle='--', linewidth=1.5, alpha=0.2)
    ax_bot.axhline(0.0, color='#888888', linewidth=1, alpha=0.2)
    ax_bot.set_ylim(-0.5, 1.5)
    ax_bot.set_yticks([])
    ax_bot.set_xlabel('Stroke Timeline (Data Points)', color='#444444', fontweight='bold', labelpad=10)
    ax_bot.tick_params(axis='x', colors='#666666')
    ax_bot.set_xlim(x_min - 5, x_max + 5)

    # Hide spines for a clean look
    for spine in ax_bot.spines.values():
        spine.set_visible(False)
    ax_bot.spines['bottom'].set_visible(True)
    ax_bot.spines['bottom'].set_color('#DDDDDD')

    # NOTE: inset axes must be positioned using the *actual* data->axes transform,
    # otherwise xlim padding will shift them and they won't align with catch/finish lines.
    def _data_x_to_axes_frac(ix: int) -> float:
        # Convert (ix, 0) from data coords to display, then to axes fraction.
        disp = ax_bot.transData.transform((ix, 0.0))
        axes_xy = ax_bot.transAxes.inverted().transform(disp)
        return float(axes_xy[0])

    # Local stick figure geometry (angle measured from vertical)
    def _vector_from_vertical_angle(angle_deg: float, length: float):
        a = np.radians(angle_deg)
        return length * np.sin(a), length * np.cos(a)

    trunk_length = 1.0
    head_radius = 0.22

    # Inset sizing in axis-fraction units (responsive)
    inset_w_default = 0.16
    inset_h = 0.80
    inset_y0 = 0.08

    # Reserve a "gutter" so inset boxes never sit flush against the axis boundaries.
    # This avoids subtle clipping of the first/last insets.
    edge_margin = 0.05

    for label, ix in stage_points:
        # Get the trunk angle at that x position from the same data used in the top plot
        try:
            angle = float(avg_cycle.loc[ix, 'Trunk_Angle'])
        except Exception:
            nearest = int(np.argmin(np.abs(x - ix)))
            angle = float(avg_cycle['Trunk_Angle'].iloc[nearest])
            ix = int(x[nearest])

        frac = _data_x_to_axes_frac(ix)

        # Clamp the stage anchor into a safe interior region so the inset box can fully fit.
        frac_safe = float(np.clip(frac, edge_margin, 1.0 - edge_margin))

        max_w_left = 2.0 * max(frac_safe - edge_margin, 0.0)
        max_w_right = 2.0 * max((1.0 - edge_margin) - frac_safe, 0.0)
        inset_w = float(min(inset_w_default, max_w_left, max_w_right))
        inset_w = float(max(inset_w, 0.12))

        x0 = float(np.clip(frac_safe - inset_w / 2, edge_margin, (1.0 - edge_margin) - inset_w))
        stage_inside = float(np.clip(frac - x0, 0.0, inset_w))

        inset = ax_bot.inset_axes([x0, inset_y0, inset_w, inset_h], transform=ax_bot.transAxes)
        inset.set_aspect('equal', adjustable='box')
        inset.axis('off')
        inset.set_clip_on(False)

        # --- Alignment fix (keep stage at x=0 inside inset coords) ---
        x_span = 1.2
        frac_in_inset = stage_inside / inset_w if inset_w > 0 else 0.5
        x_left = -x_span * frac_in_inset
        x_right = x_span * (1.0 - frac_in_inset)
        inset.set_xlim(x_left, x_right)
        inset.set_ylim(-0.35, 1.60)

        # Draw true vertical reference at x=0
        inset.plot([0, 0], [0, trunk_length], color='#888888', alpha=0.3, linestyle=':', linewidth=1.5, clip_on=False)

        dx, dy = _vector_from_vertical_angle(angle, trunk_length)
        inset.plot([0, dx], [0, dy], color='#636EFA', linewidth=3.5, solid_capstyle='round', clip_on=False)
        inset.add_patch(plt.Circle((dx, dy + head_radius), head_radius, color='#B5B9D2', zorder=3, clip_on=False))

        # Labels inside inset
        label_color = '#00CC96' if 'Catch' in label else '#EF553B' if 'Finish' in label else '#666666'
        label_weight = 'bold' if 'Catch' in label or 'Finish' in label else 'medium'
        inset.text(0, -0.27, label, ha='center', va='top', fontsize=8, color=label_color, fontweight=label_weight, clip_on=False)
        inset.text(
            0,
            1.32,
            f"{angle:.1f}°",
            ha='center',
            va='bottom',
            fontsize=8,
            color='#444444',
            fontweight='bold',
            zorder=5,
            bbox=dict(facecolor='#FFFFFF', edgecolor='none', alpha=0.85, pad=1.5),
            clip_on=False,
        )

    st.pyplot(fig)

    catch_lean = float(avg_cycle.loc[catch_idx, 'Trunk_Angle'])
    finish_lean = float(avg_cycle.loc[finish_idx, 'Trunk_Angle'])
    st.info(
        f"**Coach's Tip:** You are achieving {abs(finish_lean - catch_lean):.1f}° of range. "
        f"Catch lean: {catch_lean:.1f}°, Finish lean: {finish_lean:.1f}°. "
        "Aim for the shaded zones to optimize power."
    )
