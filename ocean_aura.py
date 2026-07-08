import cv2
import numpy as np
import math
import traceback
import sys

try:
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    HAS_MP_TASKS = True
except ImportError:
    HAS_MP_TASKS = False
    print("Warning: MediaPipe tasks module not available")

try:
    from mediapipe.solutions import hands as mp_hands
    HAS_MP_SOLUTIONS = True
except ImportError:
    HAS_MP_SOLUTIONS = False
    print("Warning: MediaPipe solutions module not available")


class Particle:
    def __init__(self, width, height, depth=0.5):
        self.width = width
        self.height = height
        self.depth = depth  # 0=前景最近, 1=后景最远
        
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
            self.hue = 0
            self.saturation = 0.0
        elif r < 0.6:
            self.hue = np.random.uniform(100, 125)
            self.saturation = np.random.uniform(0.15, 0.4)
        else:
            self.hue = np.random.uniform(85, 105)
            self.saturation = np.random.uniform(0.2, 0.45)
        
        self.base_brightness = np.random.uniform(0.65, 0.95)
        self.brightness = self.base_brightness
        
        self.orbit_radius = np.random.uniform(50, 120)
        self.orbit_speed = np.random.uniform(0.0015, 0.004) * (1 if np.random.random() > 0.5 else -1)
        self.orbit_angle = np.random.uniform(0, 2 * math.pi)
        
        self.focus_factor = 0.0
        self.wake_factor = 0.0
        
        self.glow_scale = np.random.uniform(2.0, 3.0)
    
    def update(self, time, hand_x=None, hand_y=None):
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
                self.wake_factor = (1.0 - distance / wake_radius) ** 1.5
                falloff = self.wake_factor
                
                self.orbit_angle += self.orbit_speed * (1 + falloff * 2.5)
                dynamic_radius = self.orbit_radius * (0.4 + 0.6 * (1 - falloff))
                orbit_x = math.cos(self.orbit_angle) * dynamic_radius
                orbit_y = math.sin(self.orbit_angle) * dynamic_radius
                
                target_x = hand_x + orbit_x
                target_y = hand_y + orbit_y
                
                attract_strength = 0.02 * (1.0 + (1.0 - self.depth) * 0.5)
                self.vx += (target_x - self.x) * attract_strength * falloff
                self.vy += (target_y - self.y) * attract_strength * falloff
                
                speed_multiplier = 1.0 + 3.0 * falloff
                self.vx *= speed_multiplier
                self.vy *= speed_multiplier
            else:
                self.wake_factor = 0.0
        else:
            self.focus_factor = 0.0
            self.wake_factor = 0.0
        
        focus_boost = self.focus_factor * 0.6
        self.brightness = self.base_brightness + focus_boost + self.wake_factor * 0.3
        self.alpha = self.base_alpha + self.focus_factor * 0.25 + self.wake_factor * 0.35
        self.size = self.base_size * (1.0 + self.focus_factor * 0.8 + self.wake_factor * 0.5)
        
        damp = 0.97
        self.vx = self.vx * damp + self.base_vx * (1 - damp)
        self.vy = self.vy * damp + self.base_vy * (1 - damp)
        
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
        
        hsv_color = np.uint8([[[int(self.hue), int(self.saturation * 255), int(min(brightness, 1.0) * 255)]]])
        bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
        color = (int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2]))
        
        effective_size = max(1, int(self.size))
        
        outer_radius = effective_size * int(self.glow_scale * (1.5 + self.wake_factor * 1.5))
        outer_alpha = int(alpha * 0.15 * (1.0 + self.wake_factor * 0.5))
        if outer_alpha > 3 and outer_radius > 1:
            outer_color = tuple([min(255, int(c * 0.6)) for c in color])
            cv2.circle(frame, (int(self.x), int(self.y)), outer_radius, outer_color, -1)
        
        mid_radius = effective_size * int(1.8 * (1.0 + self.wake_factor * 0.8))
        mid_alpha = int(alpha * 0.35 * (1.0 + self.wake_factor * 0.5))
        if mid_alpha > 5 and mid_radius > 1:
            mid_color = tuple([min(255, int(c * 0.8)) for c in color])
            cv2.circle(frame, (int(self.x), int(self.y)), mid_radius, mid_color, -1)
        
        core_color = tuple([min(255, int(c * alpha + 100 * alpha * self.wake_factor)) for c in color])
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
    
    def update(self):
        self.vx *= 0.992
        self.vy *= 0.992
        
        self.x += self.vx
        self.y += self.vy
        
        self.life -= 1
        
        life_ratio = self.life / self.max_life
        self.size = self.base_size * life_ratio
        
        return self.life > 0 and self.size > 0.3
    
    def draw(self, frame):
        effective_size = max(1, int(self.size))
        cv2.circle(frame, (int(self.x), int(self.y)), effective_size, self.color, -1)


