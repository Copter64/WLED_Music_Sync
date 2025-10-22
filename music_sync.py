#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
music_wled_player.py

Play music and drive multiple WLED controllers using YAML-based timed scenes.

New Features (v2):
 - Each WLED controller can have its own scene per timestamp.
 - Supports WLED preset recalls via {"preset": <num>} or {"preset_name": "<name>"}.
 - Retains dry-run, .env, and YAML mapping logic.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aiohttp
import pygame
import yaml

# region Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
LOGGER = logging.getLogger("music_wled_player")
# Timeouts in seconds
WLED_HTTP_TIMEOUT = 0.5  # Total timeout for any HTTP request
WLED_CONNECT_TIMEOUT = 0.2  # Timeout for establishing connection
WLED_READ_TIMEOUT = 0.3  # Timeout for reading response
# endregion

# region Data Models
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
# endregion

# region WLED Controller
class WLEDController:
    """
    Talks to a single WLED instance via its JSON API.

    Supports both state scenes and preset recall.
    """
    def __init__(self, controller_id: str, base_url: str):
        self.id = controller_id
        self.base_url = base_url.rstrip("/")
        self._internal_session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._internal_session is None:
            # Use more specific timeouts to prevent hanging
            timeout = aiohttp.ClientTimeout(
                total=WLED_HTTP_TIMEOUT,
                connect=WLED_CONNECT_TIMEOUT,
                sock_read=WLED_READ_TIMEOUT
            )
            connector = aiohttp.TCPConnector(
                force_close=True,  # Don't keep connections alive
                enable_cleanup_closed=True  # Clean up closed connections
            )
            self._internal_session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )
        return self._internal_session

    async def apply_scene(self, scene: Dict[str, Any], dry_run: bool = False) -> bool:
        """
        Apply a scene or preset to this WLED controller via /json endpoint.
        
        Args:
            scene: Scene definition dictionary:
                - {"preset": <num>} for preset recall by number
                - {"preset_name": "<name>"} for preset recall by name
                - Any other keys will be sent directly as state
            dry_run: If True, log but don't send commands
            
        Returns:
            bool: True if successful, False on error
        """
        # Determine endpoint and payload
        if "preset" in scene:
            # Match the working approach from wled_preset_uploader.py
            url = f"{self.base_url}/json"
            payload = {"ps": scene["preset"], "on": True}  # ensure lights are on when recalling preset
        elif "preset_name" in scene:
            # preset_name requires lookup from WLED's /presets (optional)
            return await self._apply_preset_by_name(scene["preset_name"], dry_run)
        else:
            url = f"{self.base_url}/json"
            payload = scene

        if dry_run:
            LOGGER.info("[DRY RUN] %s would POST %s -> %s", self.id, json.dumps(payload), url)
            return True

        session = await self._get_session()
        try:
            async with session.post(url, json=payload) as resp:
                text = await resp.text()
                if 200 <= resp.status < 300:
                    LOGGER.debug("WLED %s response: %s", self.id, text)
                    return True
                LOGGER.warning("WLED %s HTTP %s: %s", self.id, resp.status, text)
                return False
        except Exception as exc:  # pragma: no cover - network
            LOGGER.warning("Error posting to %s: %s", self.id, exc)
            return False

    async def _apply_preset_by_name(self, name: str, dry_run: bool) -> bool:
        """Lookup preset by name and apply if found."""
        if dry_run:
            LOGGER.info("[DRY RUN] %s would recall preset_name=%s", self.id, name)
            return True
        session = await self._get_session()
        try:
            async with session.get(f"{self.base_url}/presets") as resp:
                data = await resp.json(content_type=None)
                match = next((pid for pid, val in data.items() if val.get("n") == name), None)
                if not match:
                    LOGGER.warning("Preset '%s' not found on %s", name, self.id)
                    return False
            # recall by id using the same approach as wled_preset_uploader.py
            url = f"{self.base_url}/json"
            payload = {"ps": int(match), "on": True}
            if dry_run:
                LOGGER.info("[DRY RUN] %s would POST %s -> %s", self.id, json.dumps(payload), url)
                return True
            session = await self._get_session()
            async with session.post(url, json=payload) as resp:
                text = await resp.text()
                if 200 <= resp.status < 300:
                    LOGGER.debug("WLED %s response: %s", self.id, text)
                    return True
                LOGGER.warning("WLED %s HTTP %s: %s", self.id, resp.status, text)
                return False
        except Exception as exc:
            LOGGER.warning("Error looking up preset_name '%s' on %s: %s", name, self.id, exc)
            return False

    async def close(self) -> None:
        if self._internal_session:
            await self._internal_session.close()
            self._internal_session = None
