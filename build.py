import os
import subprocess
import sys

def main():
    print("Building PasteRich executable using PyInstaller...")
    
    # We want a single-file executable, no console window, and an icon if possible.
    # We will use the default icon for now, or just leave it without a custom .ico
    
    # -F: One file
    # -w: Windowless (noconsole)
    # -n: Name
    # -i: Icon
    command = [
        sys.executable, "-m", "PyInstaller",
        "-F",
        "-w",
        "-i", "assets/icon.ico",
        "--add-data", f"assets/icon.ico{os.pathsep}assets",
        "-n", "PasteRich",
        "pasterich.py"
    ]
    
    try:
        subprocess.run(command, check=True)
        print("Build completed successfully! Check the 'dist' folder for PasteRich.exe")
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error: {e}")

if __name__ == "__main__":
    main()
