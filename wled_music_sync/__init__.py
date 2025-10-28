"""WLED Music Sync package."""
import logging

from .config import find_song_file, load_timings_from_yaml
from .controller import WLEDController
from .gui import MusicPlayer
from .models import ControllerScene, TimedEvent
from .scheduler import SceneScheduler
from .config_loader import load_controller_config, ControllerConfig

__all__ = [
    'WLEDController',
    'MusicPlayer',
    'SceneScheduler',
    'ControllerScene',
    'TimedEvent',
    'load_timings_from_yaml',
    'find_song_file',
    'load_controller_config',
    'ControllerConfig',
]

# Set up root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
