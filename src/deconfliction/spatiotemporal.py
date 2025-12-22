import numpy as np
import pandas as pd
from typing import List, Dict

SAFETY_DISTANCE_METERS = 12  # configurable


def detect_conflicts(
    new_path: pd.DataFrame,
    existing_paths: pd.DataFrame,
    safety_distance: float = SAFETY_DISTANCE_METERS
) -> List[Dict]:
    """
    Detect spatiotemporal (4D) conflicts between a new path
    and existing drone trajectories.

    Returns a list of conflict dictionaries.
    """

    alerts = []

    new_path = new_path.sort_values("timestamp")
    grouped = existing_paths.groupby("drone_id")

    for drone_id, df in grouped:
        df = df.sort_values("timestamp")

        if len(df) < 2:
            continue

        # --- time window overlap check ---
        if (
            new_path.timestamp.iloc[-1] < df.timestamp.iloc[0]
            or new_path.timestamp.iloc[0] > df.timestamp.iloc[-1]
        ):
            continue

        for i in range(len(new_path) - 1):
            n1, n2 = new_path.iloc[i], new_path.iloc[i + 1]

            for j in range(len(df) - 1):
                o1, o2 = df.iloc[j], df.iloc[j + 1]

                t_start = max(n1.timestamp, o1.timestamp)
                t_end = min(n2.timestamp, o2.timestamp)

                if t_start >= t_end:
                    continue

                # sample time overlap
                try:
                    ts = pd.date_range(t_start, t_end, periods=4)
                except ValueError:
                    continue

                for t in ts:
                    dt_new = (n2.timestamp - n1.timestamp).total_seconds()
                    dt_old = (o2.timestamp - o1.timestamp).total_seconds()

                    if dt_new == 0 or dt_old == 0:
                        continue

                    un = (t - n1.timestamp).total_seconds() / dt_new
                    uo = (t - o1.timestamp).total_seconds() / dt_old

                    Pn = np.array([
                        n1.lat + un * (n2.lat - n1.lat),
                        n1.lon + un * (n2.lon - n1.lon),
                        n1.alt + un * (n2.alt - n1.alt)
                    ])

                    Po = np.array([
                        o1.lat + uo * (o2.lat - o1.lat),
                        o1.lon + uo * (o2.lon - o1.lon),
                        o1.alt + uo * (o2.alt - o1.alt)
                    ])

                    # lat/lon → meters (approx)
                    horizontal_m = np.linalg.norm(Pn[:2] - Po[:2]) * 111000
                    vertical_m = abs(Pn[2] - Po[2])
                    distance_m = np.sqrt(horizontal_m**2 + vertical_m**2)

                    if distance_m < safety_distance:
                        alerts.append({
                            "drone_id": drone_id,
                            "time": t,
                            "lat": float(Pn[0]),
                            "lon": float(Pn[1]),
                            "alt": float(Pn[2]),
                            "distance": float(distance_m),
                        })

    return alerts
