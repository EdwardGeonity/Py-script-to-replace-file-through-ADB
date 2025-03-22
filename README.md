# Android System Library Replacer (via ADB + su)

This Python script is designed to help replace system `.so` library files on Android devices where `adb root` is not available (i.e., production builds). It uses `adb` and `su` to remount `/system` as read-write, back up existing libraries, and replace them with new versions.

---

## ✅ Features

- Scans for replacement `.so` files in a local `Replace/` folder.
- If `Replace/` is empty, allows manual selection of files.
- Checks whether a matching library exists on the device in:
  - `/system/lib/`
  - `/system/vendor/lib/`
- Makes a timestamped backup of the original library in `Backup/`.
- Pushes the new library via `/sdcard/`, then uses `su` to:
  - Copy it to the system path
  - Set permissions to `644`
  - Delete the temporary file
- Supports devices with **root access via Magisk/SuperSU**, even without `adb root`.


📁 Folder Structure
project/ 
├── Replace/ # Place your replacement .so files here 
├── Backup/ # Automatically created for backups 
└── replace_libs.py # The main script


---

## 🧩 Requirements

- Python 3
- ADB installed and in your PATH
- Android device with:
  - USB debugging enabled
  - Root access via Magisk/SuperSU
  - Read/write remount capability for `/system`
- `adb shell` with working `su` (test with `adb shell → su → whoami → root`)

---

## 🚀 Usage

1. Connect your Android device via USB.
2. Enable USB Debugging.
3. Place `.so` files to replace into the `Replace/` folder.
4. Run the script:

```bash
python3 replace_libs.py

    Follow the prompts to confirm replacements.

⚠️ Disclaimer

    This tool modifies system files — use at your own risk.
    Always ensure you have proper backups and understand the implications of modifying /system.
