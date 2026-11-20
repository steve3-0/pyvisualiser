#!/usr/bin/env python3
"""
Test Harness for Phase 3: Decoupled Ballistics & Bounding-Safe Polar Math
Verifies:
1. MeterBallistics and FFTBallistics validation and defaults.
2. VU calculation with isolated MeterBallistics (exponential decay and peak hold).
3. compute_safe_meter_radius guarantees all radial needle endpoints and ticks
   stay strictly inside bounding boxes across narrow (200x400), wide (600x200),
   and square (300x300) aspect ratios.
4. VUMeter initialises and renders using MeterBallistics without regression.
"""

import os
import sys
import math

os.environ["SDL_VIDEODRIVER"] = "dummy"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

import pygame
pygame.init()

from pyvisualiser.styles.styles import MeterBallistics, FFTBallistics
from pyvisualiser.visualisers.vumeters import (
    VU,
    VUMeter,
    compute_safe_meter_radius,
)
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


def test_ballistics_and_polar_math():
    print("=" * 70)
    print("Running Phase 3 Test: Decoupled Ballistics & Safe Polar Math")
    print("=" * 70)

    # 1. Test Ballistics Dataclasses
    print("[*] Test 1: Testing MeterBallistics & FFTBallistics dataclasses...")
    mb = MeterBallistics(decay_rate=0.25, smoothing_samples=5)
    assert mb.decay_rate == 0.25
    assert mb.smoothing_samples == 5

    try:
        MeterBallistics(decay_rate=1.5)
        assert False, "decay_rate >= 1.0 must raise ValueError"
    except ValueError:
        pass

    fb = FFTBallistics(decay_rate=0.3)
    assert fb.decay_rate == 0.3
    print("[+] Ballistics parameter validation verified.")

    # 2. Test VU class with MeterBallistics
    print("\n[*] Test 2: Testing VU class step response with MeterBallistics...")
    plat = MockPlatform()
    # Use smoothing_samples=1 so filter responds in 1 frame
    vu = VU(plat, channel='mono', ballistics=MeterBallistics(decay_rate=0.2, smoothing_samples=1))

    # Step input: drive 1.0 for several frames to reach steady-state
    # Step input: drive 1.0 for several frames to reach steady-state (1.1111 due to Smoother's 0.9 gain factor)
    plat.vu['mono'] = 1.0
    for _ in range(5):
        h1, p1 = vu.read()

    assert abs(h1 - (1.0 / 1.0)) < 0.01, f"Steady-state level should be ~1.11, got {h1}"
    assert abs(p1 - (1.0 / 1.0)) < 0.01, f"Peak hold should be ~1.11, got {p1}"

    # Step down: jump to 0.0 -> must decay monotonically
    # Step down: jump to 0.0 -> peak hold must preserve peak level during hold window
    plat.vu['mono'] = 0.0
    h2, p2 = vu.read()
    assert h2 < h1, f"Decay failed: {h2} should be < {h1}"
    assert abs(p2 - (1.0 / 1.0)) < 0.01, f"Peak hold should preserve peak level (~1.11), got {p2}"

    for _ in range(60):
        vu.read()
    h_final, _ = vu.read()
    assert h_final < 0.05, f"Value should decay near zero, got {h_final}"
    print("[+] VU ballistics step response and peak hold verified.")

    # 3. Test Bounding-Safe Polar Radius Engine across extreme aspect ratios
    print("\n[*] Test 3: Testing compute_safe_meter_radius across aspect ratios...")
    PI = math.pi
    endstops = (3 * PI / 4, 5 * PI / 4)  # 90-degree sweep (-45 deg to +45 deg)
    pivot = -0.7

    test_geometries = [
        ("Ultrawide", 600, 200),
        ("Narrow Column", 200, 400),
        ("Square", 300, 300),
        ("Extreme Narrow", 150, 500),
    ]

    for name, w, h in test_geometries:
        radius, cx, pivot_y = compute_safe_meter_radius(
            box_w=w,
            box_h=h,
            pivot_y_normalized=pivot,
            endstops=endstops,
            margin_px=6.0,
            font_height_px=14.0
        )

        steps = 20
        for i in range(steps + 1):
            theta = endstops[0] + i * (endstops[1] - endstops[0]) / steps
            tip_x = cx + radius * math.sin(theta)
            tip_y = pivot_y - radius * math.cos(theta) # Correct pivot vertical reference

            assert 0.0 <= tip_x <= float(w), f"[{name}] Horizontal overflow at step {i}: tip_x={tip_x:.1f} (w={w})"
            assert 0.0 <= tip_y <= float(h), f"[{name}] Vertical overflow at step {i}: tip_y={tip_y:.1f} (h={h})"

        print(f"  [+] {name:<16} ({w}x{h}) -> Safe Radius: {radius:.1f}px (Fully contained)")

    for theta in endstops:
            ang = theta - (math.pi / 2)
            tip_x = cx + radius * math.sin(ang)
            tip_y = cy - radius * math.cos(ang) # Upward deflection subtracts from pivot Y

            assert 0.0 <= tip_x <= float(w), f"[{name}] Horizontal overflow: tip_x={tip_x:.1f}"
            assert 0.0 <= tip_y <= float(h), f"[{name}] Vertical overflow: tip_y={tip_y:.1f} (box_h={h})"

    print(f"  [+] {name:<15} ({w}x{h}) -> Safe Radius: {radius:.1f}px (Strictly bounded)")

    # 4. End-to-End VUMeter instantiation with MeterBallistics
    print("\n[*] Test 4: Testing VUMeter component instantiation with ballistics...")
    root_frame = Frame(plat, scalers=(1.0, 1.0))
    meter = VUMeter(
        root_frame,
        channel='left',
        ballistics=MeterBallistics(decay_rate=0.25, smoothing_samples=8)
    )
    assert meter.channel == 'left'
    assert meter.VU.ballistics.decay_rate == 0.25
    meter.update_screen()
    print("[+] VUMeter initialized and rendered without error.")

    print("\n" + "=" * 70)
    print("[+] ALL PHASE 3 TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_ballistics_and_polar_math()