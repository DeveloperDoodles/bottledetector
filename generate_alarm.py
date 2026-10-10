"""
generate_alarm.py — Generates an alarm.wav file programmatically.

Run this once before starting the detector:
    python generate_alarm.py

Creates a pulsing two-tone alarm sound (1 second long, loops seamlessly).
"""

import numpy as np
import wave
import struct
import os

SAMPLE_RATE = 44100
DURATION = 1.0  # seconds (loops seamlessly)
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alarm.wav")

# Two alternating tones for that classic alarm feel
FREQ_HIGH = 880   # A5
FREQ_LOW = 660    # E5
PULSE_RATE = 6    # pulses per second


def generate_alarm():
    """Generate a pulsing two-tone alarm WAV file."""
    num_samples = int(SAMPLE_RATE * DURATION)
    samples = []

    for i in range(num_samples):
        t = i / SAMPLE_RATE

        # Alternate between high and low tones
        pulse_phase = int(t * PULSE_RATE) % 2
        freq = FREQ_HIGH if pulse_phase == 0 else FREQ_LOW

        # Generate sine wave
        value = np.sin(2 * np.pi * freq * t)

        # Add slight envelope to soften harsh clicks at tone transitions
        pulse_pos = (t * PULSE_RATE) % 1.0
        envelope = min(pulse_pos * 20, 1.0) * min((1.0 - pulse_pos) * 20, 1.0)

        value *= envelope * 0.7  # 0.7 = overall volume

        # Convert to 16-bit integer
        sample = int(value * 32767)
        sample = max(-32768, min(32767, sample))
        samples.append(sample)

    # Write WAV file
    with wave.open(OUTPUT_FILE, "w") as wav:
        wav.setnchannels(1)        # mono
        wav.setsampwidth(2)        # 16-bit
        wav.setframerate(SAMPLE_RATE)
        for s in samples:
            wav.writeframes(struct.pack("<h", s))

    print(f"✅ Alarm sound generated: {OUTPUT_FILE}")
    print(f"   Duration: {DURATION}s | Sample rate: {SAMPLE_RATE}Hz")
    print(f"   Tones: {FREQ_HIGH}Hz / {FREQ_LOW}Hz | Pulse rate: {PULSE_RATE}/s")


if __name__ == "__main__":
    generate_alarm()
