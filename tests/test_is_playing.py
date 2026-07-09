import sounddevice as sd
import numpy as np
import time

print(f"sounddevice version: {sd.__version__}")

sample_rate = 44100
duration = 3.0
t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
tone = np.sin(2 * np.pi * 440 * t) * 0.3

print("Playing...")
sd.play(tone, sample_rate)

for i in range(6):
    time.sleep(0.5)
    print(f"Is playing: {sd.is_playing()}")

sd.wait()
print("Done!")
