# WLED Music Sync Controller

A music synchronization application for WLED light controllers, featuring an easy-to-use GUI for music playback while coordinating light shows with WLED-enabled devices.

## Features

- 🎵 Interactive GUI for music selection and playback
- 🎨 WLED controller integration with preset and scene support
- ⚡ Real-time synchronization of music and light events
- 🎮 Simple keyboard and mouse controls
- 📊 Detailed logging and error recovery
- 🔄 Automatic resource management

## Quick Start (Windows Users)

### Prerequisites
- Windows PC
- WLED-enabled device(s) on your network
- Microsoft Visual C++ Redistributable (latest)

### Installation and Setup

1. Download the latest release of `WLEDMusicSync.zip`
2. Extract all contents to a folder
3. Ensure you have the following structure:
   ```
   WLEDMusicSync/
   ├── WLEDMusicSync.exe   # Main application
   ├── timings.yml         # Light show configuration
   ├── config/
   │   └── controllers.yml # WLED device settings
   └── songs/             # Your music files
       └── song1.mp3      # Music files go here
   ```

### Running the Application

1. Double-click `WLEDMusicSync.exe` or run from command line:
   ```powershell
   .\WLEDMusicSync.exe --timings timings.yml
   ```

2. Select a song from the menu to begin playback

### Playback Controls
- Space: Play/Pause
- Left/Right: Seek ±5 seconds
- Page Up/Down: Seek ±30 seconds
- Up/Down: Volume control
- R: Restart current song
- Q: Quit application

## Configuration Files

### Controller Configuration (config/controllers.yml)
```yaml
controllers:
  controller_id:
    urls: 
      - "http://wled-device1.local"
      - "http://wled-device2.local"
    description: "Controller description"
    type: "WLED"
```

### Timing Configuration (timings.yml)
```yaml
songs:
  "song-file.mp3":
    - time: 0.0
      controllers:
        controller_id:
          preset: 1
    - time: 5.0
      controllers:
        controller_id:
          scene:
            on: true
            fx: 85
```

For detailed information about timing configuration, including all available options and examples, see [Timing Configuration Guide](readme_timings.md).

## Adding New Songs

1. Add the MP3 file to the `songs` directory
2. Add the song entry to `timings.yml` with your desired light show configuration
3. Update any preset mappings in `controller_presets.txt` if needed

## Troubleshooting

### Common Issues (Production/Executable Mode)
1. Missing DLL Errors
   - Ensure the executable wasn't quarantined by antivirus
   - Try running as administrator
   - Install Microsoft Visual C++ Redistributable if needed

2. File Not Found Errors
   - Verify all required files are in the correct locations
   - Check that `timings.yml` is in the same directory as the executable
   - Ensure the `config` and `songs` directories are present

3. WLED Connection Issues
   - Check that the WLED devices are accessible from your network
   - Verify the URLs in `config/controllers.yml` are correct
   - Try using IP addresses instead of hostnames

4. Audio Problems
   - Check Windows audio settings
   - Try running the executable as administrator
   - Verify MP3 files are not corrupted

5. Performance Issues
   - Close other applications using significant CPU
   - Ensure adequate free RAM (minimum 2GB recommended)
   - Try running with `--dry-run` to test timing accuracy

## Developer Guide

### Prerequisites
- Python 3.9 or higher
- Git (for cloning repository)

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Copter64/HalloweenLEDs.git
   cd HalloweenLEDs
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Project Structure
```
HalloweenLEDs/
├── main.py                  # Main entry point
├── requirements.txt         # Python dependencies
├── timings.yml             # Light show config
├── build_exe.py            # PyInstaller script
├── controller_presets.txt   # WLED presets
│
├── config/
│   └── controllers.yml     # WLED configuration
│
├── songs/                  # Media files
│   └── *.mp3              # Music files
│
└── wled_music_sync/       # Main package
    ├── __init__.py
    ├── config.py          # Config loading
    ├── config_loader.py   # Controller config
    ├── controller.py      # WLED interface
    ├── gui.py            # PyGame GUI
    ├── models.py         # Data models
    └── scheduler.py      # Event scheduling
```

### Development Mode Commands

1. Run the application:
   ```bash
   python main.py --timings timings.yml
   ```

2. Utility scripts:
   ```bash
   # Fetch WLED presets
   python fetch_presets.py
   
   # Update preset comments
   python update_preset_comments.py
   
   # Upload presets to WLED
   python wled_preset_uploader.py
   ```

3. Build executable:
   ```bash
   python build_exe.py
   ```

### Key Components

1. **MusicPlayer (gui.py)**
   - Graphical interface and song selection
   - Music playback controls
   - Real-time playback status

2. **WLEDController (controller.py)**
   - WLED device communication
   - Preset and scene management
   - Connection handling

