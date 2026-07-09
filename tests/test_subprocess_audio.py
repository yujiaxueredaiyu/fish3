import subprocess
import time

base_path = r'd:\fish3\assets'
ambient_path = f"{base_path}\\ambient_ocean.wav"

print(f"Trying to play: {ambient_path}")

try:
    proc = subprocess.Popen(
        ['powershell', '-Command', f'(New-Object Media.SoundPlayer "{ambient_path}").Play()'],
        creationflags=subprocess.CREATE_NO_WINDOW)
    print("Started PowerShell sound player")
    time.sleep(5)
    print("Done")
except Exception as e:
    print(f"Error: {e}")
