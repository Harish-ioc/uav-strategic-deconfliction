# Drone Path Conflict Detection System - Technical Documentation

## Project Overview

The Drone Path Conflict Detection System is a comprehensive Python-based application designed to analyze and detect potential collision risks between a new drone flight path and existing drone trajectories. The system uses spatiotemporal (4D) analysis to identify conflicts in both space and time, ensuring safe drone operations in shared airspace.

### Key Features
- Real-time collision detection using 4D spatiotemporal analysis
- Interactive map-based waypoint planning
- MAVLink drone control integration
- Multi-drone path visualization
- Configurable safety distance parameters (default: 12 meters)
- Mission execution capabilities with automated flight control

---

## System Architecture

```
drone-conflict-detection/
├── src/
│   ├── control/
│   │   └── drone_controller.py       # Drone communication & control
│   ├── deconfliction/
│   │   ├── spatiotemporal.py         # Collision detection algorithm
│   │   └── explain.py                # Human-readable conflict reports
│   ├── data_generation/
│   │   ├── simulated_paths.py        # Test data generator
│   │   └── normalize.py              # Path normalization
│   └── ui/
│       └── main_window.py            # PyQt5 GUI application
├── data/
│   ├── simulated_paths.xlsx          # Generated test paths
│   └── normalized_paths.xlsx         # Processed path data
├── scripts/
│   └── show_paths.py                 # Visualization utility
└── tests/
    └── test_spatiotemporal.py        # Unit tests
```

---

## File-by-File Documentation

### 1. `drone_controller.py`
**Location**: `src/control/drone_controller.py`  
**Purpose**: Provides MAVLink-based drone communication and control interface for autonomous flight operations.

#### Class: `SimpleDroneController`
Manages connections and commands to one or multiple drones via MAVLink protocol.

#### Key Attributes:
- `connection`: MAVLink connection object
- `detected_drones`: List of system IDs for all detected drones
- `attitude_heading`: Dictionary storing live telemetry data (heading, lat, lon, alt)
- `monitoring_active`: Boolean flag for background monitoring thread

#### Main Methods:

**`connect_to_drones(com_port, baud_rate=57600, timeout=5)`**
- Establishes connection to drone(s) via serial/UDP
- Detects all available drones by listening for HEARTBEAT messages
- Returns list of detected drone system IDs
- Default configuration: UDP connection to simulator at `udp:172.19.144.1:14550`
- Waits up to `timeout` seconds for drone discovery

**`start_attitude_monitoring(update_interval=0.1)`**
- Launches background daemon thread for continuous telemetry monitoring
- Monitors `GLOBAL_POSITION_INT` messages for position and altitude data
- Updates internal `attitude_heading` dictionary with live data:
  - `heading`: Drone compass heading (degrees)
  - `latitude`: GPS latitude (decimal degrees)
  - `longitude`: GPS longitude (decimal degrees)
  - `altitude`: Relative altitude above ground level (meters)
  - `timestamp`: Unix timestamp of last update

**`get_live_drone_attitude(system_id)`**
- Returns latest attitude data for specified drone
- Returns `None` if drone not found or no data available

**`get_all_live_drone_attitudes()`**
- Returns dictionary of attitude data for all detected drones
- Key: drone system_id, Value: attitude dictionary

**`arm_drone(system_id)` / `arm_all_drones()`**
- Arms specified drone or all drones
- Sends MAV_CMD_COMPONENT_ARM_DISARM command with param1=1
- Required before takeoff
- Returns success status

**`disarm_drone(system_id)` / `disarm_all_drones()`**
- Disarms specified drone or all drones
- Sends MAV_CMD_COMPONENT_ARM_DISARM command with param1=0
- Safety feature to stop motors

**`set_drone_mode(system_id, mode_name)` / `set_all_drone_modes(mode_name)`**
- Changes flight mode for specified drone(s)
- Supported modes: STABILIZE, GUIDED, AUTO, LOITER, RTL, LAND, etc.
- Mode must be uppercase string
- GUIDED mode required for programmatic waypoint navigation

**`takeoff_drone(system_id, altitude_meters)` / `takeoff_all_drones(altitude_meters)`**
- Initiates takeoff to specified altitude
- Sends MAV_CMD_NAV_TAKEOFF command
- Altitude specified in meters above ground level (AGL)

