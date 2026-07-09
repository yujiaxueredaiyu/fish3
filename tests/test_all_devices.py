import sounddevice as sd
import numpy as np
import time

devices = sd.query_devices()
output_devices = [(i, dev) for i, dev in enumerate(devices) if dev['max_output_channels'] > 0]

print("Available audio output devices:")
for i, dev in output_devices:
    print(f"  {i}: {dev['name']}")

sample_rate = 44100
duration = 1.0
t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
tone = np.sin(2 * np.pi * 440 * t) * 0.5

for idx, (dev_id, dev) in enumerate(output_devices):
    try:
        sd.default.device[1] = dev_id
        print(f"\nPlaying on device {dev_id}: {dev['name']}")
        sd.play(tone, sample_rate)
        time.sleep(1.5)
        sd.stop()
        time.sleep(0.5)
    except Exception as e:
        print(f"Failed to play on device {dev_id}: {e}")

print("\nDone testing all devices!")
