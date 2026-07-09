import numpy as np
import wave
import struct

SAMPLE_RATE = 44100

def generate_ocean_ambient():
    duration = 10.0
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples)
    
    wave_data = np.zeros(samples)
    
    # 低频背景
    base_freq = 40
    base_amp = 0.15
    wave_data += base_amp * np.sin(2 * np.pi * base_freq * t) * np.exp(-t * 0.05)
    
    # 水流声模拟（粉红噪音）
    noise = np.random.randn(samples) * 0.08
    noise = np.cumsum(noise) * 0.001
    wave_data += noise
    
    # 空灵氛围（长音）
    for i in range(3):
        freq = 200 + i * 150 + np.random.uniform(-10, 10)
        amp = 0.03 / (i + 1)
        wave_data += amp * np.sin(2 * np.pi * freq * t) * np.sin(t * 0.5 + i)
    
    # 轻微气泡声
    bubble_count = 15
    for _ in range(bubble_count):
        start = int(np.random.uniform(0, samples))
        bubble_duration = int(np.random.uniform(0.05, 0.2) * SAMPLE_RATE)
        end = min(start + bubble_duration, samples)
        bubble_t = np.linspace(0, 1, end - start)
        bubble_freq = 400 + np.random.uniform(200, 400)
        bubble_amp = 0.02 * np.exp(-bubble_t * 8)
        wave_data[start:end] += bubble_amp * np.sin(2 * np.pi * bubble_freq * bubble_t * 5)
    
    # 归一化
    max_val = np.max(np.abs(wave_data))
    if max_val > 0:
        wave_data = wave_data / max_val * 1.0
    
    return wave_data

def generate_sparkle():
    duration = 0.6
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples)
    
    wave_data = np.zeros(samples)
    
    # 水晶音
    frequencies = [523, 659, 784, 1047]
    for i, freq in enumerate(frequencies):
        start_delay = i * 0.02
        start_sample = int(start_delay * SAMPLE_RATE)
        if start_sample < samples:
            note_t = t[start_sample:] - start_delay
            envelope = np.exp(-note_t * 6) * (1 - np.exp(-note_t * 20))
            wave_data[start_sample:] += 0.15 * envelope * np.sin(2 * np.pi * freq * note_t)
    
    # 轻微泛音
    for freq in [1047, 1319, 1568]:
        start_sample = int(np.random.uniform(0, 0.1) * SAMPLE_RATE)
        if start_sample < samples:
            note_t = t[start_sample:]
            envelope = np.exp(-note_t * 8)
            wave_data[start_sample:] += 0.05 * envelope * np.sin(2 * np.pi * freq * note_t)
    
    # 归一化
    max_val = np.max(np.abs(wave_data))
    if max_val > 0:
        wave_data = wave_data / max_val * 1.0
    
    return wave_data

def generate_bubble():
    duration = 0.3
    samples = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, samples)
    
    wave_data = np.zeros(samples)
    
    # 水泡声
    bubble_freq_start = 800
    bubble_freq_end = 200
    freq = bubble_freq_start + (bubble_freq_end - bubble_freq_start) * (t / duration)
    envelope = np.exp(-t * 15) * (1 - np.exp(-t * 30))
    
    wave_data = 0.3 * envelope * np.sin(2 * np.pi * freq * t)
    
    # 轻微噪音
    noise = np.random.randn(samples) * 0.02
    wave_data += noise * envelope
    
    # 归一化
    max_val = np.max(np.abs(wave_data))
    if max_val > 0:
        wave_data = wave_data / max_val * 1.0
    
    return wave_data

def write_wave(filename, data):
    data = (data * 32767).astype(np.int16)
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(data.tobytes())

if __name__ == '__main__':
    print("Generating ocean ambient...")
    ambient = generate_ocean_ambient()
    write_wave('assets/ambient_ocean.wav', ambient)
    
    print("Generating sparkle sound...")
    sparkle = generate_sparkle()
    write_wave('assets/sparkle.wav', sparkle)
    
    print("Generating bubble sound...")
    bubble = generate_bubble()
    write_wave('assets/bubble.wav', bubble)
    
    print("Done!")
