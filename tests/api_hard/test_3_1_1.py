#!/usr/bin/env python3
"""
Test Harness for Sub-task 3.1.1: MeterBallistics Integration & Verification
Verifies:
1. MeterBallistics dataclass validation (e.g. decay_rate bounds, smoothing_samples min).
2. VU calculation with MeterBallistics (rise response, exponential decay, peak-hold persistence).
3. VUMeter constructor cleanly accepts ballistics=MeterBallistics(...) and passes it to self.VU.
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

from pyvisualiser.styles.ballistics import MeterBallistics
from pyvisualiser.visualisers.vumeters import VU, VUMeter
from pyvisualiser.core.state import AudioSnapshot
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
        self.vu = {'left': 0.0, 'right': 0.0, 'mono': 0.0}

        class MockRenderer:
            def draw_rect(self, *args, **kwargs): pass
            def draw_line(self, *args, **kwargs): pass
            def draw_lines(self, *args, **kwargs): pass
            def blit(self, *args, **kwargs): pass
        self.renderer = MockRenderer()

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


def test_meter_ballistics():
    print("=" * 70)
    print("Running Sub-task 3.1.1 Verification Test: MeterBallistics")
    print("=" * 70)

    # 1. Parameter Validation
    print("[*] Test 1: Testing MeterBallistics parameter validation...")
    mb = MeterBallistics(decay_rate=0.25, smoothing_samples=5, peak_hold_frames=20)
    assert mb.decay_rate == 0.25
    assert mb.smoothing_samples == 5
    assert mb.peak_hold_frames == 20

    try:
        MeterBallistics(decay_rate=1.5)
        assert False, "decay_rate >= 1.0 must raise ValueError"
    except ValueError:
        pass

    try:
        MeterBallistics(decay_rate=0.0)
        assert False, "decay_rate <= 0.0 must raise ValueError"
    except ValueError:
        pass

    # Non-positive smoothing_samples should be clamped to 1
    mb_zero = MeterBallistics(smoothing_samples=0)
    assert mb_zero.smoothing_samples == 1
    print("[+] MeterBallistics dataclass validation verified.")

    # 2. Ballistic step response & peak hold
    print("\n[*] Test 2: Testing VU class step response with MeterBallistics...")
    plat = MockPlatform()
    hold_frames = 10
    custom_ballistics = MeterBallistics(
        decay_rate=0.2,
        peak_decay_rate=0.05,
        smoothing_samples=1,
        peak_hold_frames=hold_frames
    )
    vu = VU(plat, channel='mono', ballistics=custom_ballistics)

    # Drive 1.0 for several frames to reach steady state
    plat.vu['mono'] = 1.0
    for _ in range(5):
        h1, p1 = vu.read()

    assert h1 > 0.9, f"Steady state should be close to 1.0, got {h1}"
    assert p1 >= h1, f"Peak should be at least h1, got p1={p1}, h1={h1}"
    initial_peak = p1

    # Drop input to 0.0
    plat.vu['mono'] = 0.0

    # Exactly `hold_frames` calls must maintain the initial peak
    for frame_idx in range(hold_frames):
        h, p = vu.read()
        assert p == initial_peak, (
            f"Frame {frame_idx + 1}/{hold_frames} prematurely decayed peak: got {p}, expected {initial_peak}"
        )

    # The (hold_frames + 1)-th call must trigger peak decay
    _, p_decaying = vu.read()
    assert p_decaying < initial_peak, (
        f"Frame {hold_frames + 1} did not trigger peak decay: got {p_decaying}, initial was {initial_peak}"
    )

    # Run remaining decay until near zero
    for _ in range(50):
        vu.read()
    h_final, _ = vu.read()
    assert h_final < 0.05, f"Signal should decay close to 0, got {h_final}"
    print("[+] VU rise, peak hold duration, and exponential release verified.")

    # 3. AudioSnapshot Injection
    print("\n[*] Test 3: Testing AudioSnapshot injection into VU.read()...")
    snap = AudioSnapshot(vu={'mono': 0.75, 'left': 0.4, 'right': 0.8})
    h_snap, _ = vu.read(audio_snapshot=snap)
    assert h_snap > 0.0, "AudioSnapshot injection should drive level"
    print("[+] AudioSnapshot read verified.")

    # 4. VUMeter Constructor Integration
    print("\n[*] Test 4: Testing VUMeter constructor with ballistics...")
    root_frame = Frame(plat, scalers=(1.0, 1.0))
    meter = VUMeter(
        root_frame,
        channel='left',
        ballistics=MeterBallistics(decay_rate=0.15, smoothing_samples=6)
    )
    assert meter.channel == 'left'
    assert meter.VU.ballistics.decay_rate == 0.15
    assert meter.VU.ballistics.smoothing_samples == 6
    meter.update_screen()
    print("[+] VUMeter component instantiation with custom ballistics verified.")

    print("\n" + "=" * 70)
    print("[+] ALL SUB-TASK 3.1.1 TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_meter_ballistics()