**`goto_location(system_id, latitude, longitude, altitude_meters)`**
- Commands drone to fly to specific GPS coordinates
- Uses `set_position_target_global_int` for precise positioning
- Coordinates in decimal degrees, altitude in meters
- Frame: MAV_FRAME_GLOBAL_RELATIVE_ALT_INT (relative to home)

---

### 2. `spatiotemporal.py`
**Location**: `src/deconfliction/spatiotemporal.py`  
**Purpose**: Core collision detection algorithm using 4D spatiotemporal analysis.

#### Configuration:
- `SAFETY_DISTANCE_METERS = 12`: Minimum safe separation distance (configurable)

#### Main Function:

**`detect_conflicts(new_path, existing_paths, safety_distance=12)`**

**Algorithm Overview**:
1. **Time Window Filtering**: Skip path pairs with no temporal overlap
2. **Segment-by-Segment Analysis**: Compare each segment of new path with existing path segments
3. **Temporal Interpolation**: Sample 4 time points within overlapping intervals
4. **Position Interpolation**: Calculate drone positions at each sample time using linear interpolation
5. **3D Distance Calculation**:
   - Horizontal distance: Convert lat/lon delta to meters (×111,000)
   - Vertical distance: Direct altitude difference
   - Total distance: Euclidean 3D distance
6. **Conflict Detection**: Flag if distance < safety_distance

**Input Parameters**:
- `new_path`: DataFrame with columns: `drone_id`, `lat`, `lon`, `alt`, `timestamp`
- `existing_paths`: DataFrame with same structure, potentially multiple drones
- `safety_distance`: Minimum safe separation in meters

**Returns**:
List of conflict dictionaries containing:
```python
{
    "drone_id": str,          # ID of conflicting drone
    "time": datetime,         # Time of conflict
    "lat": float,             # Latitude of conflict point
    "lon": float,             # Longitude of conflict point
    "alt": float,             # Altitude of conflict point
    "distance": float         # Distance between drones (meters)
}
```

**Mathematical Details**:
- Linear interpolation formula: `P(t) = P1 + u × (P2 - P1)` where `u = (t - t1) / (t2 - t1)`
- Lat/Lon to meters conversion: Approximate using 111,000 meters per degree
- 3D distance: `sqrt(horizontal_distance² + vertical_distance²)`

---

### 3. `explain.py`
**Location**: `src/deconfliction/explain.py`  
**Purpose**: Convert raw conflict alerts into human-readable messages for display.

#### Main Function:

**`explain_conflicts(alerts)`**

**Input**: List of conflict dictionaries from `detect_conflicts()`

**Output**: List of formatted strings containing:
- Summary header (safe or number of conflicts)
- Grouped conflicts by drone ID
- Detailed information for each conflict:
  - Timestamp
  - GPS coordinates
  - Altitude
  - Distance to new path

**Example Output**:
```
⚠️ COLLISION RISK DETECTED: 3 conflict(s)
------------------------------------------------------------
  Conflicts with drone_2:
  ├─ Time: 2025-12-23 05:03:45
  ├─ Position: (18.571234, 73.768901)
  ├─ Altitude: 15.3 m
  └─ Distance: 8.7 m
```

---

### 4. `simulated_paths.py`
**Location**: `src/data_generation/simulated_paths.py`  
**Purpose**: Generate realistic simulated drone flight paths for testing.

#### Configuration:
- **Bounding Box**: Operational area defined by corner coordinates (a, b, c, d)
  - Latitude range: 18.5615 to 18.5721
  - Longitude range: 73.7675 to 73.7775
- **Altitude Range**: 20m to 60m (with start/end at 10m)

#### Key Functions:

**`random_wp(t)`**
- Generates random waypoint within operational area
- Returns tuple: (lat, lon, alt, timestamp)

**`generate_path(path_id, ref_start_time)`**
- Creates single drone path with 2-4 random waypoints
- Path characteristics:
  - Starts at altitude 10m (at min or max latitude boundary)
  - Contains 0-2 intermediate waypoints at random altitudes
  - Ends at altitude 10m (at opposite boundary)
  - Mission duration: 60-1200 seconds
  - Start time: randomized within 2-hour window

**`generate_simulated_paths(num_paths=20)`**
- Generates dataset of multiple drone paths
- Saves to Excel file: `data/simulated_paths.xlsx`
- Columns: `drone_id`, `lat`, `lon`, `alt`, `timestamp`
- Default: 20 drone paths

**Use Case**: Create test data for validating collision detection without real drones.

---

