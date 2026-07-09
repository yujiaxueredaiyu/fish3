import sounddevice as sd
import numpy as np

sample_rate = 44100
duration = 2.0
t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
tone = np.sin(2 * np.pi * 440 * t) * 0.3

print("Testing sd.play with loop=True...")
try:
    sd.play(tone, sample_rate, loop=True)
    print("Play started with loop")
    import time
    time.sleep(5)
    sd.stop()
    print("Play stopped")
except Exception as e:
    print(f"Error: {e}")
