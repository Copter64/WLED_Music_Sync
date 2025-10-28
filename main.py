#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WLED Music Sync - Synchronized LED light shows with music playback
Copyright (c) 2025 Copter64
SPDX-License-Identifier: MIT

This is the main entry point for the WLED Music Sync application.
"""
import argparse
import asyncio
import logging
import os
import tkinter as tk
from tkinter import filedialog

import pygame
from wled_music_sync import (
    WLEDController,
    MusicPlayer,
    SceneScheduler,
    load_timings_from_yaml,
    find_song_file,
    load_controller_config,
)

LOGGER = logging.getLogger("music_wled_player")

def select_timing_file() -> str:
    """Show a file dialog to select the timing configuration file."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    timing_file = filedialog.askopenfilename(
        title="Select Timing Configuration File",
        filetypes=[("YAML files", "*.yml *.yaml"), ("All files", "*.*")],
        initialdir=os.getcwd()
    )
    return timing_file if timing_file else None

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Music + WLED show controller.")
    p.add_argument("--song", required=False, help="Song name or number (optional, will prompt if not provided)")
    p.add_argument("--timings", required=False, help="Path to YAML timing configuration (optional, will prompt if not provided)")
    p.add_argument("--dry-run", action="store_true", help="Print actions without sending to WLED")
    args = p.parse_args()
    
    # If timings file not specified, show file dialog
    if not args.timings:
        LOGGER.info("No timing file specified, opening file selector...")
        timing_file = select_timing_file()
        if not timing_file:
            LOGGER.error("No timing file selected. Exiting.")
            raise SystemExit(1)
        args.timings = timing_file
    
    return args

async def main_async(args: argparse.Namespace) -> None:
    # Load timings
    LOGGER.info("Loading timings from %s", args.timings)
    if not os.path.exists(args.timings):
        LOGGER.error("Timing file not found: %s", args.timings)
        raise SystemExit(1)
        
    timing_map = load_timings_from_yaml(args.timings)
    LOGGER.info("Found %d songs in timing map", len(timing_map))
    yaml_dir = os.path.dirname(os.path.abspath(args.timings))
    LOGGER.info("Base directory: %s", yaml_dir)
    
    # Initialize controllers
    LOGGER.info("Loading controller configuration")
    controller_configs = load_controller_config()
    
    controllers = {}
    for controller_id, config in controller_configs.items():
        controllers[controller_id] = [
            WLEDController(controller_id, url.strip())
            for url in config.urls
        ]
        LOGGER.info(f"Initialized {controller_id} ({config.description}) with {len(config.urls)} URLs")
    LOGGER.info("Loaded controllers: %s", list(controllers.keys()))

    # Initialize the player and scheduler
    player = MusicPlayer()
    player.set_available_songs(timing_map.keys())
    scheduler = SceneScheduler(controllers, dry_run=args.dry_run)
    
    try:
        while True:  # Main program loop
            if player._in_song_select:
                # Handle song selection mode
                result = player.handle_events()
                if result is False:  # Quit requested
                    LOGGER.info("Quit requested from song selection")
                    break
                elif isinstance(result, str):  # Song selected
                    song_key = result
                    song_path = find_song_file(song_key, yaml_dir)
                    
                    if os.path.isfile(song_path):
                        LOGGER.info("Starting playback of %s", song_key)
                        player._in_song_select = False
                        player._song_finished = False
                        events = timing_map[song_key]
                        loop = asyncio.get_running_loop()
                        await loop.run_in_executor(None, player.play, song_path)
                        current_event_index = 0
                        last_time = None
                    else:
                        LOGGER.error("Song file not found: %s", song_path)
            else:
                # Handle playback mode
                result = player.handle_events()
                if result is False:  # Quit requested
                    LOGGER.info("Quit requested during playback")
                    break
                elif result is None:  # Song finished
                    LOGGER.info("Song finished")
                    player._in_song_select = True  # Return to song selection
                    continue

                # Process events during playback
                current_time = player.playback_elapsed()
                if current_time is None:
                    continue

                # Only process events if time has moved forward
                if last_time is None or current_time > last_time:
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
            
            await asyncio.sleep(0.05)  # Prevent CPU overuse

    finally:
        try:
            # First stop playback
            if player:
                player.stop()
            
            # Then close all network connections
            if scheduler:
                await scheduler.close()
            
            # Finally quit pygame
            pygame.quit()
        except Exception as e:
            LOGGER.error("Error during cleanup: %s", e)

def main() -> None:
    try:
        asyncio.run(main_async(parse_args()))
    except KeyboardInterrupt:
        LOGGER.info("Interrupted.")

if __name__ == "__main__":
    main()
