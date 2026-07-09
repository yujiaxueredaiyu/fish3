import sounddevice as sd
import wave
import numpy as np

print(f"sounddevice version: {sd.__version__}")
print(f"Available devices:")
devices = sd.query_devices()
for i, dev in enumerate(devices):
    print(f"  {i}: {dev['name']}")

print(f"\nDefault output device: {sd.default.device[1]}")

try:
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration), dtype=np.float32)
    tone = np.sin(2 * np.pi * 440 * t) * 0.3
    
    print("\nTesting tone playback...")
    sd.play(tone, sample_rate)
    sd.wait()
    print("Tone played successfully!")
    
    wav_path = 'assets/sparkle.wav'
    with wave.open(wav_path, 'r') as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        print(f"\nWAV file info: {n_channels} channels, {sampwidth} bytes, {framerate} Hz, {n_frames} frames")
        
        data = wf.readframes(n_frames)
        if sampwidth == 2:
            data = np.frombuffer(data, dtype=np.int16)
            data = data.astype(np.float32) / 32767.0
        else:
            data = np.frombuffer(data, dtype=np.float32)
        
        if n_channels == 2:
            data = data.reshape(-1, 2)
            data = np.mean(data, axis=1)
        
        print(f"Loaded data: {len(data)} samples, max={np.max(data):.3f}, min={np.min(data):.3f}")
        
        print("Playing sparkle.wav...")
        sd.play(data * 0.5, framerate)
        sd.wait()
        print("Sparkle played successfully!")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
