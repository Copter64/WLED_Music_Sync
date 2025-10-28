#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main entry point for WLED Music Sync application.
"""
import argparse
import asyncio
import logging
import os

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

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Music + WLED show controller.")
    p.add_argument("--song", required=False, help="Song name or number (optional, will prompt if not provided)")
    p.add_argument("--timings", required=True, help="Path to YAML timing configuration")
    p.add_argument("--dry-run", action="store_true", help="Print actions without sending to WLED")
    return p.parse_args()

async def main_async(args: argparse.Namespace) -> None:
    # Load timings
    LOGGER.info("Loading timings from %s", args.timings)
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
