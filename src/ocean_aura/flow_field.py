import math
import numpy as np

from .config import FLOW_FIELD_CONFIG


class FlowField:
    def __init__(self):
        self.config = FLOW_FIELD_CONFIG
        self.current_vx = 0.0
        self.current_vy = 0.0
        self.target_vx = 0.0
        self.target_vy = 0.0
        
        self.change_interval = np.random.uniform(
            self.config['min_change_interval'],
            self.config['max_change_interval']
        )
        self.time_since_last_change = 0.0
        
        self._generate_new_target()
    
    def _generate_new_target(self):
        angle = np.random.uniform(0, 2 * math.pi)
        speed = np.random.uniform(0.3, 1.0) * self.config['max_speed']
        self.target_vx = math.cos(angle) * speed
        self.target_vy = math.sin(angle) * speed
        
        self.change_interval = np.random.uniform(
            self.config['min_change_interval'],
            self.config['max_change_interval']
        )
        self.time_since_last_change = 0.0
    
    def update(self, delta_time=1.0 / 30.0):
        self.time_since_last_change += delta_time
        
        if self.time_since_last_change >= self.change_interval:
            self._generate_new_target()
        
        smooth = self.config['smooth_factor'] * 30 * delta_time
        self.current_vx += (self.target_vx - self.current_vx) * smooth
        self.current_vy += (self.target_vy - self.current_vy) * smooth
    
    def get_current_vector(self):
        return self.current_vx, self.current_vy
    
    def get_influence(self, influence_type):
        vx, vy = self.get_current_vector()
        if influence_type == 'particle':
            return vx * self.config['particle_influence'], vy * self.config['particle_influence']
        elif influence_type == 'star_particle':
            return vx * self.config['star_particle_influence'], vy * self.config['star_particle_influence']
        elif influence_type == 'fish':
            return vx * self.config['fish_influence'], vy * self.config['fish_influence']
        return vx, vy
