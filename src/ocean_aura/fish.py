import math
import numpy as np
import cv2


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
            self.target_center_x += np.random.uniform(-8, 8)
            self.target_center_y += np.random.uniform(-8, 8)
        
        self.current_center_x += (self.target_center_x - self.current_center_x) * 0.02
        self.current_center_y += (self.target_center_y - self.current_center_y) * 0.02
        
        self.orbit_angle += self.orbit_speed
        self.time = time
        
        noise = np.random.uniform(-0.05, 0.05)
        noisy_radius = self.orbit_radius * (1 + noise * 0.1)
        
        if self.is_fading:
            noisy_radius += self.orbit_radius * (1.0 - self.alpha) * 3.0
        
        target_x = self.current_center_x + math.cos(self.orbit_angle) * noisy_radius
        target_y = self.current_center_y + math.sin(self.orbit_angle) * noisy_radius
        
        if self.is_fading:
            scatter_angle = np.random.uniform(0, 2 * math.pi)
            scatter_dist = (1.0 - self.alpha) * self.orbit_radius * 0.5
            target_x += math.cos(scatter_angle) * scatter_dist
            target_y += math.sin(scatter_angle) * scatter_dist
        
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        move_speed = self.speed * (1.0 + (1.0 - self.alpha) * 0.5)
        
        if dist > 1:
            self.vx = (dx / dist) * move_speed
            self.vy = (dy / dist) * move_speed
            self.angle = math.atan2(dy, dx)
        else:
            self.vx = 0
            self.vy = 0
        
        self.x += self.vx
        self.y += self.vy
        
        if self.alpha <= 0.01:
            self.x = np.random.uniform(0, self.width)
            self.y = np.random.uniform(0, self.height)
            self.orbit_angle = np.random.uniform(0, 2 * math.pi)
        
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