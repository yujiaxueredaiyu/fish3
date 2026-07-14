import math
import numpy as np
import cv2


class Particle:
    def __init__(self, width, height, depth=0.5):
        self.width = width
        self.height = height
        self.depth = depth
        
        self.x = np.random.uniform(0, width)
        self.y = np.random.uniform(0, height)
        
        speed_factor = 1.0 + (1.0 - depth) * 0.3
        self.base_vx = np.random.uniform(-0.08, 0.08) * speed_factor
        self.base_vy = np.random.uniform(-0.08, 0.08) * speed_factor - 0.015 * (1.0 - depth)
        self.vx = self.base_vx
        self.vy = self.base_vy
        
        size_min = 1.5 + (1.0 - depth) * 1.0
        size_max = 2.5 + (1.0 - depth) * 1.5
        self.base_size = np.random.uniform(size_min, size_max)
        self.size = self.base_size
        
        alpha_min = 0.15 + (1.0 - depth) * 0.10
        alpha_max = 0.28 + (1.0 - depth) * 0.12
        self.base_alpha = np.random.uniform(alpha_min, alpha_max)
        self.alpha = self.base_alpha
        
        self.phase = np.random.uniform(0, 2 * math.pi)
        
        r = np.random.random()
        if r < 0.3:
            hue = 0
            saturation = 0.0
        elif r < 0.6:
            hue = np.random.uniform(100, 125)
            saturation = np.random.uniform(0.15, 0.4)
        else:
            hue = np.random.uniform(85, 105)
            saturation = np.random.uniform(0.2, 0.45)
        
        self.base_brightness = np.random.uniform(0.65, 0.95)
        self.brightness = self.base_brightness
        
        self._precompute_colors(hue, saturation)
        
        self.orbit_radius = np.random.uniform(50, 120)
        self.orbit_speed = np.random.uniform(0.0015, 0.004) * (1 if np.random.random() > 0.5 else -1)
        self.orbit_angle = np.random.uniform(0, 2 * math.pi)
        
        self.focus_factor = 0.0
        self.wake_factor = 0.0
        
        self.glow_scale = np.random.uniform(2.0, 3.0)
    
    def _precompute_colors(self, hue, saturation):
        hsv_color = np.uint8([[[int(hue), int(saturation * 255), 255]]])
        bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
        self.base_bgr = np.array([bgr_color[0], bgr_color[1], bgr_color[2]], dtype=np.float32)
    
    def update(self, time, hand_x=None, hand_y=None, flow_field=None, highlight_intensity=0.0, state_intensity=1.0):
        if hand_x is not None and hand_y is not None:
            dx = hand_x - self.x
            dy = hand_y - self.y
            distance = math.sqrt(dx * dx + dy * dy)
            
            focus_radius = 350.0
            if distance < focus_radius:
                self.focus_factor = (1.0 - distance / focus_radius) ** 1.3
            else:
                self.focus_factor = 0.0
            
            wake_radius = 200.0
            if distance < wake_radius:
                self.wake_factor = (1.0 - distance / wake_radius) ** 2.0
                falloff = self.wake_factor
                
                self.orbit_angle += self.orbit_speed * (1 + falloff * 1.0)
                dynamic_radius = self.orbit_radius * (0.7 + 0.3 * (1 - falloff))
                orbit_x = math.cos(self.orbit_angle) * dynamic_radius
                orbit_y = math.sin(self.orbit_angle) * dynamic_radius
                
                target_x = hand_x + orbit_x
                target_y = hand_y + orbit_y
                
                attract_strength = 0.008 * (1.0 + (1.0 - self.depth) * 0.3) * state_intensity
                self.vx += (target_x - self.x) * attract_strength * falloff
                self.vy += (target_y - self.y) * attract_strength * falloff
                
                speed_multiplier = 1.0 + 1.0 * falloff * state_intensity
                self.vx *= speed_multiplier
                self.vy *= speed_multiplier
            else:
                self.wake_factor = 0.0
        else:
            self.focus_factor = 0.0
            self.wake_factor = 0.0
        
        focus_boost = self.focus_factor * 0.6
        self.brightness = self.base_brightness + focus_boost + self.wake_factor * 0.3 + highlight_intensity * 0.2
        self.alpha = (self.base_alpha + self.focus_factor * 0.25 + self.wake_factor * 0.35) * (1.0 + highlight_intensity * 0.2) * state_intensity
        self.size = self.base_size * (1.0 + self.focus_factor * 0.8 + self.wake_factor * 0.5)
        
        damp = 0.97
        self.vx = self.vx * damp + self.base_vx * (1 - damp)
        self.vy = self.vy * damp + self.base_vy * (1 - damp)
        
        if flow_field is not None:
            fx, fy = flow_field.get_influence('particle')
            self.vx += fx
            self.vy += fy
        
        self.x += self.vx
        self.y += self.vy
        
        if self.x < -20:
            self.x = self.width + 20
        elif self.x > self.width + 20:
            self.x = -20
        
        if self.y < -20:
            self.y = self.height + 20
        elif self.y > self.height + 20:
            self.y = -20
        
        flicker = 0.88 + 0.12 * math.sin(time * 0.0025 + self.phase)
        self.alpha *= flicker
    
    def draw(self, frame):
        alpha = max(0.03, min(1.0, self.alpha))
        brightness = max(0.5, min(1.1, self.brightness))
        
        color = (int(self.base_bgr[0] * brightness), 
                 int(self.base_bgr[1] * brightness), 
                 int(self.base_bgr[2] * brightness))
        
        effective_size = max(1, int(self.size))
        
        outer_radius = effective_size * int(self.glow_scale * (1.5 + self.wake_factor * 1.5))
        outer_alpha = int(alpha * 0.15 * (1.0 + self.wake_factor * 0.5))
        if outer_alpha > 3 and outer_radius > 1:
            outer_color = (int(self.base_bgr[0] * brightness * 0.6 * alpha), 
                           int(self.base_bgr[1] * brightness * 0.6 * alpha), 
                           int(self.base_bgr[2] * brightness * 0.6 * alpha))
            cv2.circle(frame, (int(self.x), int(self.y)), outer_radius, outer_color, -1)
        
        mid_radius = effective_size * int(1.8 * (1.0 + self.wake_factor * 0.8))
        mid_alpha = int(alpha * 0.35 * (1.0 + self.wake_factor * 0.5))
        if mid_alpha > 5 and mid_radius > 1:
            mid_color = (int(self.base_bgr[0] * brightness * 0.8 * alpha), 
                         int(self.base_bgr[1] * brightness * 0.8 * alpha), 
                         int(self.base_bgr[2] * brightness * 0.8 * alpha))
            cv2.circle(frame, (int(self.x), int(self.y)), mid_radius, mid_color, -1)
        
        core_color = (int(self.base_bgr[0] * brightness * alpha + 100 * alpha * self.wake_factor), 
                      int(self.base_bgr[1] * brightness * alpha + 100 * alpha * self.wake_factor), 
                      int(self.base_bgr[2] * brightness * alpha + 100 * alpha * self.wake_factor))
        cv2.circle(frame, (int(self.x), int(self.y)), effective_size, core_color, -1)


