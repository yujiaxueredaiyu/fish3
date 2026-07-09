import os
import time
import threading
import subprocess

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

from .config import AUDIO_CONFIG


class AudioSystem:
    def __init__(self, assets_path=None):
        self.enabled = HAS_WINSOUND
        self.last_bubble_time = 0
        self._ambient_playing = False
        
        if assets_path is None:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            assets_path = os.path.join(base_path, 'assets')
        
        self.ambient_path = os.path.join(assets_path, 'samuelfjohanns-atmosphere-of-atlantis-246389.wav')
        self.sparkle_path = os.path.join(assets_path, 'djartmusic-christmas-sparkle-whoosh_1-275404.wav')
        self.bubble_path = os.path.join(assets_path, 'krnbeatz-bubble-in-water-422579.wav')
    
    def update(self):
        pass
    
    def start_ambient(self):
        if not self.enabled:
            return
        
        if not os.path.exists(self.ambient_path):
            return
        
        if self._ambient_playing:
            return
        
        self._ambient_playing = True
        
        try:
            winsound.PlaySound(self.ambient_path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
        except Exception:
            self._ambient_playing = False
    
    def play_sparkle(self):
        if not self.enabled or not os.path.exists(self.sparkle_path):
            return
        
        def play():
            cmd = f'(New-Object System.Media.SoundPlayer "{self.sparkle_path}").PlaySync()'
            try:
                subprocess.run(
                    ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', cmd],
                    creationflags=0x08000000,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10
                )
            except Exception:
                pass
        
        t = threading.Thread(target=play, daemon=True)
        t.start()
    
    def play_bubble(self):
        if not self.enabled or not os.path.exists(self.bubble_path):
            return
        
        now = time.time()
        if now - self.last_bubble_time < AUDIO_CONFIG['bubble_cooldown']:
            return
        self.last_bubble_time = now
        
        def play():
            cmd = f'(New-Object System.Media.SoundPlayer "{self.bubble_path}").PlaySync()'
            try:
                subprocess.run(
                    ['powershell', '-ExecutionPolicy', 'Bypass', '-Command', cmd],
                    creationflags=0x08000000,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10
                )
            except Exception:
                pass
        
        t = threading.Thread(target=play, daemon=True)
        t.start()
    
    def stop(self):
        self._ambient_playing = False
        
        if self.enabled:
            winsound.PlaySound(None, winsound.SND_PURGE)
