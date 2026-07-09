import math
import numpy as np
import cv2


class OceanVisualizer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        self._base_gradient = self._create_base_gradient()
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
    
    def _create_base_gradient(self):
        gradient = np.zeros((self.height, self.width, 3), dtype=np.float32)
        for y in range(self.height):
            t = y / self.height
            dark_blue = np.array([30, 8, 2], dtype=np.float32)
            mid_blue = np.array([55, 18, 5], dtype=np.float32)
            light_blue = np.array([80, 30, 10], dtype=np.float32)
            if t < 0.5:
                color = dark_blue + (mid_blue - dark_blue) * (t * 2)
            else:
                color = mid_blue + (light_blue - mid_blue) * ((t - 0.5) * 2)
            gradient[y, :] = color
        return gradient
    
    def create_background(self, breath_factor, hand_x=None, hand_y=None, hand_visible=False):
        frame = self._base_gradient.copy()
        
        scatter_intensity = (0.05 + 0.05 * breath_factor)
        for y in range(self.height):
            top_ratio = 1.0 - (y / self.height) ** 1.5
            if top_ratio > 0.01:
                scatter_value = int(20 * top_ratio * scatter_intensity)
                frame[y, :, 0] = np.clip(frame[y, :, 0].astype(np.int32) + scatter_value, 0, 255)
                frame[y, :, 1] = np.clip(frame[y, :, 1].astype(np.int32) + int(scatter_value * 0.6), 0, 255)
        
        if hand_visible and hand_x is not None and hand_y is not None:
            cx, cy = int(hand_x), int(hand_y)
            if self._spot_cache is None or self._spot_cache_xy is None or \
               abs(self._spot_cache_xy[0] - cx) > 8 or abs(self._spot_cache_xy[1] - cy) > 8:
                dx = self._lr_xx - hand_x
                dy = self._lr_yy - hand_y
                dist = np.sqrt(dx * dx + dy * dy)
                spot_mask = np.clip(1.0 - dist / 350.0, 0, 1)
                spot_mask = spot_mask ** 1.4
                self._spot_cache = cv2.resize(spot_mask, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
                self._spot_cache_xy = (cx, cy)
            
            spot_intensity = 0.65 + 0.12 * breath_factor
            spot_color = np.array([90, 50, 25], dtype=np.float32)
            for c in range(3):
                frame[:, :, c] += spot_color[c] * self._spot_cache * spot_intensity
            
            if self._outer_spot_cache is None or abs(self._outer_spot_cache_xy[0] - cx) > 8 or abs(self._outer_spot_cache_xy[1] - cy) > 8:
                dist2 = np.sqrt(dx * dx + dy * dy)
                outer_spot_mask = np.clip(1.0 - dist2 / 450.0, 0, 1)
                outer_spot_mask = outer_spot_mask ** 2.0
                self._outer_spot_cache = cv2.resize(outer_spot_mask, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
                self._outer_spot_cache_xy = (cx, cy)
            
            outer_color = np.array([40, 30, 15], dtype=np.float32)
            for c in range(3):
                frame[:, :, c] += outer_color[c] * self._outer_spot_cache * (0.3 + 0.1 * breath_factor)
        
        if self._vignette_mask is None:
            dx = self._lr_xx - self.width / 2
            dy = self._lr_yy - self.height / 2
            dist = np.sqrt(dx * dx + dy * dy)
            max_dist = np.sqrt((self._lr_w/2)**2 + (self._lr_h/2)**2) * 0.9
            self._vignette_mask = np.clip(1.0 - (dist / max_dist) ** 3.5, 0.75, 1.0)
            self._vignette_mask = cv2.resize(self._vignette_mask, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
        
        for c in range(3):
            frame[:, :, c] = (frame[:, :, c] * self._vignette_mask).astype(np.uint8)
        
        frame *= (0.90 + 0.10 * breath_factor)
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        return frame