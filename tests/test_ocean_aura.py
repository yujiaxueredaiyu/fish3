import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_config():
    print("Testing config...")
    from ocean_aura.config import DEFAULT_WIDTH, DEFAULT_HEIGHT, get_assets_path
    assert DEFAULT_WIDTH == 1280
    assert DEFAULT_HEIGHT == 720
    assert callable(get_assets_path)
    print("✓ Config test successful")


def test_flow_field():
    print("\nTesting flow field...")
    from ocean_aura.flow_field import FlowField
    flow_field = FlowField()
    assert flow_field is not None
    vx, vy = flow_field.get_current_vector()
    assert isinstance(vx, (int, float))
    assert isinstance(vy, (int, float))
    
    flow_field.update()
    vx2, vy2 = flow_field.get_current_vector()
    assert isinstance(vx2, (int, float))
    assert isinstance(vy2, (int, float))
    
    infl_vx, infl_vy = flow_field.get_influence('particle')
    assert isinstance(infl_vx, (int, float))
    assert isinstance(infl_vy, (int, float))
    print("✓ Flow field test successful")


def test_audio_system():
    print("\nTesting audio system...")
    from ocean_aura.audio import AudioSystem
    audio = AudioSystem()
    assert audio is not None
    assert hasattr(audio, 'start_ambient')
    assert hasattr(audio, 'play_sparkle')
    assert hasattr(audio, 'play_bubble')
    assert hasattr(audio, 'stop')
    print("✓ Audio system test successful")


if __name__ == '__main__':
    test_config()
    test_flow_field()
    test_audio_system()
    print("\n✅ All tests passed!")
