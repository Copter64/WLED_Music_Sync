#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example script showing how to use the timecode sync module with WLED.
"""
import asyncio
import logging
from halloween_leds.timecode_sync import TimecodeSync, TimecodeConfig
from halloween_leds.music_sync import WLEDController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Example timecode source - in practice, this would come from your 
    # external timecode source (e.g., audio interface, video system, etc.)
    def mock_timecode_source():
        # This is just an example - replace with your actual timecode source
        return "01:00:00:00"  # Example: 1 hour into the timeline
    
    # Initialize the timecode sync with your timing configuration
    config = TimecodeConfig(
        framerate=24,  # Set to match your timecode source
        drop_frame=False,
        start_tc="00:00:00:00"
    )
    
    # Create the timecode sync instance from your existing YAML file
    tc_sync = TimecodeSync.from_yaml_file("timings.yml", config)
    
    # Initialize your WLED controllers (using the existing configuration)
    controllers = {
        "mainscene": WLEDController("http://your-wled-ip"),
        # Add other controllers as needed
    }
    
    # Define what happens when an event is triggered
    def handle_event(event):
        for controller_id, scene in event.controllers.items():
            if controller_id in controllers:
                asyncio.create_task(
                    controllers[controller_id].apply_scene(scene.scene)
                )
    
    # Set up the event handler
    tc_sync.set_callback(handle_event)
    
    try:
        # Start monitoring the timecode source
        await tc_sync.start_monitoring(mock_timecode_source)
    except KeyboardInterrupt:
        tc_sync.stop_monitoring()

if __name__ == "__main__":
    asyncio.run(main())
