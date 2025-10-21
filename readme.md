⚙️ Usage Examples
🧩 Upload a single preset (temporary)
```
python wled_preset_uploader.py --ip 192.168.1.186 --file preset1.json
```
💾 Upload a single preset and save it
```
python wled_preset_uploader.py --ip 192.168.1.186 --file preset1.json --save
```
📦 Bulk upload all presets in a folder
```
python wled_preset_uploader.py --ip 192.168.1.12 --dir ./presets
```
💾 Bulk upload and save each preset in sequential slots
```
python wled_preset_uploader.py --ip 192.168.1.12 --dir ./presets --save
```



## Installation

### Method 1: Install from Source
1. Clone this repository:
   ```
   git clone <your-repo-url>
   cd HalloweenLEDs
   ```

2. Install with pip:
   ```
   pip install -e .
   ```

3. Create a `.env` file with your WLED controller IPs:
   ```
   WLED_CONTROLLERS=sword1=http://192.168.1.186,mainscene=http://192.168.1.187
   ```

### Method 2: Download Executable
1. Download the latest release from the releases page
2. Extract the zip file
3. Create a `.env` file as described above
4. Run the executable

## Running the Application

To run the music sync app:
```
music-sync --timings timings.yml
```

Or if using the executable:
```
halloween-leds --timings timings.yml
```

## SMPTE Timecode Support

The application now includes support for SMPTE timecode synchronization, allowing you to sync your WLED effects with external timecode sources such as video systems, audio workstations, or show control systems.

### Using Timecode Sync

1. Install the additional dependency:
   ```
   pip install timecode
   ```

2. Configure your timecode settings in your application:
   ```python
   from halloween_leds.timecode_sync import TimecodeSync, TimecodeConfig

   config = TimecodeConfig(
       framerate=24,  # Set to match your timecode source (24, 25, 29.97, 30)
       drop_frame=False,
       start_tc="00:00:00:00"
   )
   ```

3. Initialize the timecode sync with your existing timing file:
   ```python
   tc_sync = TimecodeSync.from_yaml_file("timings.yml", config)
   ```

### Example Usage

Check out `examples/timecode_example.py` for a complete example of how to:
- Set up timecode synchronization
- Connect to WLED controllers
- Handle timecode-triggered events

### Features
- Support for various framerates (24, 25, 29.97, 30 fps)
- Drop-frame and non-drop-frame timecode
- Configurable starting timecode
- Asynchronous timecode monitoring
- Compatible with existing YAML timing files
- Seamless integration with current WLED control system

### Common Timecode Sources
- Audio interfaces with LTC input
- Video systems
- Show control software
- Network timecode (NTP)