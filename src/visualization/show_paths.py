import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from pathlib import Path

# Resolve project root and data directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

EXCEL_PATH = DATA_DIR / "normalized_paths.xlsx"

if not EXCEL_PATH.exists():
    raise FileNotFoundError(f"{EXCEL_PATH} not found")

# Load data
df = pd.read_excel(EXCEL_PATH)

# group paths per drone
groups = df.groupby("drone_id")

# Plot
plt.figure(figsize=(10, 8))
ax = plt.axes(projection=ccrs.PlateCarree())

ax.add_feature(cfeature.LAND)
ax.add_feature(cfeature.OCEAN)
ax.add_feature(cfeature.BORDERS, linewidth=0.4)
ax.add_feature(cfeature.LAKES, alpha=0.3)
ax.add_feature(cfeature.RIVERS, alpha=0.3)

for drone_id, g in groups:
    ax.plot(
        g["lon"],
        g["lat"],
        marker="o",
        linewidth=2,
        label=drone_id
    )

ax.set_title("Simulated Drone Flight Paths")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.legend()

plt.show()
