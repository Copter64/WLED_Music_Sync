"""Data models for WLED Music Sync."""
from dataclasses import dataclass
from typing import Any, Dict, List

@dataclass
class ControllerScene:
    """Scene or preset definition for a specific controller."""
    controller_id: str
    scene: Dict[str, Any]

@dataclass
class TimedEvent:
    """Single timepoint event containing per-controller scenes."""
    time_s: float
    controller_scenes: List[ControllerScene]

    def __lt__(self, other: "TimedEvent") -> bool:
        return self.time_s < other.time_s