3. **SceneScheduler (scheduler.py)**
   - Event timing and dispatch
   - Controller synchronization
   - Error handling

4. **Configuration (config.py, config_loader.py)**
   - YAML configuration parsing
   - Controller setup
   - Timing sequence management

### Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

The MIT License is a permissive license that is short and to the point. It lets people do anything they want with your code as long as they provide attribution back to you and don't hold you liable.

## Acknowledgments

- WLED Project (https://github.com/Aircoookie/WLED)
- PyGame Community

### Development Mode

To run the application in development mode:

1. Set up your Python environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python main.py --timings timings.yml
   ```

3. Optional utility scripts for development:
   ```bash
   # Fetch presets from WLED controllers
   python fetch_presets.py
   
   # Update preset comments
   python update_preset_comments.py
   
   # Upload presets to WLED controllers
   python wled_preset_uploader.py
   ```

### Production Mode (Windows Executable)

A standalone Windows executable is provided that doesn't require Python installation:

1. Required Files and Structure:
   ```
   WLEDMusicSync/
   ├── WLEDMusicSync.exe   # The main executable
   ├── timings.yml         # Light show timing configuration
   ├── config/
   │   └── controllers.yml # WLED controller configuration
   └── songs/             # Music and timing files directory
       ├── song1.mp3      # Music files
       ├── song1.txt      # Timing file for song1
       ├── song2.mp3
       └── song2.txt
   ```

2. Run the executable:
   ```bash
   WLEDMusicSync.exe --timings timings.yml
   ```

3. Configuration Requirements:
   - `config/controllers.yml`: Must contain your WLED device URLs
   - `timings.yml`: Must list all songs and their timing events
   - `songs/`: Directory must contain both MP3 and timing files
   - All paths in configuration files should be relative to the executable

### Command Line Arguments
- `--timings`: Path to the YAML timing configuration file (required)
- `--song`: Specific song to play (optional)
- `--dry-run`: Test mode - logs actions without sending to controllers

### Playback Controls
- Space: Play/Pause
- Left/Right: Seek ±5 seconds
- Page Up/Down: Seek ±30 seconds
- Up/Down: Volume control
- R: Restart current song
- Q: Quit application

### Utility Scripts (Development Only)
- `fetch_presets.py`: Retrieve presets from WLED controllers
- `update_preset_comments.py`: Update preset comments
- `wled_preset_uploader.py`: Upload presets to WLED controllers

## Development

### Key Components

1. **MusicPlayer (gui.py)**
   - Graphical interface for song selection
   - Music playback controls
   - Real-time playback status

2. **WLEDController (controller.py)**
   - WLED device communication
   - Preset and scene management
   - Connection handling and timeout management

3. **SceneScheduler (scheduler.py)**
   - Event timing and dispatch
   - Controller synchronization
   - Error handling and recovery

4. **Configuration (config.py, config_loader.py)**
   - YAML configuration parsing
   - Controller setup
   - Timing sequence management

### Error Handling
- Automatic session cleanup
- Connection timeout handling
- Resource management
- Detailed logging

## Adding New Songs

1. Add the MP3 file to the `songs` directory
2. Create a timing file in the `songs` directory with the same name
3. Add the song entry to `timings.yml`
4. Update any preset mappings in `controller_presets.txt` if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Troubleshooting

### Common Issues (Development Mode)
1. WLED Connection Failures
   - Verify controller URLs in `config/controllers.yml`
   - Check network connectivity
   - Ensure WLED devices are powered and connected

2. Missing Songs
   - Verify MP3 files are in the `songs` directory
   - Validate entries in `timings.yml`

3. Playback Issues
   - Check Python and pygame installation
   - Verify audio device settings
   - Check file permissions

### Common Issues (Production/Executable Mode)
1. Missing DLL Errors
   - Ensure the executable wasn't quarantined by antivirus
   - Try running as administrator
   - Install Microsoft Visual C++ Redistributable if needed

2. File Not Found Errors
   - Verify all required files are in the correct locations
   - Check that `timings.yml` is in the same directory as the executable
   - Ensure the `config` and `songs` directories are present

3. WLED Connection Issues
   - Check that the WLED devices are accessible from your network
   - Verify the URLs in `config/controllers.yml` are correct
   - Try using IP addresses instead of hostnames

4. Audio Problems
   - Check Windows audio settings
   - Try running the executable as administrator
   - Verify MP3 files are not corrupted

5. Performance Issues
   - Close other applications using significant CPU
   - Ensure adequate free RAM (minimum 2GB recommended)
   - Try running with `--dry-run` to test timing accuracy

## License

[Your License Here]

## Acknowledgments

- WLED Project (https://github.com/Aircoookie/WLED)
- PyGame Community