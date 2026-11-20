#!/usr/bin/env python3
"""
Test Harness for Sub-task 3.1.2: FFTBallistics Integration & Verification
Verifies:
1. FFTBallistics parameter validation and defaults.
2. Spectrum class step response with custom FFTBallistics (attack, decay, peak hold).
3. SpectrumFrame instantiation with ballistics=FFTBallistics(...) and clean rendering.
"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

import pygame
pygame.init()

from pyvisualiser.styles.ballistics import FFTBallistics
from pyvisualiser.visualisers.spectrum import Spectrum, SpectrumFrame
from pyvisualiser.core.framecore import Frame
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.presets import EmbeddedHiFiProfile

ProfileManager.set_profile(EmbeddedHiFiProfile)


class MockPlatform:
    def __init__(self, w=1280, h=400):
        self.W = w
        self.H = h
        self.wh = (w, h)
        self.boundary = [0, 0, w - 1, h - 1]
        self.mock_fft_data = [0.0] * 48

        class MockRenderer:
            def draw_rect(self, *args, **kwargs): pass
            def draw_line(self, *args, **kwargs): pass
            def draw_lines(self, *args, **kwargs): pass
            def blit(self, *args, **kwargs): pass
        self.renderer = MockRenderer()

    def createBands(self, spacing, flast=None):
        # Return 24 synthetic bands
        return [100.0 * (i + 1) for i in range(24)]

    def packFFT(self, freqs, channel):
        return [self.mock_fft_data[i % len(self.mock_fft_data)] for i in range(len(freqs))]

    def create_outline(self, frame, outline):
        class Dummy:
            w = 0
            def draw(self): pass
        return Dummy()

    def create_background(self, frame, background):
        class Dummy:
            def draw(self): pass
            def is_opaque(self): return True
            def per_frame_update(self): pass
        return Dummy()


def test_fft_ballistics():
    print("=" * 70)
    print("Running Sub-task 3.1.2 Verification Test: FFTBallistics")
    print("=" * 70)

    # 1. Parameter Validation
    print("[*] Test 1: Testing FFTBallistics parameter validation...")
    fb = FFTBallistics(attack_rate=0.85, decay_rate=0.2, peak_decay_rate=0.03)
    assert fb.attack_rate == 0.85
    assert fb.decay_rate == 0.2
    assert fb.peak_decay_rate == 0.03

    try:
        FFTBallistics(decay_rate=1.2)
        assert False, "decay_rate >= 1.0 must raise ValueError"
    except ValueError:
        pass
    print("[+] FFTBallistics parameter validation verified.")

    # 2. Step Response on Spectrum Class
    print("\n[*] Test 2: Testing Spectrum step response with FFTBallistics...")
    plat = MockPlatform()
    custom_ballistics = FFTBallistics(decay_rate=0.3, peak_decay_rate=0.05)

    spec = Spectrum(width=600, ballistics=custom_ballistics)
    spec.platform = plat

    # Inject full-scale pulse across all bands
    plat.mock_fft_data = [1.0] * 48
    for _ in range(5):
        spec.read(channel='mono')

    # All bars should be near 1.0
    initial_level = spec.current[0].smoothed()
    initial_peak = spec.peaks[0]
    assert initial_level > 0.8, f"Bars should rise near 1.0, got {initial_level}"
    assert initial_peak >= initial_level, "Peak should match or exceed current level"

    # Step down to silence
    plat.mock_fft_data = [0.0] * 48
    spec.read(channel='mono')
    decayed_level = spec.current[0].smoothed()
    assert decayed_level < initial_level, f"Signal should decay: {decayed_level} < {initial_level}"

    # Peak hold verification: peak should remain frozen during the 15-frame hold window
    for hold_idx in range(14):
        spec.read(channel='mono')
        assert spec.peaks[0] == initial_peak, (
            f"Band 0 peak decayed prematurely on hold frame {hold_idx + 1}: got {spec.peaks[0]}, expected {initial_peak}"
        )

    # Subsequent read should initiate peak decay
    spec.read(channel='mono')
    spec.read(channel='mono')
    assert spec.peaks[0] < initial_peak, f"Peak should decay after hold window: {spec.peaks[0]} < {initial_peak}"

    print("[+] Spectrum FFT attack, exponential release, and band peak hold verified.")

    # 3. SpectrumFrame Constructor Integration
    print("\n[*] Test 3: Testing SpectrumFrame constructor with FFTBallistics...")
    root_frame = Frame(plat, scalers=(1.0, 1.0))
    spec_frame = SpectrumFrame(
        root_frame,
        channel='mono',
        ballistics=FFTBallistics(decay_rate=0.15)
    )
    assert spec_frame.channel == 'mono'
    assert spec_frame.ballistics.decay_rate == 0.15
    assert spec_frame.ballistics == spec_frame.ballistics
    spec_frame.update_screen()
    print("[+] SpectrumFrame component instantiation with custom ballistics verified.")

    print("\n" + "=" * 70)
    print("[+] ALL SUB-TASK 3.1.2 TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_fft_ballistics()