class StarParticle:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        r = np.random.random()
        if r < 0.7:
            self.type = 'spread'
        elif r < 0.9:
            self.type = 'stay'
        else:
            self.type = 'far'
        
        angle = np.random.uniform(0, 2 * math.pi)
        base_speed = np.random.uniform(1.0, 4.0)
        
        if self.type == 'spread':
            self.vx = math.cos(angle) * base_speed * np.random.uniform(0.5, 1.5)
            self.vy = math.sin(angle) * base_speed * np.random.uniform(0.5, 1.2) + 0.8
            self.life = np.random.uniform(150, 250)
            self.size = np.random.uniform(1.0, 2.5)
        elif self.type == 'stay':
            self.vx = math.cos(angle) * base_speed * 0.2
            self.vy = math.sin(angle) * base_speed * 0.2 + 0.3
            self.life = np.random.uniform(100, 200)
            self.size = np.random.uniform(0.8, 2.0)
        else:
            self.vx = math.cos(angle) * base_speed * np.random.uniform(1.2, 2.5)
            self.vy = math.sin(angle) * base_speed * np.random.uniform(1.0, 2.0) + 0.5
            self.life = np.random.uniform(180, 300)
            self.size = np.random.uniform(1.5, 3.5)
        
        self.max_life = self.life
        self.base_size = self.size
        
        cr = np.random.random()
        if cr < 0.25:
            hue = 0
            saturation = 0.0
        elif cr < 0.5:
            hue = np.random.uniform(100, 130)
            saturation = np.random.uniform(0.2, 0.5)
        elif cr < 0.7:
            hue = np.random.uniform(75, 100)
            saturation = np.random.uniform(0.25, 0.55)
        elif cr < 0.85:
            hue = np.random.uniform(140, 160)
            saturation = np.random.uniform(0.15, 0.4)
        else:
            special_r = np.random.random()
            if special_r < 0.33:
                hue = np.random.uniform(20, 40)
                saturation = np.random.uniform(0.4, 0.7)
            elif special_r < 0.66:
                hue = np.random.uniform(180, 210)
                saturation = np.random.uniform(0.35, 0.6)
            else:
                hue = np.random.uniform(95, 115)
                saturation = np.random.uniform(0.35, 0.6)
        
        brightness = np.random.uniform(0.7, 1.0)
        hsv_color = np.uint8([[[int(hue), int(saturation * 255), int(brightness * 255)]]])
        bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
        self.color = (int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2]))
        
        self.phase = np.random.uniform(0, 2 * math.pi)
    
    def update(self, flow_field=None):
        self.vx *= 0.992
        self.vy *= 0.992
        
        if flow_field is not None:
            fx, fy = flow_field.get_influence('star_particle')
            self.vx += fx
            self.vy += fy
        
        self.x += self.vx
        self.y += self.vy
        
        self.life -= 1
        
        life_ratio = self.life / self.max_life
        self.size = self.base_size * life_ratio
        
        return self.life > 0 and self.size > 0.3
    
    def draw(self, frame):
        effective_size = max(1, int(self.size))
        cv2.circle(frame, (int(self.x), int(self.y)), effective_size, self.color, -1)