class Fish:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = np.random.uniform(0, width)
        self.y = np.random.uniform(0, height)
        self.angle = np.random.uniform(0, 2 * math.pi)
        self.speed = np.random.uniform(1.5, 2.5)
        self.orbit_radius = np.random.uniform(100, 140)
        self.orbit_speed = np.random.uniform(0.02, 0.04) * (1 if np.random.random() > 0.5 else -1)
        self.orbit_angle = np.random.uniform(0, 2 * math.pi)
        
        self.size = np.random.uniform(12, 18)
        self.tail_phase = np.random.uniform(0, 2 * math.pi)
        
        color_choice = np.random.randint(0, 4)
        if color_choice == 0:
            self.color = (255, 255, 255)
        elif color_choice == 1:
            self.color = (200, 220, 255)
        elif color_choice == 2:
            self.color = (50, 220, 255)
        else:
            self.color = (180, 185, 200)
        
        self.is_starfish = False
        self.is_dissolve_fish = False
        self.has_appeared = False
        self.trail_particles = []
        self.dissolve_particles = []
        
        self.target_center_x = width // 2
        self.target_center_y = height // 2
        self.current_center_x = width // 2
        self.current_center_y = height // 2
        
        self.alpha = 0.0
        self.target_alpha = 0.0
        self.is_fading = False
    
    def update(self, time, hand_x=None, hand_y=None):
        if hand_x is not None and hand_y is not None:
            self.target_center_x = hand_x
            self.target_center_y = hand_y
            self.target_alpha = 1.0
            self.is_fading = False
        else:
            self.target_alpha = 0.0
            self.is_fading = True
        
        if self.is_fading:
            self.target_center_x += np.random.uniform(-3, 3)
            self.target_center_y += np.random.uniform(-3, 3)
        
        self.current_center_x += (self.target_center_x - self.current_center_x) * 0.02
        self.current_center_y += (self.target_center_y - self.current_center_y) * 0.02
        
        self.orbit_angle += self.orbit_speed
        self.time = time
        
        noise = np.random.uniform(-0.05, 0.05)
        noisy_radius = self.orbit_radius * (1 + noise * 0.1)
        
        if self.is_fading:
            noisy_radius += self.orbit_radius * (1.0 - self.alpha) * 2.0
        
        if self.alpha <= 0.01:
            self.x = np.random.uniform(0, self.width)
            self.y = np.random.uniform(0, self.height)
            self.orbit_angle = np.random.uniform(0, 2 * math.pi)
        
        target_x = self.current_center_x + math.cos(self.orbit_angle) * noisy_radius
        target_y = self.current_center_y + math.sin(self.orbit_angle) * noisy_radius
        
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 1:
            self.vx = (dx / dist) * self.speed
            self.vy = (dy / dist) * self.speed
            self.angle = math.atan2(dy, dx)
        else:
            self.vx = 0
            self.vy = 0
        
        self.x += self.vx
        self.y += self.vy
        
        fade_speed = 0.018 if self.is_fading else 0.02
        self.alpha += (self.target_alpha - self.alpha) * fade_speed
        
        if self.alpha > 0.5:
            self.has_appeared = True
        
        if self.is_starfish and self.alpha > 0.2:
            if time % 3 == 0 and len(self.trail_particles) < 12:
                trail_x = self.x - math.cos(self.angle) * self.size * 0.8
                trail_y = self.y - math.sin(self.angle) * self.size * 0.8
                self.trail_particles.append({
                    'x': trail_x,
                    'y': trail_y,
                    'alpha': 0.9,
                    'size': np.random.uniform(1.5, 3),
                    'color': [(255, 255, 255), (200, 220, 255), (150, 200, 255)][np.random.randint(0, 3)]
                })
            
            for p in self.trail_particles:
                p['x'] -= self.vx * 0.5
                p['y'] -= self.vy * 0.5
                p['alpha'] -= 0.025
            
            self.trail_particles = [p for p in self.trail_particles if p['alpha'] > 0]
        
        if self.is_dissolve_fish and self.is_fading and self.has_appeared and self.alpha < 0.6:
            if time % 5 == 0 and len(self.dissolve_particles) < 6:
                angle = np.random.uniform(0, 2 * math.pi)
                speed = np.random.uniform(0.4, 1.0)
                self.dissolve_particles.append({
                    'x': self.x + np.random.uniform(-self.size * 0.5, self.size * 0.5),
                    'y': self.y + np.random.uniform(-self.size * 0.5, self.size * 0.5),
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'alpha': 0.8,
                    'size': np.random.uniform(1.5, 2.5),
                    'color': (255, 255, 255)
                })
            
            for p in self.dissolve_particles:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['vx'] *= 0.96
                p['vy'] *= 0.96
                p['alpha'] -= 0.012
            
            self.dissolve_particles = [p for p in self.dissolve_particles if p['alpha'] > 0]
    
    def draw(self, frame):
        if self.alpha <= 0.01:
            return
        
        alpha = max(0.01, min(1.0, self.alpha))
        
        body_length = self.size
        body_width = self.size * 0.5
        
        tail_angle = self.angle + math.pi
        tail_swing = math.sin(self.tail_phase + self.time * 0.15) * 0.4
        
        body_points = []
        for i in range(21):
            theta = (i / 20) * math.pi * 2
            bx = math.cos(self.angle + theta) * (body_length if i <= 10 else body_length * 0.3) * 0.5
            by = math.sin(self.angle + theta) * body_width * 0.5
            body_points.append((int(self.x + bx), int(self.y + by)))
        
        body_color = tuple([int(c * alpha) for c in self.color])
        cv2.fillPoly(frame, [np.array(body_points, dtype=np.int32)], body_color)
        
        tail_p1 = (int(self.x - math.cos(self.angle) * body_length * 0.4),
                   int(self.y - math.sin(self.angle) * body_length * 0.4))
        tail_p2 = (int(self.x - math.cos(tail_angle + tail_swing) * body_length * 0.6),
                   int(self.y - math.sin(tail_angle + tail_swing) * body_length * 0.6))
        tail_p3 = (int(self.x - math.cos(tail_angle - tail_swing) * body_length * 0.6),
                   int(self.y - math.sin(tail_angle - tail_swing) * body_length * 0.6))
        
        tail_color = tuple([int(c * alpha * 0.8) for c in self.color])
        cv2.fillPoly(frame, [np.array([tail_p1, tail_p2, tail_p3], dtype=np.int32)], tail_color)
        
        eye_x = int(self.x + math.cos(self.angle) * body_length * 0.3)
        eye_y = int(self.y + math.sin(self.angle) * body_length * 0.15)
        eye_color = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
        cv2.circle(frame, (eye_x, eye_y), 2, eye_color, -1)
        cv2.circle(frame, (eye_x, eye_y), 1, (0, 0, 0), -1)
        
        for p in self.trail_particles:
            p_color = tuple([int(c * p['alpha'] * alpha) for c in p['color']])
            cv2.circle(frame, (int(p['x']), int(p['y'])), int(p['size']), p_color, -1)
        
        for p in self.dissolve_particles:
            p_color = tuple([int(c * p['alpha']) for c in p['color']])
            cv2.circle(frame, (int(p['x']), int(p['y'])), int(p['size']), p_color, -1)


