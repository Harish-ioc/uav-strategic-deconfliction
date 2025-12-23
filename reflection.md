# Reflection & Design Justification  
## UAV Strategic Deconfliction in Shared Airspace

---

## 1. Problem Overview

The goal of this project was to build a **strategic UAV deconfliction system** that decides whether a newly planned drone mission is safe to fly in shared airspace. The system checks for possible conflicts with other drones by considering **both space and time**, instead of only checking geometric path intersections.

This is a **pre-flight safety system**, meaning the decision is made before the drone takes off. If the path is safe, the mission is approved; otherwise, the system reports where and when conflicts may occur.

---

## 2. Overall System Design

The system is built in a **modular way**, with each part having a clear responsibility:

- **Path Generation** – creates realistic simulated drone flight paths
- **Preprocessing** – prepares and normalizes data for analysis and visualization
- **Deconfliction Engine** – performs all spatiotemporal safety checks
- **User Interface** – allows users to create paths and visualize conflicts
- **Mission Execution** – sends MAVLink commands to fly approved missions

A key design choice was to ensure that the **UI never decides safety**.  
All safety decisions are made by a centralized deconfliction module, which makes the system easier to test, reason about, and scale.

---

## 3. Simulated Path Generation

To test the system properly, multiple drone paths were generated programmatically instead of using static data.

Each simulated mission follows a few rules:

- **Fixed Operating Area**  
  All waypoints lie within a defined latitude–longitude boundary, representing a shared airspace.

- **Altitude Rules**  
  - Missions start and end at a low altitude (around 10 m) to represent takeoff and landing.
  - Intermediate waypoints use randomized altitudes within a safe range (e.g., 20–60 m).

- **Time Randomization**  
  - Each mission starts at a random time offset.
  - Mission duration and waypoint spacing are randomized within limits.

- **Direction Randomization**  
  Start and end points are chosen from different sides of the area, creating varied flight directions and increasing the chance of intersections.

This approach creates **diverse but realistic trajectories**, which is useful for stress-testing the deconfliction logic.

---

## 4. How New Paths Are Checked

When a new mission is submitted, it goes through a series of checks.

### 4.1 Time Window Check

The system first checks whether the new mission overlaps in time with existing drone missions.

If two missions do not overlap in time, they are skipped entirely.  
This simple step avoids unnecessary computations and improves performance.

---

### 4.2 Segment-Level Time Matching

Each flight path is broken into segments between waypoints.

Only segment pairs that overlap in time are compared further.  
This ensures spatial checks are done **only when drones could actually be airborne at the same time**.

---

### 4.3 Distance-Based Conflict Detection (4D Check)

For overlapping segments:

- Drone positions are interpolated at multiple time samples.
- Horizontal distance is calculated from latitude and longitude.
- Vertical distance is calculated from altitude.
- A combined **3D Euclidean distance** is computed.

If the distance is less than a safety threshold (e.g., 12 meters), the system flags a conflict.

This effectively treats each mission as a **continuous 4D path (x, y, z, time)** instead of just a set of discrete waypoints.

---

## 5. Conflict Reporting and Visualization

When conflicts are found:

- The system records:
  - Which drone caused the conflict
  - Time of conflict
  - Position and altitude
  - Separation distance
- Conflicts are grouped and shown as **clear, readable messages**.
- The GUI highlights conflict points directly on the map.

If no conflicts are detected, the system clearly reports that the **path is safe**.

---

## 6. Mission Execution Using MAVLink

If a path is approved, the system can directly execute the mission using **MAVLink commands**.

The execution flow includes:
- Switching to GUIDED mode
- Arming the drone
- Taking off to the first waypoint altitude
- Flying through waypoints sequentially

This demonstrates a complete pipeline:  
**planning → validation → approval → execution**, as shown in the demo video.

---

## 7. Testing Strategy

To validate correctness, deterministic test cases were created:

- **Intersecting paths** to ensure conflicts are detected
- **Non-intersecting paths** to ensure false positives are avoided

These tests directly target the spatiotemporal logic and give confidence that the system behaves as expected.

---

## 8. Use of AI Tools

AI-assisted tools played an important role in this project.

- **ChatGPT and Claude**  
  Helped with:
  - Structuring the overall project layout
  - Understanding the spatiotemporal checking approaches
  - Testing and fixing bugs

- **DeepSeek / LLM-based search**  
  Helped with:
  - Researching MAVLink command usage
  - Understanding best practices for UAV safety separation
  - Exploring scalable design patterns

- **Documentation & Testing Support**  
  AI tools assisted in:
  - Writing and refining documentation
  - Designing meaningful test cases
  - Improving clarity of explanations

All AI-generated suggestions were **reviewed, validated, and adapted manually**, ensuring correctness and alignment with project requirements.

---

## 9. Scalability Considerations

The current system works well for small and medium-scale scenarios.  
For real-world deployment with thousands of drones, improvements would include:

- Spatial indexing (R-trees, geohashing)
- Time-based bucketing
- Parallel or distributed computation
- Real-time data pipelines
- Fault-tolerant system design

The modular architecture makes these upgrades achievable without major redesign.

---

## 10. Learnings and Limitations

Key learnings:
- Clear separation between UI and decision logic is crucial
- Early time filtering significantly reduces computation
- Explainable outputs improve trust in safety decisions

Current limitations:
- Assuming the speed of drones as constant for interpolation
- Approximate conversion from lat/lon to meters
- Fixed sampling resolution
- No uncertainty or wind modeling

These are good candidates for future improvement.

---

## 11. Conclusion

This project delivers a complete strategic UAV deconfliction system, covering realistic data generation, 4D conflict detection, visualization, testing, and mission execution. The focus on modular design, explainability, and safety makes it well aligned with real-world UAV airspace management systems.
