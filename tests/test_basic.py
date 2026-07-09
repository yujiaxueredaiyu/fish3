import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_config():
    print("Testing config...")
    import ocean_aura.config as config
    
    assert config.DEFAULT_WIDTH == 1280
    assert config.DEFAULT_HEIGHT == 720
    assert callable(config.get_assets_path)
    print("✓ Config test successful")


def test_flow_field():
    print("\nTesting flow field...")
    import ocean_aura.flow_field as flow_field
    
    ff = flow_field.FlowField()
    assert ff is not None
    vx, vy = ff.get_current_vector()
    assert isinstance(vx, (int, float))
    assert isinstance(vy, (int, float))
    print("✓ Flow field test successful")


def test_audio_system():
    print("\nTesting audio system...")
    import ocean_aura.audio as audio
    
    asys = audio.AudioSystem()
    assert asys is not None
    assert hasattr(asys, 'start_ambient')
    assert hasattr(asys, 'play_sparkle')
    assert hasattr(asys, 'play_bubble')
    assert hasattr(asys, 'stop')
    print("✓ Audio system test successful")


if __name__ == '__main__':
    test_config()
    test_flow_field()
    test_audio_system()
    print("\n✅ All tests passed!")
