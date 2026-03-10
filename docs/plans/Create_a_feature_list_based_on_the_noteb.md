### Rowing Analysis Project: Feature List for PDF Report

This feature list is designed to provide a comprehensive, data-driven report for rowers and coaches. Each feature focuses on "Current Performance vs. Ideal Technique" to facilitate actionable discussions.

---

### 1. Biomechanical & Technical Efficiency (Coach Focused)
These metrics analyze the geometry and coordination of the stroke.

#### ✅ **Trunk Angle & Range Analysis**
*   **Description:** Measures the angle between the shoulder and seat relative to the vertical axis throughout the stroke.
*   **Visualization:** A line plot of the trunk angle with shaded **"Ideal Zones"** (e.g., green for catch -30° to -25°, blue for finish 10° to 15°).
*   **Coach/Rower Insight:** "You are currently achieving 13° of range. To increase power, aim for the shaded green zone at the catch by leaning further forward from the hips."

#### ✅ **Seat vs. Handle Velocity Coordination**
*   **Description:** Compares the horizontal speed of the seat (legs) and handle (arms/back) during the drive.
*   **Visualization:** Overlapping line plots of Seat Velocity and Handle Velocity.
*   **Ideal vs. Reality:** Highlight the "peak" area. Ideally, the peaks should overlap, indicating the legs and back are connected. If the seat peak occurs before the handle peak, it identifies "shooting the slide" (power loss).
*   **Simple Explanation:** "The goal is for your legs and handle to accelerate together. Gaps between these peaks mean you are losing power."

#### ✅ **Handle Trajectory "Box" Plot**
*   **Description:** A 2D plot of the handle’s vertical (Y) vs. horizontal (X) path.
*   **Visualization:** A continuous loop showing the handle's path. Mark the **Catch** and **Finish** points clearly.
*   **Ideal vs. Reality:** A professional stroke follows a clean, rectangular or elliptical path. Skewed or "dipping" paths indicate technical errors like "digging" (too deep) or "skying" (handle too high at catch).
*   **Simple Explanation:** "This shows the shape of your stroke. A flatter top line on the drive means a more consistent depth in the water."

---

### 2. Consistency & Rhythm (Rower Focused)
These metrics help the rower find a stable, repeatable "rhythm."

#### ✅ **Stroke Consistency Score (CV)**
*   **Description:** Uses the Coefficient of Variation (CV) to measure how much the stroke length and duration vary over time.
*   **Visualization:** A "stability gauge" or bar chart showing your current variability vs. the **Professional Goal (< 2%)**.
*   **Simple Explanation:** "Lower numbers are better. 3% variability means your strokes are quite consistent, but there is room to find a more robotic rhythm."

#### ✅ **Dynamic Drive/Recovery Ratio**
*   **Description:** Measures the time spent on the "Work" (Drive) vs. the "Rest" (Recovery).
*   **Visualization:** A split bar chart comparing the current ratio (e.g., 56% drive / 44% recovery) to the **Ideal Ratio (33% / 66%)** at low rates.
*   **Simple Explanation:** "You are currently rushing the recovery. Slower movement on the slide (the recovery) allows your muscles to recover for the next powerful drive."

---

### 3. Suggested Future Features (Requires Additional Data)
These features would enhance the report but require hardware/data not currently available in the CSV trajectory.

*   **Force-Curve Integration:** 
    *   *Data needed:* Load cell or PM5 Force-Curve data. 
    *   *Feature:* Overlaying the handle trajectory with the force applied to see *where* in the stroke the rower is most powerful.
*   **Blade Slip & Wash Analysis:** 
    *   *Data needed:* Tracking of the blade itself (entry/exit points in the water). 
    *   *Feature:* Identifying how much the blade "slips" through the water before locking on, or how much water is "washed" at the finish.
*   **Hip/Knee Angle Biomechanics:** 
    *   *Data needed:* Tracking points for the Hip and Knee joints. 
    *   *Feature:* Analyzing the "order of operations" (Legs -> Back -> Arms) more precisely by looking at joint extension sequences.
*   **Boat Surge/Acceleration:** 
    *   *Data needed:* Accelerometer data from the boat/erg. 
    *   *Feature:* Correlating the rower's body movement with the acceleration of the boat to see which technical flaws cause "check" (slowing the boat down).

---

### Summary for the PDF Report
The final report will use a **"Traffic Light" system**:
*   **Green:** Within 5% of ideal range.
*   **Yellow:** Within 15% of ideal range (needs focus).
*   **Red:** Significant deviation (primary technical goal).

Each diagram will be accompanied by a **"Coach's Tip"**—a one-sentence instruction to fix the observed data point.