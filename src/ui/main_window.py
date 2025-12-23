import sys
import json
import numpy as np
import pandas as pd
import time 
from pathlib import Path
import pandas as pd
from datetime import datetime


from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QLabel, QInputDialog, QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSlot, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWidgets import QMessageBox

from src.deconfliction.spatiotemporal import detect_conflicts
from src.deconfliction.explain import explain_conflicts

from src.control.drone_controller import SimpleDroneController

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

controller = SimpleDroneController()
# -----------------------------------
# JS ↔ Python bridge
# -----------------------------------
from PyQt5.QtCore import QObject

class MapBridge(QObject):
    def __init__(self, mw):
        super().__init__()
        self.mw = mw

    @pyqtSlot(float, float)
    def addWaypoint(self, lat, lng):
        try:
            alt, ok1 = QInputDialog.getDouble(
                self.mw, "Altitude", "Enter altitude (m):", 10, 0, 500, 1
            )
            t_str, ok2 = QInputDialog.getText(
                self.mw, "Time", 
                "Arrival time (YYYY-mm-dd HH:MM:SS):",
                text=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            if not(ok1 and ok2):
                return

            t = pd.to_datetime(t_str)
            
            if pd.isna(t):
                self.mw.log.append("❌ Invalid timestamp format!")
                self.mw.refresh_text()
                return

            wp = {"lat":lat,"lon":lng,"alt":alt,"timestamp":t}
            self.mw.new_path.append(wp)

            self.mw.log.append(f"✓ Waypoint added: lat={lat:.6f}, lon={lng:.6f}, alt={alt}m, time={t}")
            self.mw.refresh_text()
            
            # Redraw new path with updated waypoint info
            self.mw.draw_new_path()
        except Exception as e:
            self.mw.log.append(f"❌ Error adding waypoint: {str(e)}")
            self.mw.refresh_text()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Path Conflict Detection Panel")
        self.resize(1600, 1000)

        self.stored_paths = None  # from xlsx
        self.new_path = []        # clicked waypoints
        self.path_is_safe = None

        self.init_ui()
        


    def init_ui(self):
        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        self.setCentralWidget(main)

        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # -------- LEFT PANEL (Controls & Log) ----------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Title
        title = QLabel("Control Panel")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        left_layout.addWidget(title)

        
        # Buttons
        connect_btn = QPushButton("Connect")
        connect_btn.clicked.connect(self.connect_to_drones)
        connect_btn.setMinimumHeight(40)
        left_layout.addWidget(connect_btn)

        execute_mission_btn = QPushButton("Execute Mission")
        execute_mission_btn.clicked.connect(self.execute_mission)
        execute_mission_btn.setMinimumHeight(40)
        left_layout.addWidget(execute_mission_btn)

        load_btn = QPushButton(" Load Existing Paths (xlsx)")
        load_btn.clicked.connect(self.load_paths)
        load_btn.setMinimumHeight(40)
        
        analyze_btn = QPushButton(" Analyze Collision Risk")
        analyze_btn.clicked.connect(self.analyze_paths)
        analyze_btn.setMinimumHeight(40)
        analyze_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        clear_btn = QPushButton(" Clear New Path")
        clear_btn.clicked.connect(lambda: self.reset_new())
        clear_btn.setMinimumHeight(40)

        ##------------------------------------------
        # Text input for bulk waypoint addition
        text_input_label = QLabel("Add Path from Text")
        text_input_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px; margin-top: 10px;")
        left_layout.addWidget(text_input_label)
        
        format_hint = QLabel("Format: (lat, lon, alt, 'YYYY-MM-DD HH:MM:SS')")
        format_hint.setStyleSheet("font-size: 10px; font-style: italic; padding: 2px;")
        left_layout.addWidget(format_hint)
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(
            "Enter waypoints, one per line:\n"
            "(18.5720, 73.7713, 10, '2025-12-22 12:42:18')\n"
            "(18.5687, 73.7753, 33, '2025-12-22 12:46:39')\n"
            "(18.5707, 73.7734, 48, '2025-12-22 12:51:00')"
        )
        self.text_input.setMaximumHeight(120)
        self.text_input.setStyleSheet("font-family: monospace; font-size: 10px;")
        left_layout.addWidget(self.text_input)
        
        add_text_btn = QPushButton(" Add Path from Text")
        add_text_btn.clicked.connect(self.add_path_from_text)
        add_text_btn.setMinimumHeight(35)
        left_layout.addWidget(add_text_btn)
        ##------------------------------------------

        left_layout.addWidget(load_btn)
        left_layout.addWidget(analyze_btn)
        left_layout.addWidget(clear_btn)
        
        # Status info
        status_label = QLabel("Activity Log")
        status_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px; margin-top: 10px;")
        left_layout.addWidget(status_label)

        self.log = []
        self.messages = QTextEdit()
        self.messages.setReadOnly(True)
        self.messages.setStyleSheet("background-color: #f5f5f5; font-family: monospace; font-size: 11px;")
        left_layout.addWidget(self.messages)
        
        # Instructions
        instructions = QLabel(
            "<b>Instructions:</b><br>"
            "1. Load existing paths<br>"
            "2. Click on map to add waypoints<br>"
            "3. Hover over waypoints for details<br>"
            "4. Analyze for conflicts"
        )
        instructions.setStyleSheet("padding: 10px; background-color: #e3f2fd; border-radius: 5px; font-size: 11px;")
        instructions.setWordWrap(True)
        left_layout.addWidget(instructions)

        # -------- RIGHT PANEL (Map) ----------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        self.map_view = QWebEngineView()
        right_layout.addWidget(self.map_view)

        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Set initial sizes: left panel 400px, rest for map
        splitter.setSizes([400, 1200])
        splitter.setStretchFactor(0, 0)  # Left panel doesn't stretch
        splitter.setStretchFactor(1, 1)  # Map stretches
        
        main_layout.addWidget(splitter)

        self.load_map()
        self.log.append(" Drone Path Conflict Detection System Initialized")
        self.log.append("📍 Click on the map to add waypoints for your new path")
        self.refresh_text()

    def load_map(self):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
        <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
        <style>
          body { margin:0; padding:0; overflow:hidden; }
          #map { height:100vh; width:100%; position:absolute; top:0; left:0; bottom:0; right:0; }
          .waypoint-label {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid #333;
            border-radius: 3px;
            padding: 2px 5px;
            font-size: 11px;
            font-weight: bold;
            white-space: nowrap;
          }
          .collision-popup {
            background: rgba(255, 255, 0, 0.95);
            border: 2px solid #ff0000;
            border-radius: 5px;
            padding: 8px;
            font-size: 12px;
            font-weight: bold;
            max-width: 250px;
          }
        </style>
        </head>
        <body>
        <div id="map"></div>

        <script>
        var map = L.map('map').setView([18.565743565704324, 73.77111577377781], 14);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
         { attribution:'© OpenStreetMap contributors'}
        ).addTo(map);

        var channel = new QWebChannel(qt.webChannelTransport,function(chan){
            bridge = chan.objects.bridge;
        });

        var existingWaypointMarkers = [];  // For existing drone paths
        var newPathMarkers = [];           // For new path being created
        var pathLayers = [];               // For existing drone paths
        var newPathPolyline = null;        // For new path polyline
        var collisionMarkers = [];

        map.on('click',function(e){
            bridge.addWaypoint(e.latlng.lat, e.latlng.lng);
        });

        function drawPath(path, color, droneId, isNew=false){
            var latlngs = path.map(p=>[p.lat,p.lon]);
            var polyline = L.polyline(latlngs,{
                color: color,
                weight: isNew ? 4 : 3,
                opacity: isNew ? 0.9 : 0.7,
                dashArray: isNew ? '10, 5' : null
            }).addTo(map);
            
            if (!isNew) {
                polyline.bindTooltip(`Drone: ${droneId}`, {permanent: false, direction: 'top'});
            }
            
            if (isNew) {
                newPathPolyline = polyline;
            } else {
                pathLayers.push(polyline);
            }

            // Add waypoint markers with detailed tooltips
            path.forEach((wp, idx) => {
                var markerColor = isNew ? 'red' : color;
                var marker = L.circleMarker([wp.lat, wp.lon], {
                    radius: isNew ? 7 : 5,
                    color: markerColor,
                    fillColor: markerColor,
                    fillOpacity: 0.8,
                    weight: 2
                }).addTo(map);

                // Create detailed tooltip
                var tooltipContent = isNew ? 
                    `<b>New Path - WP${idx + 1}</b><br>` :
                    `<b>${droneId} - WP${idx + 1}</b><br>`;
                
                tooltipContent += `Lat: ${wp.lat.toFixed(6)}<br>`;
                tooltipContent += `Lon: ${wp.lon.toFixed(6)}<br>`;
                tooltipContent += `Alt: ${wp.alt.toFixed(1)}m<br>`;
                tooltipContent += `Time: ${wp.time}`;

                marker.bindTooltip(tooltipContent, {
                    permanent: false,
                    direction: 'top',
                    offset: [0, -5]
                });

                // Add permanent label for waypoint number
                var labelIcon = L.divIcon({
                    className: 'waypoint-label',
                    html: isNew ? `N${idx + 1}` : `${idx + 1}`,
                    iconSize: [30, 20],
                    iconAnchor: [15, -10]
                });
                
                var label = L.marker([wp.lat, wp.lon], {
                    icon: labelIcon,
                    interactive: false
                }).addTo(map);

                // Store markers in appropriate array
                if (isNew) {
                    newPathMarkers.push(marker);
                    newPathMarkers.push(label);
                } else {
                    existingWaypointMarkers.push(marker);
                    existingWaypointMarkers.push(label);
                }
            });
        }

        function markCollision(collisionData){
            var marker = L.circleMarker([collisionData.lat, collisionData.lon], {
                radius: 15,
                color: 'red',
                fillColor: 'yellow',
                fillOpacity: 0.6,
                weight: 3
            }).addTo(map);

            // Create detailed collision popup
            var popupContent = `
                <div class="collision-popup">
                    <b>⚠️ COLLISION RISK</b><br>
                    <b>Drone:</b> ${collisionData.drone_id}<br>
                    <b>Time:</b> ${collisionData.time}<br>
                    <b>Position:</b><br>
                    &nbsp;&nbsp;Lat: ${collisionData.lat.toFixed(6)}<br>
                    &nbsp;&nbsp;Lon: ${collisionData.lon.toFixed(6)}<br>
                    &nbsp;&nbsp;Alt: ${collisionData.alt.toFixed(1)}m<br>
                    <b>Distance:</b> ${collisionData.distance}m
                </div>
            `;

            marker.bindPopup(popupContent, {
                permanent: false,
                closeButton: true
            });
            
            marker.bindTooltip('⚠️ COLLISION', {permanent: true, direction: 'top'});

            collisionMarkers.push(marker);
        }

        function clearNewPathWaypoints(){
            newPathMarkers.forEach(m => map.removeLayer(m));
            newPathMarkers = [];
            if (newPathPolyline) {
                map.removeLayer(newPathPolyline);
                newPathPolyline = null;
            }
        }

        function clearPaths(){
            pathLayers.forEach(p => map.removeLayer(p));
            pathLayers = [];
        }

        function clearCollisions(){
            collisionMarkers.forEach(m => map.removeLayer(m));
            collisionMarkers = [];
        }

        function clearAllWaypoints(){
            existingWaypointMarkers.forEach(m => map.removeLayer(m));
            existingWaypointMarkers = [];
            clearNewPathWaypoints();
        }

        </script>
        </body>
        </html>
        """

        self.bridge = MapBridge(self)
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.map_view.page().setWebChannel(self.channel)

        self.map_view.setHtml(html)

    def connect_to_drones(self):
        """Connect to the specified server"""
        try:

            drones = controller.connect_to_drones(com_port="COM3", baud_rate=57600)
            print("connection Done.")

        except Exception as e:
            self.log.append(f"❌ Connection failed: {str(e)}")
            self.refresh_text()


    def execute_mission(self):
        """Execute the mission by flying through all waypoints in new_path"""
        try:
            if not self.new_path:
                self.log.append("❌ No waypoints defined! Add waypoints first.")
                self.refresh_text()
                return
            
            if self.path_is_safe==None:
                self.log.append("❌ Cannot Execute Mission! Analysis Required !")
                self.refresh_text()
                return
            if self.path_is_safe==False:
                self.log.append("❌ Cannot Execute Mission! UnSafe FlightPath !")
                self.refresh_text()
                return
            
            # Sort waypoints by timestamp to ensure proper order
            points = sorted(self.new_path, key=lambda x: x['timestamp'])
            
            self.log.append(" Starting mission execution...")
            self.log.append(f"Number of waypoints: {len(points)}")
            self.refresh_text()
            
            # 1. Set drone to GUIDED mode
            self.log.append("Setting drone to GUIDED mode...")
            controller.set_drone_mode(2, "GUIDED")
            time.sleep(1)
            
            # 2. Arm the drone
            self.log.append("Arming drone...")
            controller.arm_drone(2)
            time.sleep(2)
            
            # 3. Takeoff to first waypoint altitude or 10m
            takeoff_alt = points[0]['alt'] if points else 10
            self.log.append(f"Taking off to {takeoff_alt}m...")
            controller.takeoff_drone(2, takeoff_alt)
            time.sleep(5)  # Wait for takeoff to complete
            
            # 4. Fly to each waypoint
            for i, waypoint in enumerate(points, 1):
                lat = waypoint['lat']
                lon = waypoint['lon']
                alt = waypoint['alt']
                
                self.log.append(f"Flying to waypoint {i}/{len(points)}:")
                self.log.append(f"  Latitude: {lat:.6f}")
                self.log.append(f"  Longitude: {lon:.6f}")
                self.log.append(f"  Altitude: {alt}m")
                self.refresh_text()
                
                # Fly to the waypoint
                controller.goto_location(2, lat, lon, alt)
                
                # Optional: Wait a bit between waypoints (adjust as needed)
                if i < len(points):
                    time.sleep(20)
            
            self.log.append("✅ Mission completed successfully!")
            self.refresh_text()
            
        except Exception as e:
            error_msg = f"❌ Mission execution failed: {str(e)}"
            self.log.append(error_msg)
            print(error_msg)
            self.refresh_text()

    def refresh_text(self):
        self.messages.setText("\n".join(self.log))
        self.messages.verticalScrollBar().setValue(
            self.messages.verticalScrollBar().maximum()
        )

    def load_paths(self):
        try:
            default_path = DATA_DIR / "normalized_paths.xlsx"

            if not default_path.exists():
                QMessageBox.warning(self, "File Missing", "normalized_paths.xlsx not found in data/")
                return

            df = pd.read_excel(default_path)
            self.stored_paths = df
            self.log.append("✓ Loaded normalized_paths.xlsx from data/")
            self.refresh_text()

            self.draw_existing_paths()

        except Exception as e:
            self.log.append(f"❌ Error loading paths: {e}")
            self.refresh_text()

    def draw_existing_paths(self):
        if self.stored_paths is None: 
            return

        try:
            grouped = self.stored_paths.groupby("drone_id")

            for i, (drone_id, df) in enumerate(grouped):
                df = df.sort_values("timestamp")
                path = []
                for _, row in df.iterrows():
                    path.append({
                        "lat": row["lat"],
                        "lon": row["lon"],
                        "alt": row["alt"],
                        "time": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                js = f"drawPath({json.dumps(path)}, '{self.color(i)}', '{drone_id}', false);"
                self.map_view.page().runJavaScript(js)
            
            self.log.append(f"✓ Drew {len(grouped)} existing drone paths with waypoint labels")
            self.refresh_text()
        except Exception as e:
            self.log.append(f"❌ Error drawing paths: {str(e)}")
            self.refresh_text()

    def draw_new_path(self):
        """Draw the new path with all its waypoints"""
        if not self.new_path:
            return
        
        try:
            # Clear only new path visualization, not existing drone paths
            self.map_view.page().runJavaScript("clearNewPathWaypoints();")
            
            # Format new path data
            path = []
            for wp in sorted(self.new_path, key=lambda x: x['timestamp']):
                path.append({
                    "lat": wp["lat"],
                    "lon": wp["lon"],
                    "alt": wp["alt"],
                    "time": wp["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                })
            
            js = f"drawPath({json.dumps(path)}, 'red', 'New Path', true);"
            self.map_view.page().runJavaScript(js)
            
        except Exception as e:
            self.log.append(f"❌ Error drawing new path: {str(e)}")
            self.refresh_text()

    def color(self, i):
        colors = ["blue","green","purple","orange","brown","pink","cyan","magenta"]
        return colors[i % len(colors)]

    def reset_new(self):
        self.new_path = []
        self.log.append("🗑️ New path cleared")
        self.refresh_text()
        # Clear only new path markers, not existing drone paths
        self.map_view.page().runJavaScript("clearNewPathWaypoints();")
        self.map_view.page().runJavaScript("clearCollisions();")

    def analyze_paths(self):
        try:
            # Basic validation
            if not self.new_path:
                self.log.append("❌ No new path to analyze! Click on map to add waypoints.")
                self.refresh_text()
                return

            if self.stored_paths is None:
                self.log.append("❌ Load existing paths first!")
                self.refresh_text()
                return

            if len(self.new_path) < 2:
                self.log.append("❌ Need at least 2 waypoints for analysis!")
                self.refresh_text()
                return

            # Clear previous results
            self.map_view.page().runJavaScript("clearCollisions();")
            self.log.append("🔍 Starting collision analysis...")
            self.log.append("=" * 60)
            self.refresh_text()

            # Run centralized deconfliction
            new_df = pd.DataFrame(self.new_path).sort_values("timestamp")

            alerts = detect_conflicts(
                new_path=new_df,
                existing_paths=self.stored_paths
            )

            # Visualize conflicts on map
            for a in alerts:
                collision_data = {
                    "lat": a["lat"],
                    "lon": a["lon"],
                    "alt": a["alt"],
                    "drone_id": a["drone_id"],
                    "time": a["time"].strftime("%Y-%m-%d %H:%M:%S"),
                    "distance": f"{a['distance']:.1f}"
                }

                self.map_view.page().runJavaScript(
                    f"markCollision({json.dumps(collision_data)});"
                )

            # Explain results
            messages = explain_conflicts(alerts)
            for msg in messages:
                self.log.append(msg)

            self.path_is_safe = len(alerts) == 0
            self.refresh_text()

        except Exception as e:
            self.log.append(f"❌ Error during analysis: {str(e)}")
            import traceback
            self.log.append(traceback.format_exc())
            self.refresh_text()


    def add_path_from_text(self):
            """Parse and add waypoints from text input"""
            try:
                text = self.text_input.toPlainText().strip()
                if not text:
                    self.log.append("❌ No text input provided!")
                    self.refresh_text()
                    return
                
                lines = text.split('\n')
                added_count = 0
                
                for line_num, line in enumerate(lines, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):  # Skip empty lines and comments
                        continue
                    
                    try:
                        # Parse the tuple format
                        # Remove parentheses and split by comma
                        line = line.strip('()')
                        parts = [p.strip().strip("'\"") for p in line.split(',')]
                        
                        if len(parts) != 4:
                            self.log.append(f"⚠️ Line {line_num}: Expected 4 values (lat, lon, alt, time), got {len(parts)}")
                            continue
                        
                        lat = float(parts[0])
                        lon = float(parts[1])
                        alt = float(parts[2])
                        t = pd.to_datetime(parts[3])
                        
                        if pd.isna(t):
                            self.log.append(f"⚠️ Line {line_num}: Invalid timestamp")
                            continue
                        
                        wp = {"lat": lat, "lon": lon, "alt": alt, "timestamp": t}
                        self.new_path.append(wp)
                        added_count += 1
                        
                    except ValueError as e:
                        self.log.append(f"⚠️ Line {line_num}: Parse error - {str(e)}")
                        continue
                
                if added_count > 0:
                    self.log.append(f"✓ Added {added_count} waypoint(s) from text input")
                    self.draw_new_path()
                    self.text_input.clear()  # Clear the input after successful addition
                else:
                    self.log.append("❌ No valid waypoints found in text input")
                
                self.refresh_text()
                
            except Exception as e:
                self.log.append(f"❌ Error parsing text input: {str(e)}")
                self.refresh_text()

    def closeEvent(self, event):
        event.accept()

    


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())