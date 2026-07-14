import cv2
import numpy as np
import math
import traceback
import sys

from .audio import AudioSystem
from .particles import Particle, StarParticle
from .fish import Fish
from .hand_detection import HandDetector
from .visualization import OceanVisualizer
from .flow_field import FlowField
from .config import (
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    PARTICLE_CONFIG,
    FISH_CONFIG,
    SPARKLE_CONFIG,
    STAR_PARTICLE_CONFIG,
    VISUAL_CONFIG,
    get_assets_path
)


class OceanAura:
    def __init__(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self.width = width
        self.height = height
        
        self.visualizer = OceanVisualizer(width, height)
        
        self.particles = []
        for _ in range(PARTICLE_CONFIG['foreground_count']):
            self.particles.append(Particle(width, height, depth=np.random.uniform(0.0, 0.3)))
        for _ in range(PARTICLE_CONFIG['midground_count']):
            self.particles.append(Particle(width, height, depth=np.random.uniform(0.3, 0.7)))
        for _ in range(PARTICLE_CONFIG['background_count']):
            self.particles.append(Particle(width, height, depth=np.random.uniform(0.7, 1.0)))
        
        self.fishes = [Fish(width, height) for _ in range(FISH_CONFIG['total_count'])]
        all_indices = np.arange(FISH_CONFIG['total_count'])
        np.random.shuffle(all_indices)
        starfish_indices = all_indices[:FISH_CONFIG['starfish_count']]
        for idx in starfish_indices:
            self.fishes[idx].is_starfish = True
        dissolve_indices = all_indices[FISH_CONFIG['starfish_count']:FISH_CONFIG['starfish_count'] + FISH_CONFIG['dissolve_fish_count']]
        for idx in dissolve_indices:
            self.fishes[idx].is_dissolve_fish = True
        
        self.sparkles = []
        for _ in range(SPARKLE_CONFIG['count']):
            hue = np.random.uniform(0, 120)
            saturation = np.random.uniform(0.0, 0.3)
            hsv_color = np.uint8([[[int(hue), int(saturation * 255), 255]]])
            bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
            base_color = (int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2]))
            self.sparkles.append({
                'angle': np.random.uniform(0, 2 * math.pi),
                'radius': np.random.uniform(SPARKLE_CONFIG['radius_min'], SPARKLE_CONFIG['radius_max']),
                'speed': np.random.uniform(SPARKLE_CONFIG['speed_min'], SPARKLE_CONFIG['speed_max']),
                'size': np.random.uniform(SPARKLE_CONFIG['size_min'], SPARKLE_CONFIG['size_max']),
                'brightness': np.random.uniform(0.5, 0.9),
                'phase': np.random.uniform(0, 2 * math.pi),
                'base_color': base_color,
            })
        
        self.star_particles = []
        
        self.time = 0
        self.hand_x = None
        self.hand_y = None
        self.smooth_hand_x = width // 2
        self.smooth_hand_y = height // 2
        self.hand_visible = False
        
        self.is_fist = False
        self.was_fist = False
        
        self.detector = HandDetector()
        self.audio = AudioSystem(get_assets_path())
        self.flow_field = FlowField()
        
        self.fist_count = 0
        self.highlight_active = False
        self.highlight_time = 0
        self.highlight_intensity = 0.0
        
        self.state = 'IDLE'
        self.state_intensity = 0.0
        self.target_state_intensity = 0.0
        self.last_hand_time = 0
        self.state_timer = 0
        self.text_alpha = 0.0
        self.current_text = ""
    
    def release_starlight(self):
        if self.hand_x is None or self.hand_y is None:
            return
        
        if len(self.star_particles) > STAR_PARTICLE_CONFIG['max_total']:
            return
        
        particle_count = np.random.randint(
            STAR_PARTICLE_CONFIG['min_count'],
            STAR_PARTICLE_CONFIG['max_count'] + 1
        )
        for _ in range(particle_count):
            self.star_particles.append(StarParticle(self.hand_x, self.hand_y, self.width, self.height))
        
        self.audio.play_sparkle()
    
    def trigger_highlight(self):
        self.highlight_active = True
        self.highlight_time = 0
    
    def run(self):
        cv2.namedWindow('Ocean Aura', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Ocean Aura', self.width, self.height)
        
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        if not cap.isOpened():
            print("Error: Could not open camera")
            cv2.destroyAllWindows()
            input("Press Enter to exit...")
            return
        
        if not self.detector.init_detector():
            cv2.destroyAllWindows()
            input("Press Enter to exit...")
            return
        
        try:
            while True:
                self.time += 1
                breath_factor = math.sin(self.time * VISUAL_CONFIG['breath_speed'])
                
                if self.time == 1:
                    self.current_text = "Move your hand\nto awaken the ocean."
                    self.state_timer = 0
                
                if self.hand_x is not None and self.hand_y is not None:
                    self.last_hand_time = self.time
                
                if self.state == 'IDLE':
                    self.target_state_intensity = 0.0
                    if self.hand_x is not None and self.hand_y is not None:
                        self.state = 'AWAKENING'
                        self.state_timer = 0
                        self.current_text = ""
                        self.text_alpha = 0.0
                    
                    self.state_timer += 1
                    if self.state_timer <= 90:
                        self.text_alpha = min(0.7, self.state_timer / 30)
                    elif self.state_timer <= 180:
                        self.text_alpha = 0.7 - (self.state_timer - 90) / 90 * 0.7
                    else:
                        self.text_alpha = 0.0
                
                elif self.state == 'AWAKENING':
                    self.target_state_intensity = 1.0
                    self.state_timer += 1
                    if self.state_timer >= 30:
                        self.state = 'INTERACTIVE'
                        self.state_timer = 0
                
                elif self.state == 'INTERACTIVE':
                    self.target_state_intensity = 1.0
                    no_hand_duration = self.time - self.last_hand_time
                    if no_hand_duration > 240:
                        self.state = 'RETURN_TO_IDLE'
                        self.state_timer = 0
                        self.current_text = "The ocean returns\nto silence."
                        self.text_alpha = 0.0
                
                elif self.state == 'RETURN_TO_IDLE':
                    self.target_state_intensity = 0.0
                    self.state_timer += 1
                    
                    if self.state_timer <= 60:
                        self.text_alpha = min(0.7, self.state_timer / 30)
                    elif self.state_timer <= 150:
                        self.text_alpha = 0.7 - (self.state_timer - 60) / 90 * 0.7
                    else:
                        self.text_alpha = 0.0
                    
                    if self.state_timer >= 150:
                        self.state = 'IDLE'
                        self.state_timer = 0
                        self.current_text = "Move your hand\nto awaken the ocean."
                        self.fist_count = 0
                
                self.state_intensity += (self.target_state_intensity - self.state_intensity) * 0.08
                
                if self.time == 1 or (self.state_intensity > 0.5 and not self.audio._ambient_playing):
                    self.audio.start_ambient()
                elif self.state_intensity < 0.1 and self.audio._ambient_playing:
                    self.audio.stop()
                
                self.audio.update()
                self.flow_field.update()
                
                if self.highlight_active:
                    self.highlight_time += 1
                    total_frames = 60
                    ramp_up_frames = 15
                    
                    if self.highlight_time <= ramp_up_frames:
                        self.highlight_intensity = (self.highlight_time / ramp_up_frames) ** 2
                    elif self.highlight_time <= total_frames:
                        decay_progress = (self.highlight_time - ramp_up_frames) / (total_frames - ramp_up_frames)
                        self.highlight_intensity = 1.0 - decay_progress ** 2
                    else:
                        self.highlight_intensity = 0.0
                        self.highlight_active = False
                
                frame = self.visualizer.create_background(
                    breath_factor,
                    self.smooth_hand_x,
                    self.smooth_hand_y,
                    self.hand_visible,
                    self.highlight_intensity,
                    self.state_intensity
                )
                
                success, camera_frame = cap.read()
                if success:
                    camera_frame_rgb = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                    
                    result = self.detector.detect_hand(camera_frame_rgb)
                    
                    if result is not None:
                        self.hand_x = result['x'] * self.width
                        self.hand_y = result['y'] * self.height
                        self.is_fist = result['is_fist']
                        
                        if self.is_fist and not self.was_fist:
                            self.fist_count += 1
                            self.release_starlight()
                            
                            if self.fist_count > 0 and self.fist_count % 3 == 0:
                                self.trigger_highlight()
                        
                        self.was_fist = self.is_fist
                    else:
                        self.hand_x = None
                        self.hand_y = None
                        self.is_fist = False
                        self.was_fist = False
                else:
                    self.hand_x = None
                    self.hand_y = None
                
                if self.hand_x is not None and self.hand_y is not None:
                    self.hand_visible = True
                    self.smooth_hand_x += (self.hand_x - self.smooth_hand_x) * VISUAL_CONFIG['hand_smooth_factor']
                    self.smooth_hand_y += (self.hand_y - self.smooth_hand_y) * VISUAL_CONFIG['hand_smooth_factor']
                else:
                    self.hand_visible = False
                
                for particle in self.particles:
                    particle.update(self.time, self.hand_x, self.hand_y, self.flow_field, self.highlight_intensity, self.state_intensity)
                    
                    if self.state_intensity > 0.3 or particle.depth > 0.5 or (hash(particle) % 3 == 0):
                        particle.draw(frame)
                
                if self.state_intensity > 0.5:
                    for sparkle in self.sparkles:
                        sparkle['angle'] += sparkle['speed']
                        flicker = 0.6 + 0.4 * math.sin(self.time * 0.008 + sparkle['phase'])
                        x = self.smooth_hand_x + math.cos(sparkle['angle']) * sparkle['radius']
                        y = self.smooth_hand_y + math.sin(sparkle['angle']) * sparkle['radius']
                        
                        base_color = sparkle['base_color']
                        color = (int(base_color[0] * sparkle['brightness'] * flicker), 
                                 int(base_color[1] * sparkle['brightness'] * flicker), 
                                 int(base_color[2] * sparkle['brightness'] * flicker))
                        
                        size = int(sparkle['size'] * flicker)
                        if size > 0 and x > 0 and x < self.width and y > 0 and y < self.height:
                            cv2.circle(frame, (int(x), int(y)), size, color, -1)
                            outer_size = size * 2
                            outer_color = (int(base_color[0] * sparkle['brightness'] * flicker * 0.4), 
                                           int(base_color[1] * sparkle['brightness'] * flicker * 0.4), 
                                           int(base_color[2] * sparkle['brightness'] * flicker * 0.4))
                            cv2.circle(frame, (int(x), int(y)), outer_size, outer_color, -1)
                
                for fish in self.fishes:
                    prev_alpha = fish.alpha
                    fish.update(self.time, self.hand_x, self.hand_y, self.flow_field, self.highlight_intensity, self.state_intensity)
                    fish.draw(frame)
                    
                    if prev_alpha < 0.1 and fish.alpha >= 0.1:
                        if np.random.random() < 0.2:
                            self.audio.play_bubble()
                
                self.star_particles = [p for p in self.star_particles if p.update(self.flow_field)]
                for p in self.star_particles:
                    p.draw(frame)
                
                frame = cv2.flip(frame, 1)
                
                if self.text_alpha > 0.01 and self.current_text:
                    text_layer = np.zeros((self.height, self.width), dtype=np.uint8)
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.8
                    thickness = 2
                    
                    lines = self.current_text.split('\n')
                    line_height = 40
                    total_height = len(lines) * line_height
                    start_y = int(self.height / 2 - total_height / 2)
                    
                    for i, line in enumerate(lines):
                        text_size = cv2.getTextSize(line, font, font_scale, thickness)[0]
                        text_x = int(self.width / 2 - text_size[0] / 2)
                        text_y = start_y + i * line_height
                        
                        cv2.putText(text_layer, line, (text_x, text_y), font, font_scale, 255, thickness)
                    
                    mask = text_layer > 0
                    frame[mask] = (int(255 * self.text_alpha), int(255 * self.text_alpha), int(255 * self.text_alpha))
                
                cv2.imshow('Ocean Aura', frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:
                    break
                
                try:
                    if cv2.getWindowProperty('Ocean Aura', cv2.WND_PROP_VISIBLE) < 1:
                        break
                except cv2.error:
                    break
        except Exception as e:
            print(f"Error during runtime: {e}")
            traceback.print_exc()
            input("Press Enter to exit...")
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.audio.stop()


def main():
    app = OceanAura()
    app.run()


if __name__ == '__main__':
    main()
