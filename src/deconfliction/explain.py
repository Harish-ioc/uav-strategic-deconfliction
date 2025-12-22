from collections import defaultdict
from typing import List, Dict


def explain_conflicts(alerts: List[Dict]) -> List[str]:
    """
    Convert conflict alerts into human-readable messages.
    """
    messages = []

    if not alerts:
        messages.append("✅ PATH SAFE - No collision risks detected")
        return messages

    messages.append(f"⚠️ COLLISION RISK DETECTED: {len(alerts)} conflict(s)")
    messages.append("-" * 60)

    grouped = defaultdict(list)
    for a in alerts:
        grouped[a["drone_id"]].append(a)

    for drone_id, conflicts in grouped.items():
        messages.append(f" Conflicts with {drone_id}:")

        for c in conflicts:
            messages.append(
                f"  ├─ Time: {c['time'].strftime('%Y-%m-%d %H:%M:%S')}"
            )
            messages.append(
                f"  ├─ Position: ({c['lat']:.6f}, {c['lon']:.6f})"
            )
            messages.append(
                f"  ├─ Altitude: {c['alt']:.1f} m"
            )
            messages.append(
                f"  └─ Distance: {c['distance']:.1f} m"
            )
            messages.append("")

    return messages
