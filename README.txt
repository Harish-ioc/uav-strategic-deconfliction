================================================================================
                 DRONE PATH CONFLICT DETECTION SYSTEM
================================================================================

PROJECT OVERVIEW
================================================================================
A Python-based system for detecting spatiotemporal conflicts between drone 
flight paths. The system analyzes a new drone path against existing drone 
trajectories to identify potential collision risks in 4D space (3D position + 
time).

Key Features:
  - 4D spatiotemporal collision detection
  - Interactive map-based waypoint planning
  - MAVLink drone control integration
  - Real-time telemetry monitoring
  - Mission execution capabilities
  - Comprehensive test suite


SYSTEM REQUIREMENTS
================================================================================
Software:
  - Python 3.8 or higher
  - pip package manager
  - Internet connection (for map tiles)

Hardware (for real drone operations):
  - MAVLink-compatible drone or simulator (ArduPilot/PX4)
  - Serial or UDP connection to flight controller
  - Minimum 4GB RAM


INSTALLATION
================================================================================
1. Clone or download the project to your local machine

2. Install required Python packages:
   
   pip install pandas numpy pymavlink pyqt5 pyqtwebengine matplotlib openpyxl
   
   Optional (for geographic visualization):
   pip install cartopy

3. Verify project structure:
   
   drone-conflict-detection/
   ├── src/
   │   ├── control/
   │   │   └── drone_controller.py
   │   ├── deconfliction/
   │   │   ├── spatiotemporal.py
   │   │   └── explain.py
   │   ├── data_generation/
   │   │   ├── simulated_paths.py
   │   │   └── normalize.py
   │   └── ui/
   │       └── main_window.py
   ├── data/
   ├── scripts/
   │   └── show_paths.py
   └── tests/
       └── test_spatiotemporal.py


QUICK START GUIDE
================================================================================

STEP 1: Generate Test Data
---------------------------
cd src/data_generation
python simulated_paths.py
python normalize.py

This creates:
  - data/simulated_paths.xlsx (raw test paths)
  - data/normalized_paths.xlsx (processed paths)


STEP 2: Run Tests (Optional)
-----------------------------
cd tests
python test_spatiotemporal.py

Expected output: "15 passed, 0 failed"


STEP 3: Launch GUI Application
-------------------------------
cd src/ui
python main_window.py


STEP 4: Using the Application
------------------------------
1. Click "📂 Load Existing Paths (xlsx)" button
   - Loads normalized_paths.xlsx from data/ folder
   - Displays existing drone paths on map

2. Create a new path:
   OPTION A: Click on map to add waypoints
     - Click any location on the map
     - Enter altitude (meters)
     - Enter arrival time (YYYY-MM-DD HH:MM:SS)
   
   OPTION B: Use text input
     - Enter waypoints in format:
       (18.5720, 73.7713, 10, '2025-12-23 12:42:18')
       (18.5687, 73.7753, 33, '2025-12-23 12:46:39')
     - Click "➕ Add Path from Text"

3. Click "🔍 Analyze Collision Risk" button
   - System analyzes path for conflicts
   - Results shown in Activity Log
   - Conflicts marked on map with yellow/red markers

4. Review Results:
   - ✅ PATH SAFE - No conflicts detected
   - ⚠️ COLLISION RISK - Conflicts found with details


STEP 5: Mission Execution (Optional - Requires Drone/Simulator)
----------------------------------------------------------------
1. Connect drone:
   - Click "Connect" button
   - Wait for connection confirmation

2. Execute mission (only if path is safe):
   - Click "Execute Mission" button
   - Drone will:
     * Set GUIDED mode
     * Arm motors
     * Takeoff to first waypoint altitude
     * Fly through all waypoints
     * Log progress in Activity Log


CONFIGURATION
================================================================================

Safety Distance
---------------
Edit: src/deconfliction/spatiotemporal.py
Change: SAFETY_DISTANCE_METERS = 12  # Default 12 meters

Operational Area
----------------
Edit: src/data_generation/simulated_paths.py
Change boundary coordinates (a, b, c, d)
Change altitude range (ALT_MIN, ALT_MAX)

Drone Connection
----------------
Edit: src/control/drone_controller.py
Line 15: Change connection string
  - Simulator: 'udp:172.19.144.1:14550'
  - Serial: 'COM3' (Windows) or '/dev/ttyUSB0' (Linux)
  - Baudrate: Default 57600


UNDERSTANDING THE SYSTEM
================================================================================

