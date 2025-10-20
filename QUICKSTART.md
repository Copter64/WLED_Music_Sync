# Quick Start Guide - Halloween LEDs

## First Time Setup

1. Extract all files from the ZIP archive to a folder
2. Create a `.env` file in the same folder as halloween-leds.exe:
   ```
   WLED_CONTROLLERS=sword1=http://192.168.1.186,mainscene=http://192.168.1.187
   ```
   Replace the IP addresses with your WLED controller IPs

3. Place your music files in the `songs` folder

## Running the Light Show

1. Open Command Prompt/PowerShell in the folder
2. Run the command:
   ```
   halloween-leds.exe --timings timings.yml
   ```

3. If no song is specified, you'll see a list of available songs
4. Enter the number or name of the song you want to play

## Playback Controls

- SPACE: Play/Pause
- LEFT/RIGHT: Skip backward/forward 5 seconds
- UP/DOWN: Adjust volume
- PGUP/PGDN: Skip backward/forward 30 seconds
- R: Restart song
- Q: Quit

## Troubleshooting

1. "Controller not found" error:
   - Check your .env file
   - Verify WLED controller IP addresses
   - Ensure WLED controllers are powered on and connected to network

2. "No timing data" error:
   - Check that your song filename matches exactly with timings.yml
   - Music files should be in the songs folder

3. No sound:
   - Check volume controls (UP/DOWN keys)
   - Verify system audio is working
   - Try restarting the application

4. LEDs not responding:
   - Check WLED controller connections
   - Verify IP addresses in .env file
   - Try accessing WLED web interface directly

## Need Help?

See full documentation in docs/usage.md or visit:
https://github.com/yourusername/halloween-leds