class OceanAura:
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        
        # 预计算背景渐变（只算一次，运行时复用）
        self._base_gradient = np.zeros((height, width, 3), dtype=np.float32)
        for y in range(height):
            t = y / height
            dark_blue = np.array([30, 8, 2], dtype=np.float32)
            mid_blue = np.array([55, 18, 5], dtype=np.float32)
            light_blue = np.array([80, 30, 10], dtype=np.float32)
            if t < 0.5:
                color = dark_blue + (mid_blue - dark_blue) * (t * 2)
            else:
                color = mid_blue + (light_blue - mid_blue) * ((t - 0.5) * 2)
            self._base_gradient[y, :] = color
        
        # 低分辨率网格（1/4缩放，用于环境光和聚光计算）
        self._lr_w = width // 4
        self._lr_h = height // 4
        y_coords = np.linspace(0, height - 1, self._lr_h)
        x_coords = np.linspace(0, width - 1, self._lr_w)
        self._lr_xx, self._lr_yy = np.meshgrid(x_coords, y_coords)
        
        self._spot_cache = None
        self._spot_cache_xy = None
        self._outer_spot_cache = None
        self._outer_spot_cache_xy = None
        self._vignette_mask = None
        
        # 3层景深粒子
        self.particles = []
        for _ in range(40):
            self.particles.append(Particle(width, height, depth=np.random.uniform(0.0, 0.3)))
        for _ in range(55):
            self.particles.append(Particle(width, height, depth=np.random.uniform(0.3, 0.7)))
        for _ in range(60):
            self.particles.append(Particle(width, height, depth=np.random.uniform(0.7, 1.0)))
        
        self.fishes = [Fish(width, height) for _ in range(20)]
        all_indices = np.arange(20)
        np.random.shuffle(all_indices)
        starfish_indices = all_indices[:3]
        for idx in starfish_indices:
            self.fishes[idx].is_starfish = True
        dissolve_indices = all_indices[3:7]
        for idx in dissolve_indices:
            self.fishes[idx].is_dissolve_fish = True
        self.time = 0
        self.hand_x = None
        self.hand_y = None
        self.smooth_hand_x = width // 2
        self.smooth_hand_y = height // 2
        self.hand_visible = False
        self.detector = None
        self.use_tasks_api = False
        
        # 环绕手的小光斑（星星点点）
        self.sparkles = []
        for _ in range(25):
            self.sparkles.append({
                'angle': np.random.uniform(0, 2 * math.pi),
                'radius': np.random.uniform(60, 200),
                'speed': np.random.uniform(0.008, 0.02),
                'size': np.random.uniform(1, 3),
                'brightness': np.random.uniform(0.5, 0.9),
                'phase': np.random.uniform(0, 2 * math.pi),
                'hue': np.random.uniform(0, 120),
                'saturation': np.random.uniform(0.0, 0.3),
            })
        
        # 星光粒子（握拳释放）
        self.star_particles = []
        
        # 握拳检测状态
        self.is_fist = False
        self.was_fist = False
    
    def init_detector(self):
        if HAS_MP_TASKS:
            try:
                base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
                options = vision.HandLandmarkerOptions(
                    base_options=base_options,
                    num_hands=1,
                    min_hand_detection_confidence=0.5,
                    min_hand_presence_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self.detector = vision.HandLandmarker.create_from_options(options)
                self.use_tasks_api = True
                print("Using MediaPipe Tasks API")
                sys.stdout.flush()
                return True
            except Exception as e:
                print(f"Tasks API failed: {e}")
        
        if HAS_MP_SOLUTIONS:
            try:
                self.detector = mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5
                )
                self.use_tasks_api = False
                print("Using MediaPipe Solutions API")
                return True
            except Exception as e:
                print(f"Solutions API failed: {e}")
        
        print("No MediaPipe API available")
        return False
    
    def create_gradient_background(self, breath_factor):
        frame = self._base_gradient.copy()
        
        # 海水散射光：从顶部向下逐渐变暗，透明度5%~10%
        scatter_intensity = (0.05 + 0.05 * breath_factor)
        for y in range(self.height):
            top_ratio = 1.0 - (y / self.height) ** 1.5
            if top_ratio > 0.01:
                scatter_value = int(20 * top_ratio * scatter_intensity)
                frame[y, :, 0] = np.clip(frame[y, :, 0].astype(np.int32) + scatter_value, 0, 255)
                frame[y, :, 1] = np.clip(frame[y, :, 1].astype(np.int32) + int(scatter_value * 0.6), 0, 255)
        
        # 聚光效果：更强更明显
        if self.hand_visible:
            cx, cy = int(self.smooth_hand_x), int(self.smooth_hand_y)
            if self._spot_cache is None or self._spot_cache_xy is None or \
               abs(self._spot_cache_xy[0] - cx) > 8 or abs(self._spot_cache_xy[1] - cy) > 8:
                dx = self._lr_xx - self.smooth_hand_x
                dy = self._lr_yy - self.smooth_hand_y
                dist = np.sqrt(dx * dx + dy * dy)
                spot_mask = np.clip(1.0 - dist / 350.0, 0, 1)
                spot_mask = spot_mask ** 1.4
                self._spot_cache = cv2.resize(spot_mask, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
                self._spot_cache_xy = (cx, cy)
            
            spot_intensity = 0.65 + 0.12 * breath_factor
            spot_color = np.array([90, 50, 25], dtype=np.float32)
            for c in range(3):
                frame[:, :, c] += spot_color[c] * self._spot_cache * spot_intensity
            
            # 第二层柔和光晕
            if self._outer_spot_cache is None or abs(self._outer_spot_cache_xy[0] - cx) > 8 or abs(self._outer_spot_cache_xy[1] - cy) > 8:
                dist2 = np.sqrt(dx * dx + dy * dy)
                outer_spot_mask = np.clip(1.0 - dist2 / 450.0, 0, 1)
                outer_spot_mask = outer_spot_mask ** 2.0
                self._outer_spot_cache = cv2.resize(outer_spot_mask, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
                self._outer_spot_cache_xy = (cx, cy)
            
            outer_color = np.array([40, 30, 15], dtype=np.float32)
            for c in range(3):
                frame[:, :, c] += outer_color[c] * self._outer_spot_cache * (0.3 + 0.1 * breath_factor)
        
        # 暗角效果（Vignette）：四周轻微变暗
        if self._vignette_mask is None:
            dx = self._lr_xx - self.width / 2
            dy = self._lr_yy - self.height / 2
            dist = np.sqrt(dx * dx + dy * dy)
            max_dist = np.sqrt((self._lr_w/2)**2 + (self._lr_h/2)**2) * 0.9
            self._vignette_mask = np.clip(1.0 - (dist / max_dist) ** 3.5, 0.75, 1.0)
            self._vignette_mask = cv2.resize(self._vignette_mask, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
        
        for c in range(3):
            frame[:, :, c] = (frame[:, :, c] * self._vignette_mask).astype(np.uint8)
        
        # 整体呼吸感
        frame *= (0.90 + 0.10 * breath_factor)
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        return frame
    
    def detect_fist(self, landmarks):
        if not landmarks:
            return False
        
        if len(landmarks) < 21:
            return False
        
        def is_finger_folded(tip_idx, pip_idx):
            tip_y = landmarks[tip_idx].y
            pip_y = landmarks[pip_idx].y
            return tip_y > pip_y + 0.02
        
        folded_count = 0
        
        if is_finger_folded(8, 6):
            folded_count += 1
        if is_finger_folded(12, 10):
            folded_count += 1
        if is_finger_folded(16, 14):
            folded_count += 1
        if is_finger_folded(20, 18):
            folded_count += 1
        
        thumb_tip = landmarks[4]
        wrist = landmarks[0]
        thumb_dist = math.sqrt((thumb_tip.x - wrist.x)**2 + (thumb_tip.y - wrist.y)**2)
        if thumb_dist < 0.15:
            folded_count += 1
        
        return folded_count >= 4
    
    def release_starlight(self):
        if self.hand_x is None or self.hand_y is None:
            return
        
        if len(self.star_particles) > 200:
            return
        
        particle_count = np.random.randint(40, 61)
        for _ in range(particle_count):
            self.star_particles.append(StarParticle(self.hand_x, self.hand_y, self.width, self.height))
    
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
        
        if not self.init_detector():
            cv2.destroyAllWindows()
            input("Press Enter to exit...")
            return
        
        try:
            while True:
                self.time += 1
                breath_factor = math.sin(self.time * 0.005)
                
                frame = self.create_gradient_background(breath_factor)
                
                success, camera_frame = cap.read()
                if success:
                    camera_frame_rgb = cv2.cvtColor(camera_frame, cv2.COLOR_BGR2RGB)
                    
                    if self.use_tasks_api:
                        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=camera_frame_rgb)
                        result = self.detector.detect(mp_image)
                        
                        if hasattr(result, 'hand_landmarks') and result.hand_landmarks:
                            landmarks = result.hand_landmarks[0]
                            wrist = landmarks[0]
                            self.hand_x = wrist.x * self.width
                            self.hand_y = wrist.y * self.height
                            
                            self.is_fist = self.detect_fist(landmarks)
                            
                            if self.is_fist and not self.was_fist:
                                self.release_starlight()
                                if self.time % 30 == 0:
                                    print("Fist detected! Releasing starlight")
                            
                            self.was_fist = self.is_fist
                            
                            if self.time % 30 == 0:
                                print(f"Hand detected (tasks): ({self.hand_x:.1f}, {self.hand_y:.1f})")
                                sys.stdout.flush()
                        else:
                            self.hand_x = None
                            self.hand_y = None
                            self.is_fist = False
                            self.was_fist = False
                            if self.time == 10:
                                print("No hand detected")
                                print(f"Result type: {type(result)}")
                                if hasattr(result, 'hand_landmarks'):
                                    print(f"hand_landmarks: {result.hand_landmarks}")
                                sys.stdout.flush()
                    else:
                        result = self.detector.process(camera_frame_rgb)
                        
                        if result.multi_hand_landmarks:
                            landmarks = result.multi_hand_landmarks[0]
                            wrist = landmarks.landmark[0]
                            self.hand_x = wrist.x * self.width
                            self.hand_y = wrist.y * self.height
                            
                            self.is_fist = self.detect_fist(landmarks.landmark)
                            
                            if self.is_fist and not self.was_fist:
                                self.release_starlight()
                            
                            self.was_fist = self.is_fist
                            
                            if self.time % 30 == 0:
                                print(f"Hand detected (solutions): ({self.hand_x:.1f}, {self.hand_y:.1f})")
                        else:
                            self.hand_x = None
                            self.hand_y = None
                            self.is_fist = False
                            self.was_fist = False
                else:
                    self.hand_x = None
                    self.hand_y = None
                    if self.time % 30 == 0:
                        print("Camera read failed")
                
                # 平滑手的位置
                if self.hand_x is not None and self.hand_y is not None:
                    self.hand_visible = True
                    self.smooth_hand_x += (self.hand_x - self.smooth_hand_x) * 0.08
                    self.smooth_hand_y += (self.hand_y - self.smooth_hand_y) * 0.08
                else:
                    self.hand_visible = False
                
                for particle in self.particles:
                    particle.update(self.time, self.hand_x, self.hand_y)
                    particle.draw(frame)
                
                # 环绕手的小光斑（星星点点）
                if self.hand_visible:
                    for sparkle in self.sparkles:
                        sparkle['angle'] += sparkle['speed']
                        flicker = 0.6 + 0.4 * math.sin(self.time * 0.008 + sparkle['phase'])
                        x = self.smooth_hand_x + math.cos(sparkle['angle']) * sparkle['radius']
                        y = self.smooth_hand_y + math.sin(sparkle['angle']) * sparkle['radius']
                        
                        hsv_color = np.uint8([[[int(sparkle['hue']), int(sparkle['saturation'] * 255), int(sparkle['brightness'] * flicker * 255)]]])
                        bgr_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0][0]
                        color = (int(bgr_color[0]), int(bgr_color[1]), int(bgr_color[2]))
                        
                        size = int(sparkle['size'] * flicker)
                        if size > 0 and x > 0 and x < self.width and y > 0 and y < self.height:
                            cv2.circle(frame, (int(x), int(y)), size, color, -1)
                            outer_size = size * 2
                            outer_color = tuple([min(255, int(c * 0.4)) for c in color])
                            cv2.circle(frame, (int(x), int(y)), outer_size, outer_color, -1)
                
                for fish in self.fishes:
                    fish.update(self.time, self.hand_x, self.hand_y)
                    fish.draw(frame)
                
                # 星光粒子（握拳释放）
                self.star_particles = [p for p in self.star_particles if p.update()]
                for p in self.star_particles:
                    p.draw(frame)
                
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


if __name__ == '__main__':
    try:
        app = OceanAura()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        input("Press Enter to exit...")