import os

DEFAULT_WIDTH = 1280
DEFAULT_HEIGHT = 720

PARTICLE_CONFIG = {
    'foreground_count': 40,
    'midground_count': 55,
    'background_count': 60,
    'focus_radius': 350.0,
    'wake_radius': 200.0,
    'max_particles': 200
}

FISH_CONFIG = {
    'total_count': 20,
    'starfish_count': 3,
    'dissolve_fish_count': 4,
    'orbit_radius_min': 100,
    'orbit_radius_max': 140,
    'speed_min': 1.5,
    'speed_max': 2.5,
    'fade_speed': 0.018,
    'appear_speed': 0.02,
    'max_trail_particles': 12,
    'max_dissolve_particles': 6
}

SPARKLE_CONFIG = {
    'count': 0,
    'radius_min': 60,
    'radius_max': 200,
    'speed_min': 0.008,
    'speed_max': 0.02,
    'size_min': 1,
    'size_max': 3
}

STAR_PARTICLE_CONFIG = {
    'min_count': 40,
    'max_count': 60,
    'max_total': 200
}

AUDIO_CONFIG = {
    'ambient_volume': 0.20,
    'sparkle_volume': 0.40,
    'bubble_volume': 0.20,
    'bubble_cooldown': 0.5,
    'fade_in_duration': 1.5
}

VISUAL_CONFIG = {
    'breath_speed': 0.005,
    'hand_smooth_factor': 0.08,
    'vignette_strength': 3.5,
    'vignette_min': 0.75
}

FLOW_FIELD_CONFIG = {
    'min_change_interval': 8,
    'max_change_interval': 15,
    'max_speed': 0.15,
    'smooth_factor': 0.015,
    'particle_influence': 0.15,
    'star_particle_influence': 0.10,
    'fish_influence': 0.05
}


def get_assets_path():
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, 'assets')


def get_model_path(model_name='hand_landmarker.task'):
    return model_name
