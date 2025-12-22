import random
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Resolve project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Bounding coordinates (operational area)
a = (18.571347469474013, 73.76757961632767)
b = (18.572087788390924, 73.77660917773662)
c = (18.561547389915898, 73.76748613083969)
d = (18.562079732297835, 73.77751174762237)

lat_min = min(a[0], b[0], c[0], d[0])
lat_max = max(a[0], b[0], c[0], d[0])
lon_min = min(a[1], b[1], c[1], d[1])
lon_max = max(a[1], b[1], c[1], d[1])

ALT_MIN = 20
ALT_MAX = 60

# Waypoint generation helpers
def random_wp(t):
    return (
        random.uniform(lat_min, lat_max),
        random.uniform(lon_min, lon_max),
        random.uniform(ALT_MIN, ALT_MAX),
        t
    )

def generate_path(path_id: str, ref_start_time: datetime):
    # choose random number of waypoints (2–4)
    n_points = random.randint(2, 4)

    mission_start = ref_start_time + timedelta(seconds=random.randint(0, 7200))
    duration_sec = random.randint(60, 1200)
    dt_step = duration_sec // (n_points - 1)

    t = mission_start
    wps = []

    # --- start at altitude 10 ---
    lat_start = random.choice([lat_min, lat_max])
    lon_start = random.uniform(lon_min, lon_max)
    wps.append((lat_start, lon_start, 10, t))

    # --- middle points ---
    for _ in range(n_points - 2):
        t += timedelta(seconds=dt_step)
        wps.append(random_wp(t))

    # --- end at altitude 10 ---
    t += timedelta(seconds=dt_step)
    lat_end = random.choice([lat_min, lat_max])
    lon_end = random.uniform(lon_min, lon_max)
    wps.append((lat_end, lon_end, 10, t))

    return [(path_id, wp[0], wp[1], wp[2], wp[3]) for wp in wps]

# Dataset generator
def generate_simulated_paths(num_paths: int = 20):
    reference_now = datetime.now()
    rows = []

    for i in range(num_paths):
        path = generate_path(
            path_id=f"drone_{i+1}",
            ref_start_time=reference_now
        )
        rows.extend(path)

    df = pd.DataFrame(
        rows,
        columns=["drone_id", "lat", "lon", "alt", "timestamp"]
    )

    output_file = DATA_DIR / "simulated_paths.xlsx"
    df.to_excel(output_file, index=False)

    print(f"✓ Generated {output_file} ({num_paths} paths)")
    return output_file

# Script entry point
if __name__ == "__main__":
    generate_simulated_paths(num_paths=20)