How Collision Detection Works
------------------------------
1. Time Window Check: Skip paths with no temporal overlap
2. Segment Analysis: Compare each path segment
3. Position Interpolation: Calculate positions at sample times
4. Distance Calculation: Compute 3D Euclidean distance
5. Conflict Flagging: Alert if distance < 12 meters

Safety Distance Rationale (12 meters)
--------------------------------------
  - GPS uncertainty: ±3-5 meters
  - Position hold accuracy: ±2-3 meters
  - Communication latency effects
  - Rotor wash interference zone: ~5-8 meters
  - Safety buffer for unexpected deviations


PROJECT FILES EXPLAINED
================================================================================

Control Layer
-------------
drone_controller.py
  - MAVLink communication
  - Drone arming/disarming
  - Flight mode management
  - Takeoff and navigation commands
  - Real-time telemetry monitoring

Deconfliction Layer
-------------------
spatiotemporal.py
  - Core collision detection algorithm
  - 4D trajectory analysis
  - Linear interpolation between waypoints
  - 3D distance calculations

explain.py
  - Converts raw conflict data to human-readable messages
  - Groups conflicts by drone
  - Formats output for display

Data Generation Layer
---------------------
simulated_paths.py
  - Generates random test drone paths
  - Creates Excel file with waypoints
  - Configurable operational area

normalize.py
  - Min-max normalization of coordinates
  - Converts timestamps to relative values
  - 3D visualization of paths

User Interface Layer
--------------------
main_window.py
  - PyQt5 GUI application
  - Leaflet map integration
  - Interactive waypoint creation
  - Conflict visualization
  - Mission execution control

Utilities
---------
show_paths.py
  - Standalone path visualization
  - Uses Cartopy for geographic maps

test_spatiotemporal.py
  - Comprehensive unit tests (15 test cases)
  - Validates collision detection logic


DATA FILES
================================================================================

simulated_paths.xlsx
--------------------
Columns: drone_id, lat, lon, alt, timestamp
Contains: Raw simulated drone paths
Created by: simulated_paths.py

normalized_paths.xlsx
---------------------
Columns: drone_id, lat, lon, alt, timestamp, x_norm, y_norm, z_norm, t_norm
Contains: Normalized coordinates for analysis
Created by: normalize.py


COMMON ISSUES & SOLUTIONS
================================================================================

Issue: "No drones detected"
---------------------------
Solution:
  - Verify simulator/drone is running
  - Check connection string in drone_controller.py
  - Confirm network/serial settings
  - Check firewall settings for UDP connections

Issue: GUI doesn't load or crashes
-----------------------------------
Solution:
  - Reinstall PyQt5: pip install --upgrade pyqt5 pyqtwebengine
  - Check Python version (3.8+ required)
  - Run with: python -v main_window.py to see errors

Issue: Map tiles don't load
----------------------------
Solution:
  - Check internet connection
  - Verify no proxy/firewall blocking OpenStreetMap
  - Wait 5-10 seconds for initial load

Issue: "Load existing paths" does nothing
------------------------------------------
Solution:
  - Generate data first: run simulated_paths.py and normalize.py
  - Verify data/normalized_paths.xlsx exists
  - Check file permissions

Issue: Tests failing
--------------------
Solution:
  - Review test output for specific failures
  - Check SAFETY_DISTANCE_METERS setting
  - Verify spatiotemporal.py has not been modified

Issue: Mission execution fails
-------------------------------
Solution:
  - Confirm path has been analyzed (click "Analyze" first)
  - Verify path is safe (no conflicts)
  - Check drone is connected
  - Ensure drone has GPS lock (outdoor or GPS simulator)
  - Verify battery level is sufficient


SAFETY WARNINGS
================================================================================

⚠️ IMPORTANT SAFETY INFORMATION ⚠️

1. TEST IN SIMULATION FIRST
   - Always test new paths in a simulator before real flights
   - Verify all waypoints are within safe operational area

2. MANUAL OVERRIDE REQUIRED
   - Maintain ability to switch to manual control
   - Always have RC transmitter ready

3. SYSTEM LIMITATIONS
   - Does NOT account for wind effects
   - Does NOT provide dynamic re-routing
   - Does NOT detect obstacles (buildings, trees, etc.)
   - GPS accuracy varies by environment

4. LEGAL COMPLIANCE
   - Follow local aviation regulations
   - Obtain necessary permits/authorizations
   - Maintain visual line of sight (VLOS)
   - Respect no-fly zones

