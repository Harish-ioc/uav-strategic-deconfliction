import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (needed for 3D)

# Resolve project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

INPUT_EXCEL = DATA_DIR / "simulated_paths.xlsx"
OUTPUT_EXCEL = DATA_DIR / "normalized_paths.xlsx"

# Normalize paths
def normalize_paths(input_excel: Path, output_excel: Path):
    df = pd.read_excel(input_excel)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    lat_min, lat_max = df["lat"].min(), df["lat"].max()
    lon_min, lon_max = df["lon"].min(), df["lon"].max()
    alt_min, alt_max = df["alt"].min(), df["alt"].max()
    t_min, t_max = df["timestamp"].min(), df["timestamp"].max()

    df["x_norm"] = (df["lon"] - lon_min) / (lon_max - lon_min)
    df["y_norm"] = (df["lat"] - lat_min) / (lat_max - lat_min)
    df["z_norm"] = (df["alt"] - alt_min) / (alt_max - alt_min)
    df["t_norm"] = (
        (df["timestamp"] - t_min).dt.total_seconds()
        / (t_max - t_min).total_seconds()
    )

    df.to_excel(output_excel, index=False)
    print(f"✓ Normalized dataset saved to {output_excel}")

# 3D Visualization (XYZ)
def plot_normalized_3d(normalized_excel: Path):
    df = pd.read_excel(normalized_excel)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")

    for drone_id, g in df.groupby("drone_id"):
        ax.plot(
            g["x_norm"],
            g["y_norm"],
            g["z_norm"],
            marker="o",
            label=drone_id
        )

    ax.set_title("Normalized Drone Paths (3D Space)")
    ax.set_xlabel("X (normalized longitude)")
    ax.set_ylabel("Y (normalized latitude)")
    ax.set_zlabel("Altitude (normalized)")
    ax.legend()

    plt.show()

# Script entry point (optional)
if __name__ == "__main__":
    if not INPUT_EXCEL.exists():
        raise FileNotFoundError(f"{INPUT_EXCEL} not found")

    normalize_paths(INPUT_EXCEL, OUTPUT_EXCEL)
    plot_normalized_3d(OUTPUT_EXCEL)