### 5. `normalize.py`
**Location**: `src/data_generation/normalize.py`  
**Purpose**: Normalize GPS coordinates and timestamps to 0-1 range for analysis and visualization.

#### Key Functions:

**`normalize_paths(input_excel, output_excel)`**
- Reads simulated paths from Excel
- Converts timestamps to datetime objects
- Applies min-max normalization:
  - `x_norm = (lon - lon_min) / (lon_max - lon_min)`
  - `y_norm = (lat - lat_min) / (lat_max - lat_min)`
  - `z_norm = (alt - alt_min) / (alt_max - alt_min)`
  - `t_norm = (timestamp - t_min) / (t_max - t_min)`
- Saves normalized data to `data/normalized_paths.xlsx`

**`plot_normalized_3d(normalized_excel)`**
- Creates 3D matplotlib visualization
- Plots each drone path in normalized coordinate space
- Axes: X (longitude), Y (latitude), Z (altitude)
- Each path colored uniquely with legend

**Use Case**: Prepare data for analysis and create visual overview of flight patterns.

---

### 6. `main_window.py`
**Location**: `src/ui/main_window.py`  
**Purpose**: PyQt5-based graphical user interface for interactive path planning and conflict analysis.

#### Class: `MainWindow`

**Key Attributes**:
- `stored_paths`: DataFrame of existing drone paths (loaded from Excel)
- `new_path`: List of waypoint dictionaries for new path being created
- `path_is_safe`: Boolean flag indicating analysis result (None/True/False)
- `log`: List of activity messages
- `map_view`: QWebEngineView displaying Leaflet map
- `bridge`: MapBridge object for JavaScript-Python communication

#### UI Components:

**Left Panel (Control Panel)**:
- **Connect Button**: Establishes connection to drone system
- **Execute Mission Button**: Flies drone through planned waypoints
- **Load Existing Paths**: Loads `normalized_paths.xlsx` from data directory
- **Analyze Collision Risk**: Runs conflict detection algorithm
- **Clear New Path**: Removes all waypoints from current plan
- **Text Input Area**: Bulk waypoint entry in format `(lat, lon, alt, 'YYYY-MM-DD HH:MM:SS')`
- **Activity Log**: Read-only text display showing system messages

**Right Panel (Interactive Map)**:
- Leaflet-based OpenStreetMap display
- Click to add waypoints
- Hover over waypoints for details
- Visual conflict markers with popup details

#### Key Methods:

**`connect_to_drones()`**
- Initializes drone controller
- Calls `controller.connect_to_drones()` with COM port settings
- Logs connection status

**`execute_mission()`**
- Pre-flight validation:
  - Checks if waypoints exist
  - Verifies path has been analyzed
  - Confirms path is safe
- Mission sequence:
  1. Set GUIDED mode
  2. Arm drone (system_id=2)
  3. Takeoff to first waypoint altitude
  4. Sequentially navigate to each waypoint using `goto_location()`
  5. 20-second delay between waypoints for flight completion
- Logs each step to activity log

**`load_paths()`**
- Loads `data/normalized_paths.xlsx`
- Stores in `self.stored_paths` DataFrame
- Calls `draw_existing_paths()` to visualize

**`draw_existing_paths()`**
- Groups paths by drone_id
- Assigns unique color to each drone
- Calls JavaScript `drawPath()` function via bridge
- Displays waypoint labels and tooltips

**`draw_new_path()`**
- Clears previous new path markers
- Sorts waypoints by timestamp
- Draws red dashed line connecting waypoints
- Labels waypoints as "N1", "N2", etc.

**`analyze_paths()`**
- Validation checks:
  - Minimum 2 waypoints required
  - Existing paths must be loaded
- Converts `new_path` list to DataFrame
- Calls `detect_conflicts()` from spatiotemporal module
- Visualizes conflicts on map with yellow markers
- Generates human-readable report via `explain_conflicts()`
- Sets `path_is_safe` flag based on results

