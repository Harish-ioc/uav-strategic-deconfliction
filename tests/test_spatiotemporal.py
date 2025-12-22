import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.deconfliction.spatiotemporal import detect_conflicts

def make_df(points, drone_id):
    """
    Helper to convert (lat, lon, alt, time_str) → DataFrame
    """
    return pd.DataFrame([
        {
            "drone_id": drone_id,
            "lat": p[0],
            "lon": p[1],
            "alt": p[2],
            "timestamp": pd.to_datetime(p[3])
        }
        for p in points
    ])

# TEST 1 
def test_exact_same_position_same_time():
    """
    Two drones at exact same position at same time SHOULD conflict
    """
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.57209, 73.76876, 10, '2025-12-23 05:05:00'),
    ]
    existing_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.57209, 73.76876, 10, '2025-12-23 05:05:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) > 0, "Expected conflicts for exact same position/time"

# TEST 2 
def test_close_proximity_horizontal():
    """
    Drones within 12m horizontally at same time and altitude SHOULD conflict
    """
    # 10m apart horizontally (approximately 0.00009 degrees at equator)
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.57209, 73.76876, 10, '2025-12-23 05:05:00'),
    ]
    existing_points = [
        (18.57218, 73.76876, 10, '2025-12-23 05:00:00'),  # ~10m north
        (18.57218, 73.76876, 10, '2025-12-23 05:05:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) > 0, "Expected conflicts for close horizontal proximity (<12m)"

# TEST 3 
def test_safe_horizontal_distance():
    """
    Drones >12m apart horizontally SHOULD NOT conflict
    """
    # 50m apart horizontally (approximately 0.00045 degrees)
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.57209, 73.76876, 10, '2025-12-23 05:05:00'),
    ]
    existing_points = [
        (18.57654, 73.76876, 10, '2025-12-23 05:00:00'),  # ~50m north
        (18.57654, 73.76876, 10, '2025-12-23 05:05:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) == 0, "Expected no conflicts for safe horizontal distance (>12m)"

# TEST 4 
def test_vertical_separation():
    """
    Drones at same lat/lon but >12m vertical separation SHOULD NOT conflict
    """
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.57209, 73.76876, 10, '2025-12-23 05:05:00'),
    ]
    existing_points = [
        (18.57209, 73.76876, 30, '2025-12-23 05:00:00'),  # 20m altitude difference
        (18.57209, 73.76876, 30, '2025-12-23 05:05:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) == 0, "Expected no conflicts with sufficient vertical separation"

# TEST 5 
def test_close_vertical_separation():
    """
    Drones at same lat/lon with <12m vertical separation SHOULD conflict
    """
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.57209, 73.76876, 10, '2025-12-23 05:05:00'),
    ]
    existing_points = [
        (18.57209, 73.76876, 18, '2025-12-23 05:00:00'),  # 8m altitude difference
        (18.57209, 73.76876, 18, '2025-12-23 05:05:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) > 0, "Expected conflicts with insufficient vertical separation (<12m)"

# TEST 6 
def test_crossing_paths_different_times():
    """
    Paths that cross spatially but at different times SHOULD NOT conflict
    """
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.56155, 73.77294, 10, '2025-12-23 05:10:00'),
    ]
    existing_points = [
        (18.57205, 73.76880, 10, '2025-12-23 06:00:00'),  # 1 hour later
        (18.56158, 73.77290, 10, '2025-12-23 06:10:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) == 0, "Expected no conflicts for paths crossing at different times"

# TEST 7 
def test_crossing_paths_overlapping_times():
    """
    Paths that cross spatially with overlapping times SHOULD conflict
    """
    # Paths that intersect around the midpoint at overlapping times
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.56155, 73.77294, 10, '2025-12-23 05:10:00'),
    ]
    existing_points = [
        (18.56155, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.57209, 73.77294, 10, '2025-12-23 05:10:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) > 0, "Expected conflicts for crossing paths at overlapping times"

# TEST 8 
def test_parallel_paths_safe_distance():
    """
    Parallel paths with safe separation SHOULD NOT conflict
    """
    # Two parallel paths 50m apart
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.56155, 73.76876, 10, '2025-12-23 05:10:00'),
    ]
    existing_points = [
        (18.57209, 73.77326, 10, '2025-12-23 05:00:00'),  # ~50m east
        (18.56155, 73.77326, 10, '2025-12-23 05:10:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) == 0, "Expected no conflicts for parallel paths with safe distance"

# TEST 9 
def test_parallel_paths_close_proximity():
    """
    Parallel paths too close together SHOULD conflict
    """
    # Two parallel paths 8m apart
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.56155, 73.76876, 10, '2025-12-23 05:10:00'),
    ]
    existing_points = [
        (18.57216, 73.76876, 10, '2025-12-23 05:00:00'),  # ~8m north
        (18.56162, 73.76876, 10, '2025-12-23 05:10:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) > 0, "Expected conflicts for parallel paths too close (<12m)"

# TEST 10 
def test_head_on_collision():
    """
    Two drones flying directly at each other SHOULD conflict
    """
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.56155, 73.76876, 10, '2025-12-23 05:10:00'),
    ]
    existing_points = [
        (18.56155, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.57209, 73.76876, 10, '2025-12-23 05:10:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) > 0, "Expected conflicts for head-on collision course"

# TEST 11 
def test_overtaking_scenario_same_altitude():
    """
    One drone overtaking another at same altitude SHOULD conflict
    """
    # Faster drone catching up with slower drone
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.56155, 73.76876, 10, '2025-12-23 05:05:00'),  # Fast
    ]
    existing_points = [
        (18.57000, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.56155, 73.76876, 10, '2025-12-23 05:10:00'),  # Slow
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) > 0, "Expected conflicts for overtaking at same altitude"

