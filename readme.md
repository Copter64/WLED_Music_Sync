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



To run the music sync app
```
C:/Users/Copte/AppData/Local/Programs/Python/Python313/python.exe music_sync.py --timings timings.yml
```