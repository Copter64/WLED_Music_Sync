"""
LED Light Show Controller with Music Synchronization

Copyright (c) 2025 Copter64
SPDX-License-Identifier: MIT

This module provides synchronized music playback with WLED light control.
"""

__version__ = "1.0.0"

from .controller import WLEDController
from .gui import MusicPlayer
from .scheduler import SceneScheduler
from .config import load_timings_from_yaml, find_song_file
from .config_loader import load_controller_config

__all__ = [
    'WLEDController',
    'MusicPlayer',
    'SceneScheduler',
    'load_timings_from_yaml',
    'find_song_file',
    'load_controller_config',
]
