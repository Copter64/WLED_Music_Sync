#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
timecode_sync.py

SMPTE Timecode synchronization module for WLED control.
Allows the system to sync WLED effects with external timecode sources.
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Callable, Any
import timecode
from .music_sync import TimedEvent, ControllerScene

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
LOGGER = logging.getLogger("timecode_sync")

@dataclass
class TimecodeConfig:
    """Configuration for timecode synchronization."""
    framerate: int = 24  # Standard film framerate
    drop_frame: bool = False
    start_tc: str = "00:00:00:00"  # Default starting timecode

class TimecodeSync:
    """
    Handles SMPTE timecode synchronization for WLED control.
    Can receive timecode and trigger events based on the current timecode position.
    """
    def __init__(self, events: Dict[float, TimedEvent], config: Optional[TimecodeConfig] = None):
        self.events = events
        self.config = config or TimecodeConfig()
        self.current_tc = timecode.Timecode(self.config.framerate, self.config.start_tc)
        self._running = False
        self._callback: Optional[Callable[[TimedEvent], None]] = None
        self._last_event_time = 0.0
        
    def set_callback(self, callback: Callable[[TimedEvent], None]) -> None:
        """Set the callback to be called when an event should be triggered."""
        self._callback = callback

    def timecode_to_seconds(self, tc: timecode.Timecode) -> float:
        """Convert a timecode object to seconds."""
        return float(tc.frames) / float(tc.framerate)

    def update_timecode(self, tc_str: str) -> None:
        """
        Update the current timecode and trigger any events that should occur.
        
        Args:
            tc_str: SMPTE timecode string in format "HH:MM:SS:FF"
        """
        try:
            new_tc = timecode.Timecode(self.config.framerate, tc_str)
            current_seconds = self.timecode_to_seconds(new_tc)
            
            # Find and trigger any events that should occur
            for event_time, event in self.events.items():
                if self._last_event_time <= event_time <= current_seconds:
                    if self._callback:
                        self._callback(event)
            
            self._last_event_time = current_seconds
            self.current_tc = new_tc
            
        except ValueError as e:
            LOGGER.error(f"Invalid timecode format: {tc_str}")
            raise ValueError(f"Invalid timecode format: {tc_str}") from e

    async def start_monitoring(self, timecode_source: Callable[[], str]) -> None:
        """
        Start monitoring a timecode source asynchronously.
        
        Args:
            timecode_source: Callable that returns the current timecode as a string
        """
        self._running = True
        while self._running:
            try:
                tc_str = timecode_source()
                self.update_timecode(tc_str)
                await asyncio.sleep(1/self.config.framerate)  # Sleep for one frame duration
            except Exception as e:
                LOGGER.error(f"Error monitoring timecode: {e}")
                await asyncio.sleep(1)  # Sleep longer on error

    def stop_monitoring(self) -> None:
        """Stop monitoring the timecode source."""
        self._running = False

    @classmethod
    def from_yaml_file(cls, yaml_path: str, config: Optional[TimecodeConfig] = None) -> 'TimecodeSync':
        """
        Create a TimecodeSync instance from a YAML file containing timing events.
        
        Args:
            yaml_path: Path to the YAML file containing timing events
            config: Optional TimecodeConfig instance
            
        Returns:
            TimecodeSync instance configured with the events from the YAML file
        """
        import yaml
        
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Convert the YAML data into a dictionary of TimedEvents
        events = {}
        for song_data in data.get('songs', {}).values():
            for event in song_data:
                time = float(event['time'])
                controllers = {}
                
                for controller_id, scene in event.get('controllers', {}).items():
                    if isinstance(scene, dict):
                        controllers[controller_id] = ControllerScene(
                            controller_id=controller_id,
                            scene=scene
                        )
                
                events[time] = TimedEvent(
                    time=time,
                    controllers=controllers
                )
        
        return cls(events, config)