**`add_path_from_text()`**
- Parses text input line-by-line
- Expected format: `(lat, lon, alt, 'YYYY-MM-DD HH:MM:SS')`
- Validates each line and converts to waypoint dictionary
- Supports comments (lines starting with #)
- Adds valid waypoints to `new_path`
- Redraws path visualization

**`reset_new()`**
- Clears `new_path` list
- Removes new path markers from map (preserves existing paths)
- Clears collision markers

#### Class: `MapBridge`

**Purpose**: Enable JavaScript-to-Python communication for map interactions.

**`addWaypoint(lat, lng)`** (PyQt slot):
- Triggered when user clicks on map
- Prompts for altitude input (QInputDialog)
- Prompts for timestamp input
- Validates inputs
- Adds waypoint to `new_path`
- Logs action and redraws path

#### JavaScript Map Functions:

**`drawPath(path, color, droneId, isNew)`**
- Creates Leaflet polyline connecting waypoints
- Adds circle markers at each waypoint
- Creates interactive tooltips with full waypoint details
- Adds permanent labels (N1, N2... for new paths, 1, 2... for existing)

**`markCollision(collisionData)`**
- Places red/yellow warning marker at conflict location
- Creates detailed popup with conflict information
- Adds permanent "⚠️ COLLISION" tooltip

**`clearNewPathWaypoints()`** / **`clearPaths()`** / **`clearCollisions()`**
- Remove specific layer types from map

---

### 7. `show_paths.py`
**Location**: `scripts/show_paths.py`  
**Purpose**: Standalone script for geographic visualization of drone paths using Cartopy.

#### Functionality:
- Loads `data/normalized_paths.xlsx`
- Creates matplotlib figure with Cartopy map projection
- Adds geographic features:
  - Land and ocean areas
  - Country borders
  - Lakes and rivers
- Plots each drone path as colored line with markers
- Displays legend identifying each drone

**Use Case**: Quick visualization of all drone paths without running full GUI application.

**Dependencies**: pandas, matplotlib, cartopy

---

### 8. `test_spatiotemporal.py`
**Location**: `tests/test_spatiotemporal.py`  
**Purpose**: Comprehensive unit test suite for collision detection algorithm.

#### Test Coverage (15 Tests):

**Spatial Tests**:
1. **Exact Same Position**: Drones at identical coordinates should conflict
2. **Close Horizontal Proximity**: <12m horizontal separation should conflict
3. **Safe Horizontal Distance**: >12m horizontal separation should not conflict
4. **Vertical Separation**: >12m vertical separation should not conflict
5. **Close Vertical Separation**: <12m vertical separation should conflict

**Temporal Tests**:
6. **Crossing Paths Different Times**: Spatial overlap but temporal separation is safe
7. **Crossing Paths Overlapping Times**: Spatial and temporal overlap should conflict

**Complex Scenarios**:
8. **Parallel Paths Safe Distance**: Parallel trajectories >12m apart are safe
9. **Parallel Paths Close Proximity**: Parallel trajectories <12m apart should conflict
10. **Head-On Collision**: Opposite direction travel on same path should conflict
11. **Overtaking Same Altitude**: Faster drone catching slower at same altitude conflicts
12. **Overtaking Different Altitudes**: Overtaking with >12m altitude difference is safe
13. **Multi-Segment Path**: Conflict detection in middle of multi-waypoint path
14. **Empty Path**: No existing paths should yield no conflicts
15. **3D Distance Boundary**: Exactly 12m separation (boundary case) should not conflict

#### Test Structure:
```python
def test_name():
    """Description of test scenario"""
    new_path_points = [(lat, lon, alt, time), ...]
    existing_points = [(lat, lon, alt, time), ...]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) > 0, "Expected conflicts"  # or == 0 for safe
```

**Running Tests**:
```bash
python tests/test_spatiotemporal.py
```

**Expected Output**:
- ✅ for passed tests
- ❌ for failed tests with assertion message
- Final summary: X passed, Y failed out of 15 tests

---

## Data Flow Diagram

```
1. Data Generation Phase:
   simulated_paths.py → data/simulated_paths.xlsx
   ↓
   normalize.py → data/normalized_paths.xlsx

2. GUI Interaction Phase:
   main_window.py loads normalized_paths.xlsx
   ↓
   User clicks map to create new_path waypoints
   ↓
   User clicks "Analyze Collision Risk"
   ↓
   spatiotemporal.py processes conflict detection
   ↓
   explain.py formats results
   ↓
   GUI displays conflicts on map

3. Mission Execution Phase:
   User clicks "Execute Mission"
   ↓
   main_window.py validates path safety
   ↓
   drone_controller.py sends MAVLink commands
   ↓
   Drone flies through waypoints
```

---

## Technical Requirements

### Dependencies:
```
Core:
- Python 3.8+
- pandas
- numpy

Drone Control:
- pymavlink

GUI:
- PyQt5
- PyQtWebEngine

Visualization:
- matplotlib
- cartopy (optional, for show_paths.py)

Map Display:
- Leaflet.js (loaded via CDN)
- OpenStreetMap tiles
```

### Hardware Requirements:
- MAVLink-compatible drone or simulator (ArduPilot, PX4)
- Serial/UDP connection to flight controller
- Minimum 4GB RAM for GUI operation

---

## Configuration Parameters

### Adjustable Constants:

**spatiotemporal.py**:
```python
SAFETY_DISTANCE_METERS = 12  # Minimum safe separation
```

**simulated_paths.py**:
```python
# Operational area boundaries
a = (18.571347469474013, 73.76757961632767)  # NW corner
b = (18.572087788390924, 73.77660917773662)  # NE corner
c = (18.561547389915898, 73.76748613083969)  # SW corner
d = (18.562079732297835, 73.77751174762237)  # SE corner

ALT_MIN = 20  # Minimum operational altitude (m)
ALT_MAX = 60  # Maximum operational altitude (m)
```

**drone_controller.py**:
```python
connection = mavutil.mavlink_connection('udp:172.19.144.1:14550')
# Change to serial: 'COM3' or '/dev/ttyUSB0' for hardware
```

---

## Usage Workflows

### Workflow 1: Test with Simulated Data

1. **Generate test paths**:
   ```bash
   python src/data_generation/simulated_paths.py
   python src/data_generation/normalize.py
   ```

2. **Launch GUI**:
   ```bash
   python src/ui/main_window.py
   ```

3. **Load existing paths** (click "📂 Load Existing Paths")

4. **Create new path** by clicking on map or using text input

5. **Analyze for conflicts** (click "🔍 Analyze Collision Risk")

6. **Review results** in activity log and map markers

### Workflow 2: Real Drone Mission

1. **Connect hardware**:
   - Ensure drone is powered and connected via telemetry
   - Update connection string in `drone_controller.py` if needed

2. **Launch GUI and connect**:
   ```bash
   python src/ui/main_window.py
   ```
   - Click "Connect" button

3. **Load existing paths** to check airspace

4. **Plan mission** by adding waypoints

5. **Analyze path** for conflicts

6. **Execute mission** if path is safe (click "Execute Mission")

### Workflow 3: Visualization Only

```bash
python scripts/show_paths.py
```

---

## Safety Considerations

### Critical Safety Rules:

1. **Always analyze before execution**: The system requires conflict analysis before allowing mission execution

2. **Safety distance buffer**: Default 12m separation accounts for:
   - GPS uncertainty (~3-5m)
   - Drone position hold accuracy (~2-3m)
   - Communication latency effects
   - Rotor wash interference zone (~5-8m)

3. **Real-time monitoring**: Background attitude monitoring provides live position updates

4. **Manual override**: Pilot can always switch to manual mode via RC transmitter

5. **Geofencing**: Simulated paths constrained to operational bounding box

### Limitations:

- **Wind effects not modeled**: Real flight may deviate from planned path
- **No dynamic re-routing**: System detects conflicts but doesn't suggest alternatives
- **Single altitude layer**: No sophisticated 3D airspace management
- **No emergency procedures**: System doesn't handle in-flight conflicts
- **Assumes constant velocity**: Linear interpolation may not match actual flight dynamics

---

## Troubleshooting

### Common Issues:

**Issue**: "No drones detected"
- **Solution**: Check connection string, verify simulator/drone is running, confirm network settings

**Issue**: "Artifact load failed" or GUI crashes
- **Solution**: Ensure PyQt5 and PyQtWebEngine are installed correctly

**Issue**: False positive conflicts
- **Solution**: Adjust `SAFETY_DISTANCE_METERS` or increase temporal sampling in spatiotemporal.py

**Issue**: Mission execution fails
- **Solution**: Verify drone is armed, in GUIDED mode, and has GPS lock

**Issue**: Map doesn't load
- **Solution**: Check internet connection (OpenStreetMap tiles), verify JavaScript console for errors

---

### Technologies Used:
- **MAVLink Protocol**: Micro Air Vehicle communication standard
- **Leaflet.js**: Interactive web maps
- **PyQt5**: Python GUI framework
- **Pandas**: Data manipulation library
- **OpenStreetMap**: Map tile provider

### Algorithm References:
- Spatiotemporal conflict detection based on 4D trajectory analysis
- Linear interpolation for position estimation between waypoints
- Euclidean distance metric for 3D separation calculation

