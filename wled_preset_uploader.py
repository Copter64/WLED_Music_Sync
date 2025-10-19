#!/usr/bin/env python3
"""
WLED Preset Uploader with Bulk Upload Support

Allows uploading individual or multiple JSON presets to WLED controllers
via the REST API. Presets can be applied temporarily or saved permanently.
"""

import json
import argparse
import requests
from pathlib import Path
from typing import Any, Dict, List


# region --- Utility Functions ---

def load_preset(file_path: Path) -> Dict[str, Any]:
    """
    Load a preset JSON from a file.

    :param file_path: Path to JSON file.
    :return: Dictionary containing preset data.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def send_preset(wled_ip: str, preset_data: Dict[str, Any], save: bool = False) -> bool:
    """
    Send a single preset to a WLED controller.

    :param wled_ip: IP address of the WLED controller.
    :param preset_data: Dictionary of preset data.
    :param save: Whether to save preset permanently (include psave key).
    :return: True if successful, False otherwise.
    """
    url = f"http://{wled_ip}/json"

    if save:
        if "psave" not in preset_data:
            preset_data["psave"] = 1  # default slot if not specified
    else:
        preset_data.pop("psave", None)

    try:
        response = requests.post(url, json=preset_data, timeout=5)
        if response.status_code == 200:
            print(f"✅ Sent preset successfully to {wled_ip}")
            return True
        print(f"⚠️ HTTP {response.status_code} Error: {response.text}")
    except requests.RequestException as err:
        print(f"❌ Network error while sending preset: {err}")
    return False


def discover_presets(directory: Path) -> List[Path]:
    """
    Find all JSON files in a directory.

    :param directory: Path to the directory containing JSON presets.
    :return: Sorted list of JSON file paths.
    """
    return sorted(directory.glob("*.json"))


# endregion


# region --- Bulk Upload ---

def bulk_upload(wled_ip: str, directory: Path, save: bool = False) -> None:
    """
    Upload all preset JSON files from a directory to a WLED controller.

    :param wled_ip: IP address of WLED controller.
    :param directory: Directory containing JSON preset files.
    :param save: Whether to store presets permanently (use psave).
    """
    presets = discover_presets(directory)

    if not presets:
        print(f"⚠️ No JSON files found in directory: {directory}")
        return

    print(f"📦 Found {len(presets)} preset(s) in {directory}")

    for index, preset_file in enumerate(presets, start=1):
        print(f"\n➡️  Uploading preset {index}/{len(presets)}: {preset_file.name}")
        preset_data = load_preset(preset_file)

        # Auto-assign psave numbers if saving permanently and not defined
        if save and "psave" not in preset_data:
            preset_data["psave"] = index

        success = send_preset(wled_ip, preset_data, save)
        if not success:
            print(f"❌ Failed to upload preset: {preset_file.name}")
        else:
            print(f"✅ Uploaded {preset_file.name}")

    print("\n🎉 Bulk upload complete.")


# endregion


# region --- CLI Interface ---

def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Upload WLED presets (single or bulk).")
    parser.add_argument("--ip", required=True, help="WLED controller IP address")
    parser.add_argument("--file", type=Path, help="Path to a single preset JSON file")
    parser.add_argument("--dir", type=Path, help="Directory containing multiple JSON presets")
    parser.add_argument("--save", action="store_true", help="Save preset(s) permanently using psave")
    return parser.parse_args()


def main() -> None:
    """
    Main entry point for CLI tool.
    """
    args = parse_args()

    if args.file and args.dir:
        print("⚠️ Please specify either --file or --dir, not both.")
        return

    if args.file:
        preset = load_preset(args.file)
        success = send_preset(args.ip, preset, args.save)
        if success:
            print("🎉 Preset uploaded successfully.")
        else:
            print("❌ Upload failed.")

    elif args.dir:
        bulk_upload(args.ip, args.dir, args.save)

    else:
        print("⚠️ You must specify either --file or --dir for upload.")


# endregion


# region --- Entry Point ---

if __name__ == "__main__":
    main()

# endregion