# TEST 12 
def test_overtaking_different_altitudes():
    """
    One drone overtaking another at different altitudes SHOULD NOT conflict
    """
    # Faster drone at higher altitude
    new_path_points = [
        (18.57209, 73.76876, 30, '2025-12-23 05:00:00'),  # Higher altitude
        (18.56155, 73.76876, 30, '2025-12-23 05:05:00'),
    ]
    existing_points = [
        (18.57000, 73.76876, 10, '2025-12-23 05:00:00'),  # Lower altitude
        (18.56155, 73.76876, 10, '2025-12-23 05:10:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) == 0, "Expected no conflicts for overtaking at different altitudes"

# TEST 13 
def test_multi_segment_path_with_conflict():
    """
    Multi-waypoint path with conflict in middle segment SHOULD detect
    """
    new_path_points = [
        (18.57500, 73.76500, 10, '2025-12-23 05:00:00'),
        (18.57209, 73.76876, 10, '2025-12-23 05:05:00'),  # Conflict here
        (18.56800, 73.77200, 10, '2025-12-23 05:10:00'),
        (18.56400, 73.77500, 10, '2025-12-23 05:15:00'),
    ]
    existing_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:04:00'),
        (18.57209, 73.76876, 10, '2025-12-23 05:06:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) > 0, "Expected conflicts in middle segment of multi-waypoint path"

# TEST 14 
def test_empty_path_no_conflict():
    """
    Empty existing paths SHOULD NOT cause conflicts
    """
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.56155, 73.77294, 10, '2025-12-23 05:10:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = pd.DataFrame(columns=["drone_id", "lat", "lon", "alt", "timestamp"])
    alerts = detect_conflicts(new_df, existing_df)
    assert len(alerts) == 0, "Expected no conflicts with empty existing paths"

# TEST 15 
def test_3d_distance_boundary_case():
    """
    Test exact boundary case: distance exactly at 12m threshold
    """
    # Calculate position that's exactly 12m away in 3D space
    # Using 8.5m horizontal + 8.5m vertical = ~12.02m total
    new_path_points = [
        (18.57209, 73.76876, 10, '2025-12-23 05:00:00'),
        (18.57209, 73.76876, 10, '2025-12-23 05:05:00'),
    ]
    existing_points = [
        (18.57216, 73.76876, 18.5, '2025-12-23 05:00:00'),  # ~8.5m north, 8.5m up
        (18.57216, 73.76876, 18.5, '2025-12-23 05:05:00'),
    ]
    new_df = make_df(new_path_points, "new_drone")
    existing_df = make_df(existing_points, "drone_A")
    alerts = detect_conflicts(new_df, existing_df)
    # At exactly 12m, it should not conflict (threshold is <12m)
    assert len(alerts) == 0, "Expected no conflicts at exactly 12m distance"


# RUN ALL TESTS
if __name__ == "__main__":
    tests = [
        test_exact_same_position_same_time,
        test_close_proximity_horizontal,
        test_safe_horizontal_distance,
        test_vertical_separation,
        test_close_vertical_separation,
        test_crossing_paths_different_times,
        test_crossing_paths_overlapping_times,
        test_parallel_paths_safe_distance,
        test_parallel_paths_close_proximity,
        test_head_on_collision,
        test_overtaking_scenario_same_altitude,
        test_overtaking_different_altitudes,
        test_multi_segment_path_with_conflict,
        test_empty_path_no_conflict,
        test_3d_distance_boundary_case,
    ]
    
    print("=" * 60)
    print("Running Spatiotemporal Conflict Detection Tests")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"⚠️  {test.__name__}: Unexpected error - {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the conflict detection logic.")