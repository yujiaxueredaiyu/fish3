import sounddevice as sd
import wave
import numpy as np
import time

base_path = r'd:\fish3\assets'

sd.default.device[1] = 4

for filename in ['ambient_ocean.wav', 'sparkle.wav', 'bubble.wav']:
    filepath = f"{base_path}\\{filename}"
    print(f"\nPlaying {filename}...")
    
    with wave.open(filepath, 'r') as wf:
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
    
    duration = len(data) / framerate
    print(f"Duration: {duration:.2f}s, Framerate: {framerate}")
    
    sd.play(data, framerate)
    time.sleep(duration + 0.5)
    sd.stop()

print("\nDone!")