5. PRE-FLIGHT CHECKLIST
   ☐ Analyze path for conflicts
   ☐ Verify all waypoints are valid
   ☐ Check weather conditions
   ☐ Ensure sufficient battery
   ☐ Confirm GPS lock
   ☐ Test manual control
   ☐ Clear operational area of obstacles


TESTING THE SYSTEM
================================================================================

Running Unit Tests
------------------
cd tests
python test_spatiotemporal.py

Test Coverage:
  ✓ Exact position/time conflicts
  ✓ Horizontal proximity detection
  ✓ Vertical separation safety
  ✓ Temporal separation handling
  ✓ Crossing paths scenarios
  ✓ Parallel paths analysis
  ✓ Head-on collision detection
  ✓ Overtaking scenarios
  ✓ Multi-segment path analysis
  ✓ Boundary condition testing

Expected Result: "15 passed, 0 failed"


ADVANCED USAGE
================================================================================

Custom Operational Area
-----------------------
Edit: src/data_generation/simulated_paths.py

Define new corner coordinates:
  a = (lat_nw, lon_nw)  # Northwest corner
  b = (lat_ne, lon_ne)  # Northeast corner
  c = (lat_sw, lon_sw)  # Southwest corner
  d = (lat_se, lon_se)  # Southeast corner

Adjusting Safety Parameters
----------------------------
Edit: src/deconfliction/spatiotemporal.py

Change minimum separation:
  SAFETY_DISTANCE_METERS = 15  # Increase for more conservative analysis

Increase temporal sampling:
  ts = pd.date_range(t_start, t_end, periods=8)  # Line 65
  # More samples = more accurate but slower

Batch Path Analysis
-------------------
For analyzing multiple new paths:
  1. Create script to iterate through candidate paths
  2. Call detect_conflicts() for each
  3. Store results in DataFrame
  4. Export summary report


TROUBLESHOOTING CONNECTION ISSUES
================================================================================

Serial Connection (Hardware Drone)
-----------------------------------
Windows:
  connection = mavutil.mavlink_connection('COM3', baud=57600)

Linux:
  connection = mavutil.mavlink_connection('/dev/ttyUSB0', baud=57600)

Check port: Device Manager (Windows) or ls /dev/tty* (Linux)

UDP Connection (Simulator)
---------------------------
Default: mavutil.mavlink_connection('udp:172.19.144.1:14550')

For local simulator:
  connection = mavutil.mavlink_connection('udp:127.0.0.1:14550')

For remote simulator:
  connection = mavutil.mavlink_connection('udp:<IP_ADDRESS>:14550')

Testing Connection
------------------
1. Start simulator (ArduPilot SITL, Gazebo, etc.)
2. Run simple test:
   
   from pymavlink import mavutil
   conn = mavutil.mavlink_connection('udp:127.0.0.1:14550')
   msg = conn.recv_match(type='HEARTBEAT', blocking=True)
   print(f"Connected to drone: System ID {msg.get_srcSystem()}")


PERFORMANCE OPTIMIZATION
================================================================================

For Large Datasets
------------------
- Spatial indexing: Implement quadtree or R-tree
- Parallel processing: Use multiprocessing for multiple paths
- Reduce sampling: Decrease temporal sample points (trade accuracy)

For Real-Time Operation
-----------------------
- Pre-compute path segments
- Cache interpolation results
- Use numpy vectorization
- Implement distance early-exit conditions


EXTENDING THE SYSTEM
================================================================================

Adding New Features
-------------------
1. Alternative path suggestions
2. Wind effect modeling
3. Battery consumption estimation
4. Multi-objective optimization
5. No-fly zone integration

Integration Points
------------------
- REST API: Wrap detect_conflicts() in Flask/FastAPI
- ROS Integration: Create ROS node for path planning
- Database Storage: Store paths in PostgreSQL/MongoDB
- Cloud Deployment: Containerize with Docker


SYSTEM ARCHITECTURE SUMMARY
================================================================================

Data Flow:
  1. Generate/Load → simulated_paths.xlsx
  2. Normalize → normalized_paths.xlsx
  3. Load in GUI → Display on map
  4. User creates new path → Click/Text input
  5. Analyze → spatiotemporal.py
  6. Display results → Map markers + Activity log
  7. Execute (optional) → drone_controller.py → Physical drone

Key Algorithms:
  - Linear interpolation for position estimation
  - Euclidean distance for 3D separation
  - Time window filtering for efficiency
  - Segment-by-segment conflict checking


================================================================================
                           END OF README
================================================================================

