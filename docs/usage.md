# Halloween LEDs Documentation

## Overview
Halloween LEDs is a Python application that synchronizes LED light shows with music playback. It supports multiple WLED controllers and provides an interactive interface for controlling music playback and light show timing.

## Features
- Synchronized music playback with LED control
- Support for multiple WLED controllers
- YAML-based timing configuration
- Interactive playback controls
- Preset recall and scene control
- Bulk preset upload utility

## Installation

### Method 1: Install from Source
```bash
# Clone the repository
git clone <your-repo-url>
cd HalloweenLEDs

# Install with pip
pip install -e .

# Create .env file with your WLED controller IPs
echo "WLED_CONTROLLERS=sword1=http://192.168.1.186,mainscene=http://192.168.1.187" > .env
```

### Method 2: Install from Release
1. Download the latest release
2. Extract the ZIP file
3. Create a .env file with your WLED controller configuration
4. Run the executable

## Usage

### Music Sync Application
```bash
# Using installed package
music-sync --timings timings.yml

# Using executable
halloween-leds --timings timings.yml
```

### Interactive Controls
- Space: Play/Pause
- Left/Right: Seek ±5s
- PgUp/PgDown: Seek ±30s
- Up/Down: Volume control
- R: Restart
- Q: Quit

### Preset Upload Utility
```bash
# Upload single preset
preset-upload --ip 192.168.1.186 --file preset1.json --save

# Bulk upload from directory
preset-upload --ip 192.168.1.186 --dir ./presets --save
```

## Configuration

### Timing Configuration (timings.yml)
```yaml
songs:
  "song.mp3":
    - time: 0.0
      controllers:
        group:
          controllers: [sword1, sword2]
          preset: 1
        mainscene:
          preset: 1
```

### Environment Variables
Create a `.env` file with:
```
WLED_CONTROLLERS=controller1=http://192.168.1.186,controller2=http://192.168.1.187
```

## Development

### Setup Development Environment
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .
```

### Building from Source
```bash
# Clean previous builds
python scripts/build.py clean

# Build package and executable
python scripts/build.py all
```

## Troubleshooting

### Common Issues
1. "No timing data found": Ensure song filename matches exactly with timings.yml
2. "Controller not defined": Check .env file configuration
3. "Connection failed": Verify WLED controller IP addresses
4. "Playback issues": Check audio file format (MP3/WAV supported)

### Logs
The application logs to the console with timestamps and log levels. Use these for debugging.
