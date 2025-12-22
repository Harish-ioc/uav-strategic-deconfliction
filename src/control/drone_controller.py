from pymavlink import mavutil
import time
import threading

class SimpleDroneController:
    def __init__(self):
        self.connection = None
        self.detected_drones = []
        self.attitude_heading = {}  # Live data storage
        self.monitoring_active = False

    def connect_to_drones(self, com_port, baud_rate=57600, timeout=5):
        """Connect and detect all available drones"""
        try:
            print(f"Connecting to {com_port}...")
            # self.connection = mavutil.mavlink_connection(com_port, baud=int(baud_rate))
            self.connection = mavutil.mavlink_connection('udp:172.19.144.1:14550')  # SIM connection parameters

            print("Detecting drones...")
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                msg = self.connection.recv_match(type='HEARTBEAT', blocking=False)
                if msg:
                    system_id = msg.get_srcSystem()
                    if system_id not in self.detected_drones:
                        self.detected_drones.append(system_id)
                        print(f"Found drone with System ID: {system_id}")
                
                time.sleep(0.1)
            
            if len(self.detected_drones) == 0:
                print("No drones detected!")
            else:
                print(f"Total drones found: {len(self.detected_drones)}")
                print(f"Drone IDs: {self.detected_drones}")
            
            return self.detected_drones
            
        except Exception as e:
            print(f"Connection failed: {e}")
            return []

    def start_attitude_monitoring(self, update_interval=0.1):
        """Start continuous attitude monitoring in background thread"""
        if self.monitoring_active:
            print("Attitude monitoring already running!")
            return
        
        self.monitoring_active = True
        print("Starting background attitude monitoring...")
        
        def monitor_loop():
            while self.monitoring_active:
                try:
                    # Clear buffer to get fresh data
                    while self.connection.recv_match(type='GLOBAL_POSITION_INT', blocking=False):
                        pass
                    
                    # Small delay to let fresh data arrive
                    time.sleep(0.05)
                    
                    # Get fresh GLOBAL_POSITION_INT messages
                    msg = self.connection.recv_match(type='GLOBAL_POSITION_INT', blocking=False)
                    if msg:
                        system_id = msg.get_srcSystem()
                        if system_id in self.detected_drones:
                            if system_id not in self.attitude_heading:
                                self.attitude_heading[system_id] = {}
                            
                            self.attitude_heading[system_id].update({
                                'heading': msg.hdg / 100,
                                'latitude': msg.lat / 1e7,
                                'longitude': msg.lon / 1e7,
                                'altitude': msg.relative_alt / 1000.0,  # Use relative altitude (AGL)
                                'timestamp': time.time()
                            })
                            print(f"Drone {system_id} - Lat: {msg.lat/1e7:.6f}, Lng: {msg.lon/1e7:.6f}, Alt: {msg.relative_alt/1000.0:.1f}m")
                    
                    time.sleep(update_interval)
                    
                except Exception as e:
                    print(f"Error in attitude monitoring: {e}")
                    time.sleep(0.5)
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        print("✓ Background attitude monitoring started!")

    def get_live_drone_attitude(self, system_id):
        """Get the latest attitude data for a specific drone"""
        if system_id not in self.attitude_heading:
            return None
        
        data = self.attitude_heading[system_id].copy()
        data.pop('timestamp', None)
        return data

    def get_all_live_drone_attitudes(self):
        """Get live attitude data for all detected drones"""
        attitudes = {}
        
        for drone_id in self.detected_drones:
            attitude_data = self.get_live_drone_attitude(drone_id)
            if attitude_data:
                attitudes[drone_id] = attitude_data
        
        return attitudes

    def arm_drone(self, system_id):
        """Arm a specific drone"""
        try:
            print(f"Arming drone {system_id}...")
            
            self.connection.mav.command_long_send(
                system_id,  # target_system
                1,          # target_component
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,  # command
                0,          # confirmation
                1,          # param1 (1 to arm, 0 to disarm)
                0, 0, 0, 0, 0, 0  # param2-7 (unused)
            )
            
            print(f"✓ Arm command sent to drone {system_id}")
            return True
            
        except Exception as e:
            print(f"✗ Error sending arm command to drone {system_id}: {e}")
            return False

    def disarm_drone(self, system_id):
        """Disarm a specific drone"""
        try:
            print(f"Disarming drone {system_id}...")
            
            self.connection.mav.command_long_send(
                system_id,  # target_system
                1,          # target_component
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,  # command
                0,          # confirmation
                0,          # param1 (1 to arm, 0 to disarm)
                0, 0, 0, 0, 0, 0  # param2-7 (unused)
            )
            
            print(f"✓ Disarm command sent to drone {system_id}")
            return True
            
        except Exception as e:
            print(f"✗ Error sending disarm command to drone {system_id}: {e}")
            return False

    def arm_all_drones(self):
        """Arm all detected drones"""
        print("\n=== Arming All Drones ===")
        success_count = 0
        
        for drone_id in self.detected_drones:
            if self.arm_drone(drone_id):
                success_count += 1
            time.sleep(0.1)
        
        print(f"Arming complete: {success_count}/{len(self.detected_drones)} drones armed")
        return success_count == len(self.detected_drones)

    def disarm_all_drones(self):
        """Disarm all detected drones"""
        print("\n=== Disarming All Drones ===")
        success_count = 0
        
        for drone_id in self.detected_drones:
            if self.disarm_drone(drone_id):
                success_count += 1
            time.sleep(0.1)
        
        print(f"Disarming complete: {success_count}/{len(self.detected_drones)} drones disarmed")
        return success_count == len(self.detected_drones)

    def set_drone_mode(self, system_id, mode_name):
        """Set flight mode for a specific drone"""
        try:
            flight_modes = {
                "STABILIZE": 0, "ACRO": 1, "ALTHLD": 2, "AUTO": 3, "GUIDED": 4,
                "LOITER": 5, "RTL": 6, "CIRCLE": 7, "POSITION": 8, "LAND": 9,
                "OF_LOITER": 10, "DRIFT": 11, "SPORT": 13, "FLIP": 14, "AUTOTUNE": 15,
                "POSHOLD": 16, "BRAKE": 17, "THROW": 18, "AVOID_ADSB": 19, "GUIDED_NOGPS": 20,
                "SMART_RTL": 21, "FLOWHOLD": 22, "FOLLOW": 23, "ZIGZAG": 24
            }
            
            mode_name_upper = mode_name.upper()
            if mode_name_upper not in flight_modes:
                print(f"✗ Unknown mode: {mode_name}")
                return False
            
            mode_number = flight_modes[mode_name_upper]
            print(f"Setting drone {system_id} to {mode_name} mode...")
            
            self.connection.mav.set_mode_send(
                system_id,  # target_system
                mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,  # base_mode
                mode_number  # custom_mode
            )
            
            print(f"✓ Mode change command sent for {system_id}")
            return True
            
        except Exception as e:
            print(f"✗ Error setting mode for drone {system_id}: {e}")
            return False

    def set_all_drone_modes(self, mode_name):
        """Set the same flight mode for all detected drones"""
        print(f"\n=== Setting All Drones to {mode_name} Mode ===")
        success_count = 0
        
        for drone_id in self.detected_drones:
            if self.set_drone_mode(drone_id, mode_name):
                success_count += 1
            time.sleep(0.1)
        
        print(f"Mode change complete: {success_count}/{len(self.detected_drones)} drones changed to {mode_name}")
        return success_count == len(self.detected_drones)

    def takeoff_drone(self, system_id, altitude_meters):
        """Takeoff a specific drone to specified altitude"""
        try:
            print(f"Initiating takeoff for drone {system_id} to {altitude_meters}m...")
            
            self.connection.mav.command_long_send(
                system_id,  # target_system
                1,          # target_component
                mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,  # command
                0,          # confirmation
                0,          # param1 (minimum pitch)
                0,          # param2 (empty)
                0,          # param3 (empty)
                0,          # param4 (yaw angle)
                0,          # param5 (latitude)
                0,          # param6 (longitude)
                altitude_meters  # param7 (altitude)
            )
            
            print(f"✓ Takeoff command sent to drone {system_id}")
            return True
                
        except Exception as e:
            print(f"✗ Error taking off drone {system_id}: {e}")
            return False

    def takeoff_all_drones(self, altitude_meters):
        """Takeoff all detected drones to specified altitude"""
        print(f"\n=== Taking Off All Drones to {altitude_meters}m ===")
        success_count = 0
        
        for drone_id in self.detected_drones:
            if self.takeoff_drone(drone_id, altitude_meters):
                success_count += 1
            time.sleep(0.1)
        
        print(f"Takeoff complete: {success_count}/{len(self.detected_drones)} drones took off")
        return success_count == len(self.detected_drones)

    def goto_location(self, system_id, latitude, longitude, altitude_meters):
        """Send drone to specific location"""
        try:
            print(f"Sending drone {system_id} to location: {latitude}, {longitude} at {altitude_meters}m...")
            
            lat_int = int(latitude * 10000000)
            lon_int = int(longitude * 10000000)
            
            self.connection.mav.set_position_target_global_int_send(
                0,  # time_boot_ms
                system_id,  # target_system
                1,  # target_component
                mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # coordinate_frame
                0b0000111111111000,  # type_mask (ignore velocities, accelerations, yaw)
                lat_int=lat_int,
                lon_int=lon_int,
                alt=altitude_meters,  # Altitude in meters
                vx=0, vy=0, vz=0,
                afx=0, afy=0, afz=0, 
                yaw=0,
                yaw_rate=0
            )
            
            print(f"✓ Drone {system_id} position target sent!")
            return True
            
        except Exception as e:
            print(f"✗ Error sending drone {system_id} to location: {e}")
            return False