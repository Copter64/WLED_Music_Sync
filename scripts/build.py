#!/usr/bin/env python3
"""Build script for Halloween LEDs package"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

def clean():
    """Clean build artifacts"""
    print("Cleaning build artifacts...")
    dirs_to_clean = ['build', 'dist', '*.egg-info']
    for pattern in dirs_to_clean:
        for path in Path('.').glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    print("Clean complete!")

def setup_venv():
    """Create and setup virtual environment"""
    print("Setting up virtual environment...")
    subprocess.run([sys.executable, '-m', 'venv', '.venv'], check=True)
    
    # Determine the pip path based on OS
    if os.name == 'nt':  # Windows
        pip_path = '.venv\\Scripts\\pip'
    else:  # Unix-like
        pip_path = '.venv/bin/pip'
    
    # Install dependencies
    subprocess.run([pip_path, 'install', '-r', 'requirements.txt'], check=True)
    subprocess.run([pip_path, 'install', 'pyinstaller'], check=True)
    print("Virtual environment setup complete!")

def build_package():
    """Build Python package"""
    print("Building Python package...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'], check=True)
    print("Package build complete!")

def build_executable():
    """Build executable using PyInstaller"""
    print("Building executable...")
    subprocess.run([
        'pyinstaller',
        '--name=halloween-leds',
        '--onefile',
        '--add-data=presets:presets',
        '--hidden-import=pygame',
        '--hidden-import=librosa',
        '--hidden-import=numpy',
        '--hidden-import=matplotlib',
        'halloween_leds/music_sync.py'
    ], check=True)
    print("Executable build complete!")

def create_release():
    """Create a release package with all necessary files"""
    print("Creating release package...")
    os.makedirs('release', exist_ok=True)
    
    # Copy executable
    shutil.copy('dist/halloween-leds.exe', 'release/')
    
    # Copy presets and example files
    shutil.copytree('presets', 'release/presets', dirs_exist_ok=True)
    shutil.copy('timings.yml', 'release/timings.yml')
    
    # Create example .env file
    with open('release/.env.example', 'w') as f:
        f.write('WLED_CONTROLLERS=sword1=http://192.168.1.186,mainscene=http://192.168.1.187\n')
    
    # Create README
    with open('release/README.txt', 'w') as f:
        f.write("""Halloween LEDs - Quick Start Guide

1. Rename .env.example to .env and update with your WLED controller IPs
2. Run halloween-leds.exe --timings timings.yml
3. Use the following controls:
   - Space: Play/Pause
   - Left/Right: Seek ±5s
   - Up/Down: Volume
   - R: Restart
   - Q: Quit
""")
    
    # Create ZIP archive
    shutil.make_archive('halloween-leds', 'zip', 'release')
    print("Release package created!")

def main():
    """Main build process"""
    commands = {
        'clean': clean,
        'venv': setup_venv,
        'package': build_package,
        'exe': build_executable,
        'release': create_release,
        'all': lambda: [clean(), setup_venv(), build_package(), build_executable(), create_release()]
    }
    
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: python build.py [command]")
        print("Commands:")
        print("  clean   - Clean build artifacts")
        print("  venv    - Setup virtual environment")
        print("  package - Build Python package")
        print("  exe     - Build executable")
        print("  release - Create release package")
        print("  all     - Run all steps")
        return
    
    commands[sys.argv[1]]()

if __name__ == "__main__":
    main()
