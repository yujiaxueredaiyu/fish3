import os
import threading

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class AudioSystem:
    def __init__(self, assets_path=None):
        self.enabled = HAS_WINSOUND
        self.last_bubble_time = 0
        self._ambient_thread = None
        self._ambient_playing = False
        
        if assets_path is None:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            assets_path = os.path.join(base_path, 'assets')
        
        self.ambient_path = os.path.join(assets_path, 'ambient_ocean.wav')
        self.sparkle_path = os.path.join(assets_path, 'sparkle.wav')
        self.bubble_path = os.path.join(assets_path, 'bubble.wav')
    
    def _play_effect(self, filepath):
        if not os.path.exists(filepath):
            return
        
        try:
            winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_SYNC)
        except Exception:
            pass
    
    def _ambient_loop(self):
        while self._ambient_playing:
            try:
                winsound.PlaySound(self.ambient_path, winsound.SND_FILENAME | winsound.SND_SYNC)
            except Exception:
                break
    
    def _effect_thread(self, filepath):
        was_playing = self._ambient_playing
        self._ambient_playing = False
        
        self._play_effect(filepath)
        
        if was_playing:
            self._ambient_playing = True
            self._ambient_thread = threading.Thread(target=self._ambient_loop, daemon=True)
            self._ambient_thread.start()
    
    def update(self):
        if not self.enabled:
            return
        
        if not self._ambient_playing and os.path.exists(self.ambient_path):
            self._ambient_playing = True
            self._ambient_thread = threading.Thread(target=self._ambient_loop, daemon=True)
            self._ambient_thread.start()
    
    def play_sparkle(self):
        if self.enabled and os.path.exists(self.sparkle_path):
            t = threading.Thread(target=self._effect_thread, args=(self.sparkle_path,), daemon=True)
            t.start()
    
    def play_bubble(self):
        if self.enabled and os.path.exists(self.bubble_path):
            import time
            now = time.time()
            if now - self.last_bubble_time > 0.5:
                t = threading.Thread(target=self._effect_thread, args=(self.bubble_path,), daemon=True)
                t.start()
                self.last_bubble_time = now
    
    def stop(self):
        if self.enabled:
            self._ambient_playing = False
            winsound.PlaySound(None, winsound.SND_PURGE)