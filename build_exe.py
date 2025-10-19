import PyInstaller.__main__
import sys
import os

def create_executable():
    # Add any additional data files here
    datas = [
        ('presets', 'presets'),  # Include presets folder
        ('.env', '.'),  # Include .env file if it exists
    ]
    
    PyInstaller.__main__.run([
        'music_sync.py',  # Your main script
        '--onefile',  # Create a single executable
        '--name=halloween-leds',  # Name of the executable
        '--add-data=presets:presets',  # Include presets folder
        '--hidden-import=pygame',
        '--hidden-import=librosa',
        '--hidden-import=numpy',
        '--hidden-import=matplotlib',
    ])

if __name__ == "__main__":
    create_executable()
