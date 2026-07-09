import sounddevice as sd
import numpy as np

print(f"sounddevice version: {sd.__version__}")
print(f"Available methods: {[m for m in dir(sd) if not m.startswith('_')]}")

sample_rate = 44100
duration = 2.0
samples = int(sample_rate * duration)

t = np.linspace(0, duration, samples, dtype=np.float32)
tone = np.sin(2 * np.pi * 440 * t) * 0.3

print("\nTrying RawOutputStream...")
try:
    stream = sd.RawOutputStream(samplerate=sample_rate, channels=1, dtype='float32')
    stream.start()
    stream.write(tone.tobytes())
    print("Stream started and data written")
    stream.stop()
    stream.close()
    print("Stream closed")
except Exception as e:
    print(f"RawOutputStream error: {e}")

print("\nTrying OutputStream...")
try:
    stream = sd.OutputStream(samplerate=sample_rate, channels=1, dtype='float32')
    stream.start()
    stream.write(tone)
    print("Stream started and data written")
    stream.stop()
    stream.close()
    print("Stream closed")
except Exception as e:
    print(f"OutputStream error: {e}")
