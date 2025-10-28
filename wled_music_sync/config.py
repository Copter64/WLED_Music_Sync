"""Configuration loading module."""
import logging
import os
from typing import Dict, List

import yaml

from .models import ControllerScene, TimedEvent

LOGGER = logging.getLogger(__name__)

def find_song_file(song_name: str, yaml_dir: str) -> str:
    """Find the full path to a song file."""
    return os.path.join(yaml_dir, "songs", song_name)

def load_timings_from_yaml(path: str) -> Dict[str, List[TimedEvent]]:
    """
    Updated YAML format:

    songs:
      spooky-song.mp3:
        - time: 0.0
          controllers:
            trunk_master:
              preset: 1
            derpy_blade:
              scene:
                on: true
                fx: 85
        - time: 10.0
          controllers:
            trunk_master:
              preset_name: "PurpleFade"
            derpy_blade:
              scene:
                on: false
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if "songs" not in data:
        raise ValueError("Missing 'songs' key")

    def _parse_controller_entry(ctrl_key: str, scene_def: Dict) -> List[ControllerScene]:
        """Handle both individual controllers and controller groups"""
        # Handle group definition
        if ctrl_key == "group" and isinstance(scene_def, dict):
            if "controllers" not in scene_def:
                LOGGER.warning("Group definition missing 'controllers' list")
                return []
                
            controllers = scene_def["controllers"]
            if not isinstance(controllers, list):
                LOGGER.warning("Group 'controllers' must be a list")
                return []
                
            # Create a scene definition without the controllers list
            scene = scene_def.copy()
            del scene["controllers"]
            
            # Create a scene for each controller
            return [ControllerScene(controller_id=ctrl_id, scene=scene.copy()) 
                   for ctrl_id in controllers]
        
        # Handle regular single controller
        if isinstance(scene_def, dict) and "scene" in scene_def:
            scene = scene_def["scene"]
        else:
            scene = scene_def
        return [ControllerScene(controller_id=ctrl_key, scene=scene)]

    songs: Dict[str, List[TimedEvent]] = {}
    for song, events in data["songs"].items():
        timed_list: List[TimedEvent] = []
        for ev in events:
            time_s = float(ev.get("time", 0))
            ctrl_map = ev.get("controllers", {})
            controller_scenes: List[ControllerScene] = []
            
            # Process each controller or controller group
            for ctrl_key, scene_def in ctrl_map.items():
                try:
                    scenes = _parse_controller_entry(ctrl_key, scene_def)
                    controller_scenes.extend(scenes)
                except Exception as e:
                    LOGGER.warning(f"Error processing controller entry {ctrl_key}: {e}")
                    continue
                    
            timed_list.append(TimedEvent(time_s=time_s, controller_scenes=controller_scenes))
        songs[song] = sorted(timed_list)
    return songs
