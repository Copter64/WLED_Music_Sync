"""Build script for creating standalone executable."""
import os
import PyInstaller.__main__

def build_exe():
    """Build the executable using PyInstaller."""
    # Define resource files and directories to include
    datas = [
        ('config', 'config'),          # Config directory
        ('songs', 'songs'),            # Songs directory
        ('timings.yml', '.'),          # Main config file
        ('README.md', '.'),            # Documentation
    ]
    
    # Convert datas to PyInstaller format
    datas_args = []
    for src, dst in datas:
        datas_args.extend(['--add-data', f'{src}{os.pathsep}{dst}'])

    PyInstaller.__main__.run([
        'main.py',                     # Your main script
        '--name=WLEDMusicSync',        # Name of the executable
        '--onefile',                   # Create a single executable file
        '--windowed',                  # Don't show console window
        '--icon=config/app_icon.ico',  # Application icon (you'll need to create this)
        '--noconfirm',                 # Overwrite existing build files
        '--clean',                     # Clean PyInstaller cache
        '--log-level=WARN',           # Reduce log verbosity
        *datas_args,                   # Add resource files
        # Hidden imports for packages that PyInstaller might miss
        '--hidden-import=pygame',
        '--hidden-import=aiohttp',
        '--hidden-import=yaml',
        '--hidden-import=wled_music_sync',
    ])

if __name__ == '__main__':
    build_exe()
