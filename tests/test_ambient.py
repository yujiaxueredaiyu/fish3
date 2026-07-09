import sounddevice as sd
import wave
import numpy as np

print(f"sounddevice version: {sd.__version__}")

with wave.open('assets/ambient_ocean.wav', 'r') as wf:
    n_channels = wf.getnchannels()
    sampwidth = wf.getsampwidth()
    framerate = wf.getframerate()
    n_frames = wf.getnframes()
    data = wf.readframes(n_frames)
    
    if sampwidth == 2:
        data = np.frombuffer(data, dtype=np.int16)
        data = data.astype(np.float32) / 32767.0
    else:
        data = np.frombuffer(data, dtype=np.float32)
    
    if n_channels == 2:
        data = data.reshape(-1, 2)
        data = np.mean(data, axis=1)

print(f"Data: {len(data)} samples, max={np.max(data):.3f}, min={np.min(data):.3f}")
print("Playing ambient at full volume for 3 seconds...")

sd.play(data[:int(framerate * 3)] * 1.0, framerate)
sd.wait()
print("Done!")