# endregion

# region Music Player
class MusicPlayer:
    """Lightweight pygame-based player with keyboard controls."""
    def __init__(self):
        pygame.mixer.init()
        pygame.init()  # Initialize pygame for event handling
        
        # Create a larger control window
        self._window = pygame.display.set_mode((800, 400))
        pygame.display.set_caption("Music Controls")
        
        # Initialize fonts for display
        self._font = pygame.font.Font(None, 48)  # Larger main font
        self._small_font = pygame.font.Font(None, 36)  # Smaller font for status
        
        self._start_time = None
        self._paused = False
        self._current_pos = 0.0
        self._file_path = None
        self._volume = 1.0
        self._song_finished = False
        pygame.mixer.music.set_volume(self._volume)
        
        # Set up the end of song event
        pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
        
        # Draw initial controls
        self._draw_controls()

    def play(self, file_path: str) -> None:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)
        self._file_path = file_path
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        self._start_time = time.perf_counter()
        self._paused = False
        LOGGER.info("Started music: %s", file_path)

    def stop(self) -> None:
        pygame.mixer.music.stop()
        self._start_time = None
        self._paused = False

    def is_playing(self) -> bool:
        return pygame.mixer.music.get_busy() or self._paused

    def playback_elapsed(self) -> Optional[float]:
        if not self._start_time:
            return None
        if self._paused:
            return self._current_pos
        return time.perf_counter() - self._start_time

    def _draw_controls(self):
        """Draw the control interface"""
        self._window.fill((0, 0, 0))  # Black background
        
        # Draw controls text
        controls = [
            "SPACE: Play/Pause",
            "LEFT/RIGHT: Seek ±5s",
            "PGUP/PGDN: Seek ±30s",
            "UP/DOWN: Volume",
            "R: Restart",
            "Q: Quit"
        ]
        
        # Draw title
        title = self._font.render("Music Controls", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=self._window.get_width() // 2, y=20)
        self._window.blit(title, title_rect)
        
        # Draw controls in two columns
        y = 100
        col_width = self._window.get_width() // 2
        for i, text in enumerate(controls):
            surface = self._font.render(text, True, (255, 255, 255))
            if i < len(controls) // 2:
                x = 40
            else:
                x = col_width + 40
                y = 100 + (i - len(controls) // 2) * 60
            self._window.blit(surface, (x, y))
            if i < len(controls) // 2:
                y += 60
        
        # Draw status bar at bottom
        if self._start_time is not None:
            # Status bar background
            pygame.draw.rect(self._window, (40, 40, 40), (20, 320, 760, 60))
            
            # Current time
            time_text = f"Time: {self.playback_elapsed():.1f}s"
            time_surface = self._font.render(time_text, True, (0, 255, 0))
            self._window.blit(time_surface, (30, 330))
            
            # Volume
            vol_text = f"Volume: {int(self._volume * 100)}%"
            vol_surface = self._font.render(vol_text, True, (0, 255, 0))
            vol_rect = vol_surface.get_rect(midright=(780, 350))
            self._window.blit(vol_surface, vol_rect)
            
            # Playback status
            if self._song_finished:
                status = "FINISHED - Press 'R' to replay or 'Q' to quit"
                status_surface = self._font.render(status, True, (0, 255, 0))
            else:
                status = "PAUSED" if self._paused else "PLAYING"
                status_surface = self._font.render(status, True, (255, 165, 0))
            status_rect = status_surface.get_rect(center=(self._window.get_width() // 2, 350))
            self._window.blit(status_surface, status_rect)
        
        pygame.display.flip()

    def handle_events(self) -> bool:
        """Handle keyboard events. Returns False if should quit, None if song finished."""
        for event in pygame.event.get():
            if event.type == pygame.USEREVENT + 1:  # End of song
                self._song_finished = True
                return None
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # Play/Pause
                    if self._paused:
                        pygame.mixer.music.unpause()
                        self._start_time = time.perf_counter() - self._current_pos
                        self._paused = False
                        LOGGER.info("Resumed at %.2fs", self._current_pos)
                    else:
                        pygame.mixer.music.pause()
                        self._current_pos = time.perf_counter() - self._start_time
                        self._paused = True
                        LOGGER.info("Paused at %.2fs", self._current_pos)
                
                elif event.key == pygame.K_LEFT:  # Rewind 5 seconds
                    current = self.playback_elapsed() or 0
                    new_pos = max(0, current - 5)
                    self._current_pos = new_pos
                    pygame.mixer.music.rewind()
                    pygame.mixer.music.play(start=new_pos)
                    self._start_time = time.perf_counter() - new_pos
                    LOGGER.info("Seeking to %.2fs", new_pos)
                
                elif event.key == pygame.K_RIGHT:  # Forward 5 seconds
                    current = self.playback_elapsed() or 0
                    new_pos = current + 5
                    self._current_pos = new_pos
                    pygame.mixer.music.rewind()
                    pygame.mixer.music.play(start=new_pos)
                    self._start_time = time.perf_counter() - new_pos
                    LOGGER.info("Seeking to %.2fs", new_pos)
                
                elif event.key == pygame.K_r:  # Restart
                    pygame.mixer.music.play()
                    self._start_time = time.perf_counter()
                    self._paused = False
                    LOGGER.info("Restarted playback")
                
                elif event.key == pygame.K_UP:  # Volume up
                    self._volume = min(1.0, self._volume + 0.1)
                    pygame.mixer.music.set_volume(self._volume)
                    LOGGER.info("Volume: %.1f", self._volume)
                
                elif event.key == pygame.K_DOWN:  # Volume down
                    self._volume = max(0.0, self._volume - 0.1)
                    pygame.mixer.music.set_volume(self._volume)
                    LOGGER.info("Volume: %.1f", self._volume)
                
                elif event.key == pygame.K_PAGEUP:  # Forward 30 seconds
                    current = self.playback_elapsed() or 0
                    new_pos = current + 30
                    self._current_pos = new_pos
                    pygame.mixer.music.rewind()
                    pygame.mixer.music.play(start=new_pos)
                    self._start_time = time.perf_counter() - new_pos
                    LOGGER.info("Seeking to %.2fs", new_pos)

                elif event.key == pygame.K_PAGEDOWN:  # Rewind 30 seconds
                    current = self.playback_elapsed() or 0
                    new_pos = max(0, current - 30)
                    self._current_pos = new_pos
                    pygame.mixer.music.rewind()
                    pygame.mixer.music.play(start=new_pos)
                    self._start_time = time.perf_counter() - new_pos
                    LOGGER.info("Seeking to %.2fs", new_pos)

                elif event.key == pygame.K_q:  # Quit
                    return False
            
            elif event.type == pygame.QUIT:
                return False

        # Update display
        self._draw_controls()
        return True
# endregion

# region Scene Scheduler
class SceneScheduler:
    """Schedules events and dispatches controller scenes."""
    def __init__(self, controllers: Dict[str, List[WLEDController]], dry_run: bool = False):
        self.controllers = controllers
        self.dry_run = dry_run

    async def run_schedule(self, events: List[TimedEvent], music_player: Optional[MusicPlayer] = None) -> None:
        if not events:
            LOGGER.warning("No events to schedule.")
            return

        events.sort()
        reference = time.perf_counter() - (music_player.playback_elapsed() or 0)
        for event in events:
            sleep_for = reference + event.time_s - time.perf_counter()
            if sleep_for > 0:
                await asyncio.sleep(sleep_for)
            await self._dispatch_event(event)

    async def _dispatch_event(self, event: TimedEvent) -> None:
        dispatch_start = time.perf_counter()
        LOGGER.info("Dispatching event @%.2fs", event.time_s)
        
        # Prepare all requests in parallel
        tasks = []
        for cscene in event.controller_scenes:
            controllers = self.controllers.get(cscene.controller_id, [])
            if not controllers:
                LOGGER.warning("Controller %s not defined", cscene.controller_id)
                continue
                
            # Create tasks for all instances of this controller
            for ctrl in controllers:
                task = asyncio.create_task(
                    ctrl.apply_scene(cscene.scene, dry_run=self.dry_run)
                )
                tasks.append((f"{cscene.controller_id}_{ctrl.base_url}", task))
        
        # Wait for all tasks with a timeout
        if tasks:
            # Use wait instead of gather to handle timeouts better
            done, pending = await asyncio.wait(
                [t for _, t in tasks],
                timeout=WLED_HTTP_TIMEOUT
            )
            
            # Cancel any pending tasks that didn't complete in time
            for pending_task in pending:
                pending_task.cancel()
            
            # Log results
            total_time = time.perf_counter() - dispatch_start
            success_count = len(done)
            timeout_count = len(pending)
            
            if timeout_count:
                LOGGER.warning(
                    "Event @%.2fs: %d/%d controllers responded (%.3fs), %d timed out",
                    event.time_s, success_count, len(tasks), total_time, timeout_count
                )
            else:
                LOGGER.debug(
                    "Event @%.2fs: All %d controllers responded in %.3fs",
                    event.time_s, len(tasks), total_time
                )

    async def close(self) -> None:
        for c in self.controllers.values():
            await c.close()
# endregion

# region YAML loader
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

    def _parse_controller_entry(ctrl_key: str, scene_def: Dict[str, Any]) -> List[ControllerScene]:
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
# endregion

# region CLI and main
def find_song_file(timing_map: Dict[str, List[TimedEvent]], song_hint: str, yaml_dir: str) -> str:
    """Find the full path to a song file based on a partial name match."""
    if not song_hint:
        print("\nAvailable songs:")
        for idx, song in enumerate(timing_map.keys(), 1):
            print(f"{idx}. {song}")
        choice = input("\nSelect song number or enter name: ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(timing_map):
                song_hint = list(timing_map.keys())[idx-1]
        except ValueError:
            song_hint = choice

    # Try exact match first
    for song_name in timing_map.keys():
        if song_hint.lower() == song_name.lower():
            return os.path.join(yaml_dir, "KPopDH", song_name)
        
    # Try partial match
    matches = [s for s in timing_map.keys() 
              if song_hint.lower() in s.lower()]
    
    if not matches:
        raise ValueError(f"No song matching '{song_hint}' found in timing configuration")
    elif len(matches) > 1:
        print("\nMultiple matches found:")
        for idx, song in enumerate(matches, 1):
            print(f"{idx}. {song}")
        choice = input("\nSelect song number: ").strip()
        try:
            idx = int(choice)
            if 1 <= idx <= len(matches):
                return os.path.join(yaml_dir, "KPopDH", matches[idx-1])
        except ValueError:
            pass
        raise ValueError("Invalid selection")
    
    return os.path.join(yaml_dir, "KPopDH", matches[0])

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Music + WLED show controller.")
    p.add_argument("--song", required=False, help="Song name or number (optional, will prompt if not provided)")
    p.add_argument("--timings", required=True, help="Path to YAML timing configuration")
    p.add_argument("--dry-run", action="store_true", help="Print actions without sending to WLED")
    return p.parse_args()

async def main_async(args: argparse.Namespace) -> None:
    # Load timings
    timing_map = load_timings_from_yaml(args.timings)
    yaml_dir = os.path.dirname(os.path.abspath(args.timings))
    
    # Find and validate song
    song_path = find_song_file(timing_map, args.song or "", yaml_dir)
    song_key = os.path.basename(song_path)
    if song_key not in timing_map:
        raise ValueError(f"No timing data found for '{song_key}'")
    
    events = timing_map[song_key]
    LOGGER.info("Playing %s with %d events", song_key, len(events))
    
    # Load controllers from YAML configuration
    from halloween_leds.controller_config import load_controller_config
    controller_configs = load_controller_config()
    
    # Initialize controllers
    controllers: Dict[str, List[WLEDController]] = {}
    # Create controller instances for each URL
    for controller_id, config in controller_configs.items():
        controllers[controller_id] = [
            WLEDController(controller_id, url.strip())
            for url in config.urls
        ]
        LOGGER.info(f"Initialized {controller_id} ({config.description}) with {len(config.urls)} URLs")
    LOGGER.info("Loaded controllers: %s", list(controllers.keys()))

    player = MusicPlayer()
    scheduler = SceneScheduler(controllers, dry_run=args.dry_run)

    try:
        if os.path.isfile(song_path):
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, player.play, song_path)
        else:
            LOGGER.error("Song file not found: %s (expected in %s)", song_key, yaml_dir)
            return
        current_event_index = 0
        last_time = None

        while True:
            result = player.handle_events()  # Handle keyboard controls
            if result is False:  # Quit requested
                LOGGER.info("Quit requested")
                break
            elif result is None:  # Song finished
                LOGGER.info("Song finished")
                # Keep window open but stop processing events
                while True:
                    result = player.handle_events()
                    if result is False:  # Quit requested
                        break
                    pygame.display.flip()
                    await asyncio.sleep(0.05)
                break

            current_time = player.playback_elapsed()
            if current_time is None:
                continue

            # Only process events if time has moved forward
            if last_time is None or current_time > last_time:
                # Process any events that should have happened by now
                while (current_event_index < len(events) and 
                       events[current_event_index].time_s <= current_time):
                    await scheduler._dispatch_event(events[current_event_index])
                    current_event_index += 1
            
            # If we went backwards, find the new position in events
            elif current_time < last_time:
                current_event_index = 0
                while (current_event_index < len(events) and 
                       events[current_event_index].time_s <= current_time):
                    current_event_index += 1

            last_time = current_time
            await asyncio.sleep(0.05)  # More responsive control checks
    finally:
        await scheduler.close()
        player.stop()
        pygame.quit()

def main() -> None:
    try:
        asyncio.run(main_async(parse_args()))
    except KeyboardInterrupt:
        LOGGER.info("Interrupted.")
# endregion

if __name__ == "__main__":
    main()
