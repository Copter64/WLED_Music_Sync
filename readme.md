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