from .audio import AudioSystem
from .flow_field import FlowField
from .config import (
    DEFAULT_WIDTH,
    DEFAULT_HEIGHT,
    PARTICLE_CONFIG,
    FISH_CONFIG,
    SPARKLE_CONFIG,
    STAR_PARTICLE_CONFIG,
    AUDIO_CONFIG,
    VISUAL_CONFIG,
    FLOW_FIELD_CONFIG,
    get_assets_path,
    get_model_path
)

__all__ = [
    'AudioSystem',
    'FlowField',
    'DEFAULT_WIDTH',
    'DEFAULT_HEIGHT',
    'PARTICLE_CONFIG',
    'FISH_CONFIG',
    'SPARKLE_CONFIG',
    'STAR_PARTICLE_CONFIG',
    'AUDIO_CONFIG',
    'VISUAL_CONFIG',
    'FLOW_FIELD_CONFIG',
    'get_assets_path',
    'get_model_path'
]

__version__ = '1.0.0'


def get_particle_class():
    from .particles import Particle
    return Particle


def get_star_particle_class():
    from .particles import StarParticle
    return StarParticle


def get_fish_class():
    from .fish import Fish
    return Fish


def get_hand_detector_class():
    from .hand_detection import HandDetector
    return HandDetector


def get_visualizer_class():
    from .visualization import OceanVisualizer
    return OceanVisualizer


def get_ocean_aura_class():
    from .main import OceanAura
    return OceanAura


def get_main_function():
    from .main import main
    return main
