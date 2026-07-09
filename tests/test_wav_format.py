import wave
import winsound

base_path = r'd:\fish3\assets'

for filename in ['ambient_ocean.wav', 'sparkle.wav', 'bubble.wav']:
    filepath = f"{base_path}\\{filename}"
    try:
        with wave.open(filepath, 'r') as wf:
            print(f"\n{filename}:")
            print(f"  Channels: {wf.getnchannels()}")
            print(f"  Sample width: {wf.getsampwidth()}")
            print(f"  Framerate: {wf.getframerate()}")
            print(f"  Compression: {wf.getcomptype()}")
            print(f"  Format: {wf.getformat()}")
        
        print("  Testing winsound...")
        winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
        import time
        time.sleep(2)
        
    except Exception as e:
        print(f"  Error: {e}")

print("\nDone!")
