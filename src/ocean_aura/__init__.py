from .audio import AudioSystem
from .particles import Particle, StarParticle
from .fish import Fish
from .hand_detection import HandDetector
from .visualization import OceanVisualizer
from .flow_field import FlowField
from .main import OceanAura, main
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
    'Particle',
    'StarParticle',
    'Fish',
    'HandDetector',
    'OceanVisualizer',
    'FlowField',
    'OceanAura',
    'main',
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
