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
        self.depth = depth  # 0=前景, 1=后景
        
        self.x = np.random.uniform(0, width)
        self.y = np.random.uniform(0, height)
        
        speed_factor = 1.0 + (1.0 - depth) * 1.5
        self.base_vx = np.random.uniform(-0.15, 0.15) * speed_factor
        self.base_vy = np.random.uniform(-0.15, 0.15) * speed_factor - 0.05 * (1.0 - depth)
        self.vx = self.base_vx
        self.vy = self.base_vy
        
        size_min = 1.0 + (1.0 - depth) * 4.0
        size_max = 2.0 + (1.0 - depth) * 5.0
        self.base_size = np.random.uniform(size_min, size_max)
        self.size = self.base_size
        
        alpha_min = 0.08 + (1.0 - depth) * 0.15
        alpha_max = 0.2 + (1.0 - depth) * 0.25
        self.base_alpha = np.random.uniform(alpha_min, alpha_max)
        self.alpha = self.base_alpha
        
        self.phase = np.random.uniform(0, 2 * math.pi)
        
        color_choice = np.random.randint(0, 3)
        if color_choice == 0:
            self.hue = 0
            self.saturation = 0.0
        elif color_choice == 1:
            self.hue = np.random.uniform(100, 125)
            self.saturation = np.random.uniform(0.4, 0.7)
        else:
            self.hue = np.random.uniform(85, 105)
            self.saturation = np.random.uniform(0.5, 0.8)
        
        self.base_brightness = np.random.uniform(0.6, 0.9)
        self.brightness = self.base_brightness
        
        self.orbit_radius = np.random.uniform(50, 120)
        self.orbit_speed = np.random.uniform(0.002, 0.006) * (1 if np.random.random() > 0.5 else -1)
        self.orbit_angle = np.random.uniform(0, 2 * math.pi)
        
        self.focus_factor = 0.0
        self.wake_factor = 0.0
    
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
        
        glow_intensity = self.focus_factor * 0.5 + self.wake_factor * 0.5
        if glow_intensity > 0.1:
            glow_size = int(self.size * (1.5 + glow_intensity * 2))
            glow_alpha = int(alpha * glow_intensity * 80)
            if glow_alpha > 5:
                glow_color = tuple([min(255, int(c + 100 * glow_intensity)) for c in color])
                overlay = frame.copy()
                cv2.circle(overlay, (int(self.x), int(self.y)), glow_size, glow_color, -1)
                cv2.addWeighted(overlay, glow_alpha / 255.0, frame, 1 - glow_alpha / 255.0, 0, frame)
        
        core_color = tuple([min(255, int(c * alpha + 128 * alpha * self.wake_factor)) for c in color])
        cv2.circle(frame, (int(self.x), int(self.y)), max(1, int(self.size)), core_color, -1)


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
        self.trail_particles = []
        
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
        
        self.current_center_x += (self.target_center_x - self.current_center_x) * 0.02
        self.current_center_y += (self.target_center_y - self.current_center_y) * 0.02
        
        self.orbit_angle += self.orbit_speed
        self.time = time
        
        noise = np.random.uniform(-0.05, 0.05)
        noisy_radius = self.orbit_radius * (1 + noise * 0.1)
        
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
        
        self.alpha += (self.target_alpha - self.alpha) * 0.02
        
        if self.is_starfish and self.alpha > 0.3:
            if time % 4 == 0 and len(self.trail_particles) < 15:
                trail_x = self.x - math.cos(self.angle) * self.size * 0.8
                trail_y = self.y - math.sin(self.angle) * self.size * 0.8
                self.trail_particles.append({
                    'x': trail_x,
                    'y': trail_y,
                    'alpha': 0.8,
                    'size': np.random.uniform(2, 4),
                    'color': [(255, 255, 255), (200, 220, 255), (150, 200, 255)][np.random.randint(0, 3)]
                })
            
            for p in self.trail_particles:
                p['x'] -= self.vx * 0.5
                p['y'] -= self.vy * 0.5
                p['alpha'] -= 0.02
            
            self.trail_particles = [p for p in self.trail_particles if p['alpha'] > 0]
    
    def draw(self, frame):
        if self.alpha <= 0.01:
            return
        
        alpha = max(0.01, min(1.0, self.alpha))
        alpha_int = int(alpha * 255)
        
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
        cv2.circle(frame, (eye_x, eye_y), 2, (255, 255, 255), -1)
        cv2.circle(frame, (eye_x, eye_y), 1, (0, 0, 0), -1)
        
        for p in self.trail_particles:
            p_alpha = int(p['alpha'] * alpha * 255)
            p_color = tuple([int(c * p['alpha'] * alpha) for c in p['color']])
            cv2.circle(frame, (int(p['x']), int(p['y'])), int(p['size']), p_color, -1)


