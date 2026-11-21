#!/usr/bin/env python3
"""
Test Harness for Sub-task 4.1.1: VUMeter Dataclass API Harmonization
Verifies:
1. VUMeter instantiates cleanly using FrameConfig, VUMeterStyle, and MeterBallistics.
2. Channel Enum and string aliases ('left', Channel.LEFT) resolve correctly.
3. Passing dictionary outlines/backgrounds triggers DeprecationWarning.
"""

import os
import sys
import warnings

os.environ["SDL_VIDEODRIVER"] = "dummy"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

import pygame
pygame.init()

from pyvisualiser.core.base_defs import Channel
from pyvisualiser.core.config import FrameConfig
from pyvisualiser.styles.ballistics import MeterBallistics
from pyvisualiser.styles.styles import VUMeterStyle, OutlineStyle
from pyvisualiser.visualisers.vumeters import VUMeter
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
        self.vu = {'left': 0.5, 'right': 0.5, 'mono': 0.5}

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


def test_vumeter_modern_api():
    print("=" * 70)
    print("Running Sub-task 4.1.1 Verification Test: VUMeter Modern API")
    print("=" * 70)

    plat = MockPlatform()
    root = Frame(plat, config=FrameConfig())

    # 1. Test clean dataclass instantiation
    print("[*] Test 1: Instantiating VUMeter with FrameConfig, VUMeterStyle, MeterBallistics...")
    meter = VUMeter(
        root,
        channel=Channel.LEFT,
        config=FrameConfig(scalers=(0.5, 1.0), theme='hifi'),
        visuals=VUMeterStyle(),
        ballistics=MeterBallistics(decay_rate=0.2)
    )
    assert meter.channel == Channel.LEFT
    assert meter.VU.ballistics.decay_rate == 0.2
    meter.update_screen()
    print("[+] VUMeter modern dataclass instantiation verified.")

    # 2. Test string channel conversion & DeprecationWarning on dicts
    print("\n[*] Test 2: Testing string channel conversion & legacy dict deprecation warning...")
    warnings.simplefilter("always", DeprecationWarning)
    
    with warnings.catch_warnings(record=True) as w:
        meter_str = VUMeter(
            root,
            channel="right",
            outline={'colour': 'light', 'width': 2} # Should trigger DeprecationWarning
        )
        assert len(w) >= 1, "Passing a dict outline should trigger a DeprecationWarning"
        assert issubclass(w[0].category, DeprecationWarning)
        assert meter_str.channel == Channel.RIGHT

    print("[+] Deprecation warning and string channel parsing verified.")
    print("=" * 70)
    print("[+] SUB-TASK 4.1.1 TEST PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_vumeter_modern_api()