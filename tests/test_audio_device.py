import sounddevice as sd
import numpy as np

devices = sd.query_devices()
for i, dev in enumerate(devices):
    if dev['max_output_channels'] > 0:
        print(f"{i}: {dev['name']}")

print(f"\nCurrent default output: {sd.default.device[1]}")

sample_rate = 44100
duration = 1.0
t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
tone = np.sin(2 * np.pi * 440 * t) * 0.5

print("\nTesting with device 4 (headphones)...")
sd.default.device[1] = 4
sd.play(tone, sample_rate)
sd.wait()

print("Testing with device 5 (speakers)...")
sd.default.device[1] = 5
sd.play(tone, sample_rate)
sd.wait()

print("Done!")
