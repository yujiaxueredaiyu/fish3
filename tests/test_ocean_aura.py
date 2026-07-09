import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ocean_aura import OceanAura, AudioSystem, HandDetector


def test_imports():
    print("Testing imports...")
    assert OceanAura is not None
    assert AudioSystem is not None
    assert HandDetector is not None
    print("✓ All imports successful")


def test_audio_system():
    print("\nTesting audio system...")
    audio = AudioSystem()
    assert audio is not None
    assert hasattr(audio, 'start_ambient')
    assert hasattr(audio, 'play_sparkle')
    assert hasattr(audio, 'play_bubble')
    assert hasattr(audio, 'stop')
    print("✓ Audio system initialization successful")


if __name__ == '__main__':
    test_imports()
    test_audio_system()
    print("\n✅ All tests passed!")
