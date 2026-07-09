import winsound
import time

base_path = r'd:\fish3\assets'

print("Testing winsound...")

print("\nPlaying ambient...")
winsound.PlaySound(f"{base_path}\\ambient_ocean.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
time.sleep(3)

print("Playing sparkle...")
winsound.PlaySound(f"{base_path}\\sparkle.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
time.sleep(1)

print("Playing bubble...")
winsound.PlaySound(f"{base_path}\\bubble.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
time.sleep(1)

print("\nDone!")
