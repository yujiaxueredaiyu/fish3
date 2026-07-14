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
        
        self._precompute_scatter()
    
    def _precompute_scatter(self):
        y = np.arange(self.height)
        top_ratio = 1.0 - (y / self.height) ** 1.5
        top_ratio[top_ratio <= 0.01] = 0.0
        self._scatter_base = np.zeros((self.height, self.width, 3), dtype=np.float32)
        self._scatter_base[:, :, 0] = top_ratio[:, None] * 20
        self._scatter_base[:, :, 1] = top_ratio[:, None] * 20 * 0.6
    
    def _create_base_gradient(self):
        gradient = np.zeros((self.height, self.width, 3), dtype=np.float32)
        y = np.arange(self.height) / self.height
        t = y.copy()
        mask_low = t < 0.5
        mask_high = ~mask_low
        dark_blue = np.array([30, 8, 2], dtype=np.float32)
        mid_blue = np.array([55, 18, 5], dtype=np.float32)
        light_blue = np.array([80, 30, 10], dtype=np.float32)
        color = np.zeros((self.height, 3), dtype=np.float32)
        color[mask_low] = dark_blue + (mid_blue - dark_blue) * (t[mask_low, None] * 2)
        color[mask_high] = mid_blue + (light_blue - mid_blue) * ((t[mask_high, None] - 0.5) * 2)
        gradient[:] = color[:, None, :]
        return gradient
    
    def create_background(self, breath_factor, hand_x=None, hand_y=None, hand_visible=False, highlight_intensity=0.0, state_intensity=1.0):
        frame = self._base_gradient.copy()
        
        brightness_multiplier = 0.4 + 0.6 * state_intensity
        scatter_intensity = (0.05 + 0.05 * breath_factor) * (1.0 + highlight_intensity * 0.2) * brightness_multiplier
        frame[:, :, :2] += self._scatter_base[:, :, :2] * scatter_intensity
        
        if hand_visible and hand_x is not None and hand_y is not None:
            cx, cy = int(hand_x), int(hand_y)
            
            dx = self._lr_xx - hand_x
            dy = self._lr_yy - hand_y
            dist = np.sqrt(dx * dx + dy * dy)
            
            highlight_radius_mult = 1.0 + highlight_intensity * 0.8
            highlight_decay_mult = 1.0 - highlight_intensity * 0.3
            
            current_inner_radius = 280.0 * highlight_radius_mult
            current_outer_radius = 500.0 * highlight_radius_mult
            
            cache_key_inner = (cx, cy, round(current_inner_radius))
            if self._spot_cache is None or self._spot_cache_xy is None or self._spot_cache_xy != cache_key_inner:
                inner_mask = np.clip(1.0 - dist / current_inner_radius, 0, 1)
                inner_mask = inner_mask ** (1.2 * highlight_decay_mult)
                self._spot_cache = cv2.resize(inner_mask, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
                self._spot_cache_xy = cache_key_inner
            
            inner_intensity = (0.70 + 0.15 * breath_factor) * (1.0 + highlight_intensity * 0.2)
            inner_color = np.array([110, 70, 35], dtype=np.float32)
            frame += inner_color * self._spot_cache[:, :, None] * inner_intensity
            
            cache_key_outer = (cx, cy, round(current_outer_radius))
            if self._outer_spot_cache is None or self._outer_spot_cache_xy is None or self._outer_spot_cache_xy != cache_key_outer:
                outer_mask = np.clip(1.0 - dist / current_outer_radius, 0, 1)
                outer_mask = outer_mask ** (2.5 * highlight_decay_mult)
                self._outer_spot_cache = cv2.resize(outer_mask, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
                self._outer_spot_cache_xy = cache_key_outer
            
            outer_color = np.array([60, 90, 120], dtype=np.float32)
            outer_intensity = (0.4 + 0.15 * breath_factor) * (1.0 + highlight_intensity * 0.2)
            frame += outer_color * self._outer_spot_cache[:, :, None] * outer_intensity
        
        if self._vignette_mask is None:
            dx = self._lr_xx - self.width / 2
            dy = self._lr_yy - self.height / 2
            dist = np.sqrt(dx * dx + dy * dy)
            max_dist = np.sqrt((self._lr_w/2)**2 + (self._lr_h/2)**2) * 0.9
            self._vignette_mask = np.clip(1.0 - (dist / max_dist) ** 3.5, 0.75, 1.0)
            self._vignette_mask = cv2.resize(self._vignette_mask, (self.width, self.height), interpolation=cv2.INTER_LINEAR)
        
        frame = (frame * self._vignette_mask[:, :, None]) * (0.90 + 0.10 * breath_factor)
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        
        return frame