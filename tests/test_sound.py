import sounddevice as sd
import numpy as np

print(f"sounddevice version: {sd.__version__}")

sample_rate = 44100
duration = 2.0

t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
tone = np.sin(2 * np.pi * 440 * t) * 0.3

print("Playing 440Hz tone for 2 seconds...")
sd.play(tone, sample_rate)
sd.wait()
print("Done!")
