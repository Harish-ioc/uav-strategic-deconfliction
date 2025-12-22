# Reflection & Design Justification  
## UAV Strategic Deconfliction in Shared Airspace

---

## 1. Problem Understanding

The objective of this project was to design and implement a **strategic UAV deconfliction system** that acts as a *final authority* to decide whether a newly planned drone mission is safe to execute in shared airspace. The system must evaluate conflicts not only in space, but also in time, ensuring that no two drones violate a minimum safety separation while operating within overlapping mission windows.

Unlike tactical or reactive collision avoidance, this system focuses on **pre-flight validation**, where a drone queries the deconfliction service before takeoff and receives an approval or rejection based on predicted spatiotemporal conflicts.

---

## 2. System Architecture Overview

The system is designed using a **modular architecture**, separating concerns clearly across components:

- **Data Generation Layer**  
  Responsible for simulating realistic drone flight paths.
- **Preprocessing Layer**  
  Normalizes and prepares flight data for analysis and visualization.
- **Deconfliction Engine (Core Logic)**  
  A centralized module that performs all spatiotemporal conflict checks.
- **User Interface & Visualization Layer**  
  Collects new mission inputs, visualizes paths, and displays conflict results.
- **Execution Layer**  
  Executes approved missions using MAVLink commands.

This separation ensures that the **UI never makes safety decisions**. All decisions are delegated to a centralized spatiotemporal deconfliction module, which improves testability, scalability, and correctness.

---

## 3. Simulated Flight Path Generation

To evaluate the deconfliction logic, a dataset of simulated drone missions was generated programmatically.

Each simulated mission follows these constraints:

- **Geographic Area Bounding**  
  All waypoints are constrained within a predefined rectangular operational area (latitude–longitude bounds). This models a shared urban or campus-scale airspace.
  
- **Altitude Constraints**  
  - Mission **start and end altitudes** are fixed at a low altitude (e.g., 10 meters), simulating takeoff and landing phases.
  - Intermediate waypoints have **randomized altitudes** within a specified range (e.g., 20–60 meters), reflecting cruise flight variations.

- **Temporal Constraints**  
  - Each mission starts at a randomized time offset from a reference time.
  - Total mission duration and waypoint spacing are randomized but bounded.

- **Directional Randomization**  
  Start and end positions are chosen from opposite sides of the bounding area, ensuring diverse flight directions and increasing the likelihood of path intersections.

This controlled randomization produces **realistic yet diverse trajectories**, which is essential for stress-testing spatiotemporal conflict detection logic.

---

## 4. Phases of Deconfliction for a New Mission

When a new drone mission is submitted, the system evaluates it through a **multi-stage deconfliction pipeline**.

### 4.1 Temporal Overlap Check (First Filter)

The first and cheapest check is **time-based filtering**.

- The overall mission time window of the new path is compared with each existing drone’s mission window.
- If two missions do **not overlap in time**, they are immediately skipped.
  
This step significantly reduces unnecessary spatial computations and improves scalability.

---

### 4.2 Segment-Level Time Intersection

For missions that overlap globally in time:

- Each path is broken into **line segments** between consecutive waypoints.
- Only segment pairs whose time intervals overlap are considered further.

This ensures that spatial checks are performed **only when two drones could physically coexist in the airspace at the same time**.

---

### 4.3 Spatiotemporal Distance Check (4D Check)

For overlapping segment pairs:

- Positions of both drones are **interpolated** at multiple sample points within the overlapping time interval.
- At each sampled time:
  - Horizontal separation is computed using Euclidean distance in latitude–longitude space (converted approximately to meters).
  - Vertical separation is computed directly from altitude.
  - A combined **3D Euclidean distance** is calculated.

If the distance falls below a predefined **safety threshold** (e.g., 12 meters), a conflict is recorded.

This process effectively treats each drone’s trajectory as a **continuous 4D curve (x, y, z, t)** rather than discrete waypoints.

---

## 5. Conflict Explanation and Visualization

When conflicts are detected:

- Each conflict is recorded with:
  - Drone ID
  - Time of conflict
  - Position (latitude, longitude, altitude)
  - Separation distance
- Conflicts are grouped by drone and converted into **human-readable explanations**.
- The GUI visualizes conflict points directly on the map using highlighted markers, allowing operators to understand *where and when* conflicts occur.

If no conflicts are found, the system explicitly returns a **PATH SAFE** decision.

---

## 6. Mission Execution via MAVLink

If a mission is approved:

- The system proceeds to execute the mission using **MAVLink commands**, as demonstrated in the project demo.
- The execution flow includes:
  - Switching the drone to GUIDED mode
  - Arming the vehicle
  - Takeoff to the first waypoint altitude
  - Sequential navigation through approved waypoints using position target commands

This integration demonstrates a **closed-loop workflow**:  
planning → validation → approval → execution.

---

## 7. Testing and Validation Strategy

To validate correctness, deterministic test cases were created using:

- **Intersecting paths** (expected to produce conflicts)
- **Non-intersecting paths** (expected to be conflict-free)

These tests directly validate the spatiotemporal deconfliction logic and ensure that the system detects true conflicts while avoiding false positives.

---

## 8. Scalability Considerations

While the current implementation is suitable for small-to-medium scale simulations, scaling to tens of thousands of drones would require:

- Spatial indexing structures (e.g., R-trees or geohashing)
- Time bucketing and interval indexing
- Parallel or distributed computation
- Real-time data ingestion pipelines
- Fault-tolerant, event-driven architecture

The current modular design makes these extensions feasible without major refactoring.

---

## 9. Learnings and Limitations

Key learnings include:

- The importance of separating **decision logic from visualization**
- The effectiveness of temporal filtering in reducing computational load
- The trade-offs involved in spatial approximation using latitude–longitude

Limitations include:
- Approximate conversion from degrees to meters
- Fixed sampling resolution along segments
- No modeling of uncertainty or communication delays

These areas represent clear opportunities for future improvement.

---

## 10. Conclusion

This project demonstrates a complete strategic UAV deconfliction pipeline—from realistic data generation to spatiotemporal analysis and real-world mission execution. The system emphasizes explainability, modularity, and correctness, aligning well with real-world airspace management requirements.
