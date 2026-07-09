import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ocean_aura import OceanAura, AudioSystem, HandDetector, FlowField


def test_imports():
    print("Testing imports...")
    assert OceanAura is not None
    assert AudioSystem is not None
    assert HandDetector is not None
    assert FlowField is not None
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


def test_flow_field():
    print("\nTesting flow field...")
    flow_field = FlowField()
    assert flow_field is not None
    vx, vy = flow_field.get_current_vector()
    assert isinstance(vx, (int, float))
    assert isinstance(vy, (int, float))
    print("✓ Flow field initialization successful")


def test_audio_system_skip_on_non_windows():
    print("\nTesting audio system on non-Windows...")
    import sys
    if sys.platform != 'win32':
        audio = AudioSystem()
        assert not audio.enabled
        print("✓ Audio system correctly disabled on non-Windows")
    else:
        print("✓ Skipping - running on Windows")


if __name__ == '__main__':
    test_imports()
    test_audio_system()
    test_flow_field()
    test_audio_system_skip_on_non_windows()
    print("\n✅ All tests passed!")
