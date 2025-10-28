# WLED Music Sync Timing Configuration Guide

This guide explains how to create and configure timing files for the WLED Music Sync application.

## File Structure

The timing configuration consists of two parts:
1. The main `timings.yml` file that maps songs to their events
2. Individual timing files (optional) in the `songs` directory

## Main Timings File (timings.yml)

### Basic Structure
```yaml
songs:
  "song-file.mp3":  # Must match the filename in songs directory
    - time: 0.0     # Time in seconds
      controllers:   # Controller actions
        controller1: # Controller ID from controllers.yml
          preset: 1  # Action to take
```

### Minimum Required Configuration
```yaml
songs:
  "song1.mp3":
    - time: 0.0
      controllers:
        main_controller:
          preset: 1
```

### Full Configuration Example
```yaml
songs:
  "halloween_theme.mp3":
    - time: 0.0  # Start of song
      controllers:
        porch_lights:
          preset: 1  # Use preset 1
        garden_lights:
          scene:     # Use custom scene
            on: true
            bri: 255
            fx: 85
            speed: 200
            intensity: 150
            palette: 1
    
    - time: 5.5  # 5.5 seconds into song
      controllers:
        porch_lights:
          scene:
            on: true
            bri: 128  # 50% brightness
            fx: 73    # Custom effect
        garden_lights:
          preset: 5   # Switch to preset 5
    
    # Multiple controllers can change at the same time
    - time: 10.0
      controllers:
        porch_lights:
          scene:
            on: false  # Turn off
        garden_lights:
          scene:
            on: true
            fx: 0      # Solid color
            col:       # RGB colors
              - 255    # Red
              - 0      # Green
              - 0      # Blue

  "another_song.mp3":
    - time: 0.0
      controllers:
        all_lights:
          preset: 1
```

## Controller Groups

Groups allow you to control multiple controllers with the same settings. Groups are defined inline within the timing events.

### Using Groups in timings.yml
```yaml
songs:
  "song.mp3":
    - time: 0.0
      controllers:
        group:  # Special 'group' keyword for grouping controllers
          controllers: [controller1, controller2, controller3]  # List of controllers to affect
          preset: 1  # The preset to apply to all controllers in the group
    
    - time: 5.0
      controllers:
        group:
          controllers: [controller1, controller2]  # Can use different combinations
          scene:  # Can use scenes instead of presets
            on: true
            bri: 255
        controller3:  # Can still control individual controllers separately
          preset: 2

    - time: 10.0
      controllers:
        group:
          controllers: [controller1, controller2, controller3]
          preset: 5  # All controllers will switch to preset 5
```

### Group Properties
- `controllers`: Array of controller IDs that will be affected
- Can use either `preset` or `scene` like with individual controllers
- All controllers in the group will receive the same settings

You can use groups anywhere you would normally specify a controller, and they support all the same operations (presets and scenes).

## Scene Properties

### Basic Properties
- `on`: boolean - Turn the lights on/off
- `bri`: number (0-255) - Master brightness
- `preset`: number - Use a saved preset

### Advanced Scene Properties
```yaml
scene:
  on: true                # Required - true/false
  bri: 255               # Optional - Brightness (0-255)
  fx: 85                 # Optional - Effect index
  speed: 128             # Optional - Effect speed (0-255)
  intensity: 128         # Optional - Effect intensity (0-255)
  palette: 1             # Optional - Color palette index
  seg:                   # Optional - Segment configuration
    - id: 0             # Segment ID
      col:              # Array of RGB colors
        - [255, 0, 0]   # Primary color (RGB)
        - [0, 255, 0]   # Secondary color (RGB)
        - [0, 0, 255]   # Tertiary color (RGB)
      fx: 85            # Effect for this segment
      bri: 255          # Brightness for this segment
```

### Color Formats
```yaml
scene:
  # Single color (RGB)
  col:
    - 255  # Red
    - 0    # Green
    - 0    # Blue

  # Multiple colors for effects
  col:
    - [255, 0, 0]    # Primary (Red)
    - [0, 255, 0]    # Secondary (Green)
    - [0, 0, 255]    # Tertiary (Blue)
```

## Timing Events

### Time Specification
- Times are in seconds
- Can use decimal points for precise timing
- Must be in ascending order
- Example time points:
  ```yaml
  - time: 0.0    # Start of song
  - time: 1.5    # 1.5 seconds
  - time: 10.0   # 10 seconds
  - time: 60.5   # 1 minute and 0.5 seconds
  ```

### Controller Actions
1. Using Presets:
   ```yaml
   controller_id:
     preset: 1  # Use preset number 1
   ```

2. Using Scenes:
   ```yaml
   controller_id:
     scene:
       on: true
       bri: 255
       fx: 85
   ```

3. Multiple Controllers:
   ```yaml
   controllers:
     controller1:
       preset: 1
     controller2:
       scene:
         on: true
         bri: 255
     controller3:
       scene:
         on: false
   ```

## Best Practices

1. **Time Organization**
   - Keep times in ascending order
   - Use comments to mark significant points
   - Group related changes together

2. **Performance**
   - Avoid unnecessary scene changes
   - Use presets when possible (they're faster)
   - Group controller changes at the same timestamp

3. **Maintenance**
   - Use comments to document effects and sections
   - Keep a consistent format
   - Test with --dry-run before running live

## Common Patterns

### Using Groups for Synchronized Effects
```yaml
# Example of coordinated light show using groups
- time: 0.0  # Start with everything off
  controllers:
    group:
      controllers: [left1, left2, left3, right1, right2, right3]
      scene:
        on: false

- time: 1.0  # Light up left side
  controllers:
    group:
      controllers: [left1, left2, left3]
      preset: 1
    
- time: 2.0  # Light up right side
  controllers:
    group:
      controllers: [right1, right2, right3]
      preset: 1

- time: 3.0  # Synchronize all lights
  controllers:
    group:
      controllers: [left1, left2, left3, right1, right2, right3]
      preset: 2
```

### Fade In/Out Example
```yaml
- time: 0.0  # Fade in
  controllers:
    main:
      scene:
        on: true
        bri: 0
        fx: 0  # Solid color effect
- time: 0.5
  controllers:
    main:
      scene:
        bri: 64  # 25%
- time: 1.0
  controllers:
    main:
      scene:
        bri: 128  # 50%
- time: 1.5
  controllers:
    main:
      scene:
        bri: 255  # 100%
```

### Chase Effect Example
```yaml
- time: 0.0  # Start chase
  controllers:
    section1:
      preset: 1
- time: 0.25
  controllers:
    section2:
      preset: 1
    section1:
      preset: 2
- time: 0.5
  controllers:
    section3:
      preset: 1
    section2:
      preset: 2
    section1:
      preset: 3
```

## Troubleshooting

### Common Issues
1. Events not triggering:
   - Check time values are in seconds
   - Verify controller IDs match controllers.yml
   - Ensure presets exist on the WLED device

2. Wrong effects:
   - Verify effect numbers match your WLED version
   - Check segment IDs are correct
   - Validate color values are in range (0-255)

3. Timing problems:
   - Ensure times are in ascending order
   - Check for duplicate time entries
   - Verify decimal point usage
