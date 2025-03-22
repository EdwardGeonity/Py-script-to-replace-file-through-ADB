import subprocess
import os
import shutil
from datetime import datetime

ADB_PATH = "adb"
REPLACE_DIR = "Replace"
BACKUP_DIR = "Backup"
TARGET_DIRS = ["/system/lib", "/system/vendor/lib"]

def log(msg):
    print(f"[LOG] {msg}")

def adb_shell_root(command):
    return subprocess.check_output([ADB_PATH, "shell", f"su -c \"{command}\""], text=True)

def adb_remount_system():
    log("🔧 Attempting to remount /system as rw...")
    try:
        adb_shell_root("mount -o rw,remount /system")
        log("✅ /system successfully remounted as rw.")
    except subprocess.CalledProcessError:
        log("⚠️ Standard remount failed, trying alternative method...")
        try:
            adb_shell_root("mount -o rw,remount /dev/block/bootdevice/by-name/system /system")
            log("✅ Alternative remount succeeded.")
        except subprocess.CalledProcessError as e:
            log("❌ Failed to remount /system.")
            exit(1)

def adb_pull(remote, local):
    result = subprocess.run([ADB_PATH, "pull", remote, local], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"Error while pulling file from device:\n{result.stderr}")

def adb_push(local, remote):
    result = subprocess.run([ADB_PATH, "push", local, remote], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"Error while pushing file to device:\n{result.stderr}")
        return False
    return True

def list_files(directory):
    try:
        output = adb_shell_root(f"ls {directory}")
        return output.strip().splitlines()
    except subprocess.CalledProcessError:
        return []

def find_on_device(filename):
    for directory in TARGET_DIRS:
        files = list_files(directory)
        if filename in files:
            return f"{directory}/{filename}"
    return None

def make_backup(remote_path, filename):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    file_backup_dir = os.path.join(BACKUP_DIR, filename)
    if os.path.exists(file_backup_dir):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived = file_backup_dir + "_" + timestamp
        shutil.move(file_backup_dir, archived)
    os.makedirs(file_backup_dir)
    local_backup_path = os.path.join(file_backup_dir, filename)
    adb_pull(remote_path, local_backup_path)
    log(f"Backup saved to: {local_backup_path}")

def replace_file_on_device(local_file, remote_path):
    filename = os.path.basename(remote_path)
    tmp_remote_path = f"/sdcard/{filename}"

    log(f"📤 Uploading to temporary path: {tmp_remote_path}")
    result = subprocess.run([ADB_PATH, "push", local_file, tmp_remote_path], capture_output=True, text=True)
    if result.returncode != 0:
        log(f"❌ Failed to push file to temporary path:\n{result.stderr}")
        return

    adb_remount_system()

    log(f"📁 Copying file from /sdcard/ to {remote_path} using su...")
    try:
        adb_shell_root(f"cp {tmp_remote_path} {remote_path}")
        adb_shell_root(f"chmod 644 {remote_path}")
        adb_shell_root(f"rm {tmp_remote_path}")
        log("✅ File copied, permissions set, temporary file deleted.")
    except subprocess.CalledProcessError as e:
        log(f"❌ Error during copy/delete operations: {e}")

def get_replacement_files():
    if os.path.isdir(REPLACE_DIR):
        return [f for f in os.listdir(REPLACE_DIR) if os.path.isfile(os.path.join(REPLACE_DIR, f))]
    return []

def main():
    log("Starting library replacement script...")
    replacement_files = get_replacement_files()

    if not replacement_files:
        log("Replace folder is empty or missing.")
        manual = input("Do you want to select a file manually? (y/n): ").strip().lower()
        if manual != 'y':
            return
        selected = input("Enter the path to the local file: ").strip()
        if not os.path.isfile(selected):
            log("Specified file does not exist.")
            return
        replacement_files = [os.path.basename(selected)]
        selected_manual_file = selected
    else:
        selected_manual_file = None

    adb_remount_system()

    for filename in replacement_files:
        local_file = selected_manual_file or os.path.join(REPLACE_DIR, filename)

        log(f"Looking for {filename} on the device...")
        device_path = find_on_device(filename)

        if not device_path:
            log(f"File {filename} not found on device.")
            continue

        log(f"File found: {device_path}")
        confirm = input("Do you want to replace this file? (y/n): ").strip().lower()
        if confirm != 'y':
            continue

        make_backup(device_path, filename)
        replace_file_on_device(local_file, device_path)

        log(f"✅ {filename} replaced successfully.")

if __name__ == "__main__":
    main()
