# Drone Path Conflict Detection System

A Python-based system for detecting spatiotemporal conflicts between drone flight paths. The system analyzes new drone paths against existing trajectories to identify potential collision risks in 4D space (3D position + time).

## Features

- **4D Spatiotemporal Collision Detection** - Analyzes position and time simultaneously
- **Interactive Map-Based Planning** - Visual waypoint creation with Leaflet integration
- **MAVLink Drone Control** - Direct integration with ArduPilot/PX4 flight controllers
- **Real-Time Telemetry** - Live monitoring of drone status and position
- **Mission Execution** - Automated flight through validated waypoints
- **Comprehensive Testing** - 15 unit tests covering edge cases and scenarios

## Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Safety Warnings](#safety-warnings)
- [Advanced Usage](#advanced-usage)
- [Contributing](#contributing)

## System Requirements

### Software
- Python 3.8 or higher
- pip package manager
- Internet connection (for map tiles)

### Hardware (for real drone operations)
- MAVLink-compatible drone or simulator (ArduPilot/PX4)
- Serial or UDP connection to flight controller
- Minimum 4GB RAM

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/drone-conflict-detection.git
cd drone-conflict-detection
```

2. Install required Python packages:
```bash
pip install pandas numpy pymavlink pyqt5 pyqtwebengine matplotlib openpyxl pytest
```

3. Optional (for geographic visualization):
```bash
pip install cartopy
```

4. Verify project structure:
```
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
```

## Running the Project

> **IMPORTANT:**  
> Always run commands from the **project root directory** using the `-m` flag to ensure proper module imports.

### Command Reference

#### 1. Generate Simulated Drone Paths

Creates randomized drone flight paths within a bounded area and saves them to `data/simulated_paths.xlsx`.

```bash
python -m src.data_generation.simulated_paths
```

**Output:**
- `data/simulated_paths.xlsx` with columns: `drone_id`, `lat`, `lon`, `alt`, `timestamp`

#### 2. Normalize Paths & Generate 3D Visualization

Normalizes spatial and temporal values and generates a 3D visualization of trajectories.

```bash
python -m src.data_generation.normalize
```

**Output:**
- `data/normalized_paths.xlsx` with normalized coordinates
- 3D plot window (XYZ space visualization)

#### 3. Static 2D Map Visualization (Optional)

Displays all existing drone paths on a geographic map using Cartopy.

```bash
python -m scripts.show_paths
```

**Requirements:** `cartopy` must be installed

#### 4. Run Unit Tests

Validates intersecting and non-intersecting path scenarios.

```bash
python -m pytest tests/test_spatiotemporal.py
```

**Expected output:**
```
15 passed in X.XXs
```

#### 5. Launch GUI Application (Main System)

Starts the interactive map-based planning and conflict detection interface.

```bash
python -m src.ui.main_window
```

**From the GUI you can:**
- Load existing paths from Excel files
- Create new paths (map click or text input)
- Analyze collision risks in real-time
- Execute approved missions via MAVLink
- Monitor drone telemetry

#### 6. MAVLink Connection Test (Optional)

Useful for verifying simulator or drone connectivity before mission execution.

```bash
python - <<EOF
from pymavlink import mavutil
conn = mavutil.mavlink_connection('udp:127.0.0.1:14550')
msg = conn.recv_match(type='HEARTBEAT', blocking=True)
print(f"Connected to drone: System ID {msg.get_srcSystem()}")
EOF
```

### Recommended Run Order (First-Time Setup)

```bash
# Step 1: Generate test data
python -m src.data_generation.simulated_paths

# Step 2: Normalize the data
python -m src.data_generation.normalize

# Step 3: (Optional) Run tests to verify system
python -m pytest tests/test_spatiotemporal.py

# Step 4: Launch the GUI application
python -m src.ui.main_window
```

### Common Mistakes to Avoid

**INCORRECT - Do NOT run files directly:**
```bash
# This will cause import errors
python src/ui/main_window.py
cd src/ui && python main_window.py
```

**CORRECT - Always use the `-m` flag:**
```bash
# This ensures proper module resolution
python -m src.ui.main_window
```

## Quick Start

### Step 1: Generate Test Data

```bash
python -m src.data_generation.simulated_paths
python -m src.data_generation.normalize
```

This creates:
- `data/simulated_paths.xlsx` - Raw test paths
- `data/normalized_paths.xlsx` - Processed paths

### Step 2: Run Tests (Optional)

```bash
python -m pytest tests/test_spatiotemporal.py
```

Expected output: `15 passed, 0 failed`

### Step 3: Launch GUI Application

```bash
python -m src.ui.main_window
```

## Usage Guide

### Loading Existing Paths

1. Click **"Load Existing Paths (xlsx)"** button
2. The system loads `normalized_paths.xlsx` from the data folder
3. Existing drone paths are displayed on the map

### Creating a New Path

#### Option A: Interactive Map Input
1. Click any location on the map
2. Enter altitude in meters
3. Enter arrival time in format: `YYYY-MM-DD HH:MM:SS`

#### Option B: Text Input
1. Enter waypoints in the text box using this format:
```python
(18.5720, 73.7713, 10, '2025-12-23 12:42:18')
(18.5687, 73.7753, 33, '2025-12-23 12:46:39')
```
2. Click **"Add Path from Text"**

### Analyzing for Conflicts

1. Click **"Analyze Collision Risk"** button
2. System analyzes the path against all existing trajectories
3. Results appear in the Activity Log
4. Conflicts are marked on the map with colored markers

#### Result Indicators
- **PATH SAFE** - No conflicts detected
- **COLLISION RISK** - Conflicts found with detailed information

### Mission Execution (Requires Drone/Simulator)

1. **Connect Drone:**
   - Click **"Connect"** button
   - Wait for connection confirmation in Activity Log

2. **Execute Mission** (only if path is safe):
   - Click **"Execute Mission"** button
   - The drone will:
     - Set GUIDED mode
     - Arm motors
     - Takeoff to first waypoint altitude
     - Fly through all waypoints sequentially
     - Log progress in Activity Log

## Configuration

### Safety Distance

Edit `src/deconfliction/spatiotemporal.py`:
```python
SAFETY_DISTANCE_METERS = 12  # Default: 12 meters
```

### Operational Area

Edit `src/data_generation/simulated_paths.py`:
```python
# Define boundary coordinates
a = (lat_nw, lon_nw)  # Northwest corner
b = (lat_ne, lon_ne)  # Northeast corner
c = (lat_sw, lon_sw)  # Southwest corner
d = (lat_se, lon_se)  # Southeast corner

# Altitude range
ALT_MIN = 10
ALT_MAX = 100
```

### Drone Connection

Edit `src/control/drone_controller.py` (line 15):

**For Simulator:**
```python
connection = mavutil.mavlink_connection('udp:127.0.0.1:14550')
```

**For Serial Connection:**
```python
# Windows
connection = mavutil.mavlink_connection('COM3', baud=57600)

# Linux
connection = mavutil.mavlink_connection('/dev/ttyUSB0', baud=57600)
```

## Project Structure

### Control Layer
**`drone_controller.py`**
- MAVLink communication protocol
- Drone arming/disarming functions
- Flight mode management
- Takeoff and navigation commands
- Real-time telemetry monitoring

### Deconfliction Layer
**`spatiotemporal.py`**
- Core collision detection algorithm
- 4D trajectory analysis
- Linear interpolation between waypoints
- 3D Euclidean distance calculations

**`explain.py`**
- Converts raw conflict data to human-readable messages
- Groups conflicts by drone
- Formats output for display

### Data Generation Layer
**`simulated_paths.py`**
- Generates random test drone paths
- Creates Excel file with waypoints
- Configurable operational area

**`normalize.py`**
- Min-max normalization of coordinates
- Converts timestamps to relative values
- 3D visualization of paths

### User Interface Layer
**`main_window.py`**
- PyQt5 GUI application
- Leaflet map integration
- Interactive waypoint creation
- Conflict visualization
- Mission execution control

### Utilities
**`show_paths.py`**
- Standalone path visualization using Cartopy

**`test_spatiotemporal.py`**
- 15 comprehensive unit tests
- Validates collision detection logic

## How It Works

### Collision Detection Algorithm

1. **Time Window Check** - Filters out paths with no temporal overlap
2. **Segment Analysis** - Compares each segment of the new path against existing paths
3. **Position Interpolation** - Calculates exact positions at sampled time points
4. **Distance Calculation** - Computes 3D Euclidean distance between positions
5. **Conflict Flagging** - Alerts if distance falls below safety threshold

### Safety Distance Rationale (12 meters)

- GPS uncertainty: ±3-5 meters
- Position hold accuracy: ±2-3 meters
- Communication latency effects
- Rotor wash interference zone: ~5-8 meters
- Safety buffer for unexpected deviations

### Data Files

**`simulated_paths.xlsx`**
- Columns: `drone_id`, `lat`, `lon`, `alt`, `timestamp`
- Contains raw simulated drone paths
- Created by `simulated_paths.py`

**`normalized_paths.xlsx`**
- Columns: `drone_id`, `lat`, `lon`, `alt`, `timestamp`, `x_norm`, `y_norm`, `z_norm`, `t_norm`
- Contains normalized coordinates for analysis
- Created by `normalize.py`

## Testing

### Running Unit Tests

```bash
cd tests
python test_spatiotemporal.py
```

### Test Coverage

- Exact position/time conflicts
- Horizontal proximity detection
- Vertical separation safety
- Temporal separation handling
- Crossing paths scenarios
- Parallel paths analysis
- Head-on collision detection
- Overtaking scenarios
- Multi-segment path analysis
- Boundary condition testing

**Expected Result:** `15 passed, 0 failed`

## Troubleshooting

### "No drones detected"

**Solution:**
- Verify simulator/drone is running
- Check connection string in `drone_controller.py`
- Confirm network/serial settings
- Check firewall settings for UDP connections

### GUI doesn't load or crashes

**Solution:**
```bash
pip install --upgrade pyqt5 pyqtwebengine
```
- Confirm Python version 3.8+
- Run with verbose output: `python -v main_window.py`

### Map tiles don't load

**Solution:**
- Check internet connection
- Verify no proxy/firewall blocking OpenStreetMap
- Wait 5-10 seconds for initial tile loading

### "Load existing paths" does nothing

**Solution:**
- Generate data first: run `simulated_paths.py` and `normalize.py`
- Verify `data/normalized_paths.xlsx` exists
- Check file permissions

### Tests failing

**Solution:**
- Review test output for specific failures
- Check `SAFETY_DISTANCE_METERS` setting
- Verify `spatiotemporal.py` has not been modified

### Mission execution fails

**Solution:**
- Confirm path has been analyzed first
- Verify path is safe (no conflicts detected)
- Check drone is connected
- Ensure drone has GPS lock (outdoor or GPS simulator)
- Verify battery level is sufficient

### Connection Testing

Test your MAVLink connection:
```python
from pymavlink import mavutil

# Connect to drone
conn = mavutil.mavlink_connection('udp:127.0.0.1:14550')

# Wait for heartbeat
msg = conn.recv_match(type='HEARTBEAT', blocking=True)
print(f"Connected to drone: System ID {msg.get_srcSystem()}")
```

## Safety Warnings

### IMPORTANT SAFETY INFORMATION

1. **TEST IN SIMULATION FIRST**
   - Always test new paths in a simulator before real flights
   - Verify all waypoints are within safe operational area

2. **MANUAL OVERRIDE REQUIRED**
   - Maintain ability to switch to manual control
   - Always have RC transmitter ready

3. **SYSTEM LIMITATIONS**
   - Does NOT account for wind effects
   - Does NOT provide dynamic re-routing
   - Does NOT detect obstacles (buildings, trees, etc.)
   - GPS accuracy varies by environment

4. **LEGAL COMPLIANCE**
   - Follow local aviation regulations
   - Obtain necessary permits/authorizations
   - Maintain visual line of sight (VLOS)
   - Respect no-fly zones

5. **PRE-FLIGHT CHECKLIST**
   - [ ] Analyze path for conflicts
   - [ ] Verify all waypoints are valid
   - [ ] Check weather conditions
   - [ ] Ensure sufficient battery
   - [ ] Confirm GPS lock
   - [ ] Test manual control
   - [ ] Clear operational area of obstacles

## Advanced Usage

### Custom Operational Area

Edit `src/data_generation/simulated_paths.py`:
```python
# Define new corner coordinates
a = (lat_nw, lon_nw)  # Northwest corner
b = (lat_ne, lon_ne)  # Northeast corner
c = (lat_sw, lon_sw)  # Southwest corner
d = (lat_se, lon_se)  # Southeast corner
```

### Adjusting Safety Parameters

Edit `src/deconfliction/spatiotemporal.py`:
```python
# Increase minimum separation
SAFETY_DISTANCE_METERS = 15

# Increase temporal sampling (line 65)
ts = pd.date_range(t_start, t_end, periods=8)
# More samples = more accurate but slower
```

### Batch Path Analysis

For analyzing multiple paths programmatically:
```python
import pandas as pd
from src.deconfliction.spatiotemporal import detect_conflicts

# Load existing paths
existing_paths = pd.read_excel('data/normalized_paths.xlsx')

# Analyze multiple candidate paths
results = []
for candidate_path in candidate_paths_list:
    conflicts = detect_conflicts(candidate_path, existing_paths)
    results.append({
        'path_id': candidate_path['id'],
        'conflicts': len(conflicts),
        'safe': len(conflicts) == 0
    })

# Export summary
summary_df = pd.DataFrame(results)
summary_df.to_excel('analysis_results.xlsx')
```

### Performance Optimization

**For Large Datasets:**
- Implement spatial indexing (quadtree or R-tree)
- Use multiprocessing for parallel path analysis
- Reduce temporal sampling (trade accuracy for speed)

**For Real-Time Operation:**
- Pre-compute path segments
- Cache interpolation results
- Use numpy vectorization
- Implement distance early-exit conditions

### Extending the System

**Potential Features:**
- Alternative path suggestions
- Wind effect modeling
- Battery consumption estimation
- Multi-objective optimization
- No-fly zone integration

**Integration Points:**
- REST API: Wrap `detect_conflicts()` in Flask/FastAPI
- ROS Integration: Create ROS node for path planning
- Database Storage: Store paths in PostgreSQL/MongoDB
- Cloud Deployment: Containerize with Docker

## System Architecture

### Data Flow

1. **Generate/Load** → `simulated_paths.xlsx`
2. **Normalize** → `normalized_paths.xlsx`
3. **Load in GUI** → Display on interactive map
4. **User creates path** → Click on map or text input
5. **Analyze** → `spatiotemporal.py` collision detection
6. **Display results** → Map markers + Activity log
7. **Execute (optional)** → `drone_controller.py` → Physical drone

### Key Algorithms

- **Linear Interpolation** - Position estimation between waypoints
- **Euclidean Distance** - 3D spatial separation calculation
- **Time Window Filtering** - Efficiency optimization
- **Segment-by-Segment Analysis** - Granular conflict checking

