#!/usr/bin/env python3
import asyncio
import os
from typing import Dict
import aiohttp
from dotenv import load_dotenv

async def get_controller_presets(url: str) -> Dict[int, str]:
    """Fetch presets from a WLED controller."""
    timeout = aiohttp.ClientTimeout(total=5, connect=2)
    connector = aiohttp.TCPConnector(force_close=True)
    
    # List of possible API endpoints to try
    endpoints = [
        '/presets.json',      # Common endpoint
        '/json/presets',      # Alternative endpoint
        '/json/cfg/presets',  # Newer versions
        '/json/state',        # Current state endpoint
        '/json'               # Basic endpoint
    ]
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        try:
            print(f"Connecting to {url}...")
            
            # Try each endpoint
            for endpoint in endpoints:
                try:
                    full_url = f"{url}{endpoint}"
                    print(f"Trying {full_url}...")
                    async with session.get(full_url) as resp:
                        if resp.status == 200:
                            try:
                                data = await resp.json(content_type=None)
                                if isinstance(data, dict):
                                    # Found some data, try to extract presets
                                    presets = {}
                                    
                                    # Handle different response formats
                                    if endpoint == '/json/state' and 'ps' in data:
                                        # Current preset from state
                                        presets[data['ps']] = f"Active Preset {data['ps']}"
                                    elif isinstance(data, dict):
                                        # Try to extract preset information
                                        for key, value in data.items():
                                            if key.isdigit() and isinstance(value, dict) and 'n' in value:
                                                presets[int(key)] = value['n']
                                            elif isinstance(value, dict) and 'id' in value and 'n' in value:
                                                presets[value['id']] = value['n']
                                    
                                    if presets:
                                        print(f"Successfully fetched {len(presets)} presets from {full_url}")
                                        return presets
                                    
                            except Exception as e:
                                print(f"Could not parse response from {full_url}: {e}")
                                continue
                                
                except Exception as e:
                    print(f"Error with {endpoint}: {e}")
                    continue
            
            print(f"No preset data found at {url} after trying all endpoints")
            
        except aiohttp.ClientConnectorError:
            print(f"Error: Could not connect to {url} - Please check if the controller is online")
        except Exception as e:
            print(f"Error accessing {url}: {str(e)}")
    
    return {}

def load_wled_controllers() -> Dict[str, str]:
    """Load WLED controller URLs from .env file."""
    load_dotenv()
    controllers = {}
    wled_config = os.getenv('WLED_CONTROLLERS', '')
    if not wled_config:
        return controllers
    
    # Parse controller definitions (e.g., "sword1=http://192.168.1.186,mainscene=http://192.168.1.187")
    for ctrl in wled_config.split(','):
        if '=' in ctrl:
            name, url = ctrl.split('=', 1)
            controllers[name.strip()] = url.strip()
    
    return controllers

async def get_all_presets() -> Dict[str, Dict[int, str]]:
    """Fetch presets from all configured controllers."""
    controllers = load_wled_controllers()
    all_presets = {}
    
    # Fetch presets from all controllers in parallel
    async def fetch_controller(name: str, url: str):
        presets = await get_controller_presets(url)
        if presets:
            all_presets[name] = presets
    
    tasks = [fetch_controller(name, url) for name, url in controllers.items()]
    await asyncio.gather(*tasks)
    return all_presets

def update_yaml_with_comments(file_path: str, preset_info: Dict[str, Dict[int, str]]) -> None:
    """Update the YAML file with preset comments."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Split into lines for processing
    lines = content.split('\n')
    new_lines = []
    
    # Track context
    in_controllers = False
    in_group = False
    current_group_controllers = []
    current_controller = None
    
    for line in lines:
        stripped = line.strip()
        
        # Track section context
        if stripped == 'controllers:':
            in_controllers = True
            in_group = False
            current_group_controllers = []
        elif in_controllers and stripped == 'group:':
            in_group = True
            current_controller = None
        elif in_controllers and not in_group and ':' in stripped:
            current_controller = stripped.split(':')[0]
            
        # Handle group controller list
        if in_group and 'controllers:' in stripped and '[' in stripped:
            ctrl_list = stripped[stripped.find('[')+1:stripped.find(']')]
            current_group_controllers = [c.strip() for c in ctrl_list.split(',')]
            
        # Handle preset lines
        if 'preset:' in stripped:
            try:
                preset_num = int(stripped.split(':')[1].strip())
                preset_names = set()
                
                # Get preset names based on context
                if in_group and current_group_controllers:
                    for ctrl in current_group_controllers:
                        if ctrl in preset_info and preset_num in preset_info[ctrl]:
                            preset_names.add(preset_info[ctrl][preset_num])
                elif current_controller and current_controller in preset_info:
                    if preset_num in preset_info[current_controller]:
                        preset_names.add(preset_info[current_controller][preset_num])
                
                # Add comment if we found preset names
                if preset_names:
                    line = f"{line}  # {', '.join(sorted(preset_names))}"
            except ValueError:
                pass
        
        new_lines.append(line)

    # Write back to file
    with open(file_path, 'w') as f:
        f.write('\n'.join(new_lines))

async def main():
    print("Fetching preset information from WLED controllers...")
    preset_info = await get_all_presets()
    
    if not preset_info:
        print("No preset information found. Please check your .env file and controller connectivity.")
        return

    # Print summary of what we found
    for controller, presets in preset_info.items():
        print(f"\nFound {len(presets)} presets for controller '{controller}':")
        for num, name in sorted(presets.items()):
            print(f"  Preset {num:2d}: {name}")

    # Update the timings.yml file
    timings_file = "timings.yml"
    if os.path.exists(timings_file):
        print(f"\nUpdating {timings_file} with preset comments...")
        update_yaml_with_comments(timings_file, preset_info)
        print("Done!")
    else:
        print(f"\nError: {timings_file} not found!")

if __name__ == "__main__":
    asyncio.run(main())
