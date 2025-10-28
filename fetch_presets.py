#!/usr/bin/env python3
import requests

def get_presets():
    url = "http://192.168.1.14/presets.json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        presets = response.json()
        
        # Write to a file
        with open('controller_presets.txt', 'w') as f:
            for key, value in presets.items():
                if isinstance(value, dict) and 'n' in value:
                    f.write(f"Preset {key}: {value['n']}\n")
                    
        print("Presets have been saved to controller_presets.txt")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_presets()