class OceanAura:
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        
        # 3层景深粒子
        self.particles = []
        # 前景层（离镜头近）：35个，大、亮、快
        for _ in range(35):
            self.particles.append(Particle(width, height, depth=np.random.uniform(0.0, 0.3)))
        # 中景层：50个，中等
        for _ in range(50):
            self.particles.append(Particle(width, height, depth=np.random.uniform(0.3, 0.7)))
        # 后景层（离镜头远）：45个，小、暗、慢
        for _ in range(45):
            self.particles.append(Particle(width, height, depth=np.random.uniform(0.7, 1.0)))
        
        self.fishes = [Fish(width, height) for _ in range(20)]
        starfish_indices = np.random.choice(20, 3, replace=False)
        for idx in starfish_indices:
            self.fishes[idx].is_starfish = True
        self.time = 0
        self.hand_x = None
        self.hand_y = None
        self.smooth_hand_x = width // 2
        self.smooth_hand_y = height // 2
        self.hand_visible = False
        self.detector = None
        self.use_tasks_api = False
    
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
        frame = np.zeros((self.height, self.width, 3), dtype=np.float32)
        
        for y in range(self.height):
            t = y / self.height
            dark_blue = np.array([40, 12, 3], dtype=np.float32)
            mid_blue = np.array([70, 25, 8], dtype=np.float32)
            light_blue = np.array([100, 40, 15], dtype=np.float32)
            
            if t < 0.5:
                color = dark_blue + (mid_blue - dark_blue) * (t * 2)
            else:
                color = mid_blue + (light_blue - mid_blue) * ((t - 0.5) * 2)
            
            frame[y, :] = color
        
        # 聚光效果（手附近更亮）
        if self.hand_visible:
            # 生成径向渐变蒙版
            y_coords = np.linspace(0, self.height - 1, self.height)
            x_coords = np.linspace(0, self.width - 1, self.width)
            xx, yy = np.meshgrid(x_coords, y_coords)
            
            dx = xx - self.smooth_hand_x
            dy = yy - self.smooth_hand_y
            dist = np.sqrt(dx * dx + dy * dy)
            
            # 聚光半径和强度
            spot_radius = 280.0
            spot_intensity = 0.35 + 0.1 * breath_factor
            
            # 平滑的径向渐变（边缘柔和）
            spot_mask = np.clip(1.0 - dist / spot_radius, 0, 1)
            spot_mask = spot_mask ** 1.8  # 让中心更亮，边缘更柔和
            
            # 添加到背景（亮蓝色调的聚光）
            spot_color = np.array([60, 30, 15], dtype=np.float32)
            for c in range(3):
                frame[:, :, c] += spot_color[c] * spot_mask * spot_intensity
        
        # 整体呼吸感
        frame *= (0.92 + 0.08 * breath_factor)
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        return frame
    
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
                            if self.time % 30 == 0:
                                print(f"Hand detected (tasks): ({self.hand_x:.1f}, {self.hand_y:.1f})")
                                sys.stdout.flush()
                        else:
                            self.hand_x = None
                            self.hand_y = None
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
                            if self.time % 30 == 0:
                                print(f"Hand detected (solutions): ({self.hand_x:.1f}, {self.hand_y:.1f})")
                        else:
                            self.hand_x = None
                            self.hand_y = None
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
                
                for fish in self.fishes:
                    fish.update(self.time, self.hand_x, self.hand_y)
                    fish.draw(frame)
                
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