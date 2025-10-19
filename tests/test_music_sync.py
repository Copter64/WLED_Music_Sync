"""Basic tests for music_sync functionality"""
import pytest
from halloween_leds.music_sync import load_timings_from_yaml, ControllerScene, TimedEvent

def test_load_timings(sample_timings):
    """Test loading timings from YAML"""
    timings = load_timings_from_yaml(sample_timings)
    assert "test.mp3" in timings
    events = timings["test.mp3"]
    assert len(events) == 1
    
    event = events[0]
    assert isinstance(event, TimedEvent)
    assert event.time_s == 0.0
    assert len(event.controller_scenes) == 2  # Two controllers from group
    
    # Check controller scenes
    controllers = {cs.controller_id: cs.scene for cs in event.controller_scenes}
    assert "sword1" in controllers
    assert "sword2" in controllers
    assert controllers["sword1"]["preset"] == 1
    assert controllers["sword2"]["preset"] == 1
