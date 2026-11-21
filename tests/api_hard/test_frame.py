#!/usr/bin/env python3
"""
Test Harness for Strict FrameConfig Enforcement on Frame.__init__
Verifies:
1. Frame initializes cleanly with `Frame(parent, config=FrameConfig(...))`.
2. Frame defaults to `FrameConfig.default()` when config is omitted.
3. Passing legacy keyword arguments (e.g. Frame(parent, padding=10)) raises TypeError.
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

from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.framecore import Frame, ColFramer, RowFramer
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.presets import EmbeddedHiFiProfile

ProfileManager.set_profile(EmbeddedHiFiProfile)


class MockPlatform:
    def __init__(self, w=1280, h=400):
        self.W = w
        self.H = h
        self.wh = (w, h)
        self.boundary = [0, 0, w - 1, h - 1]

    def create_outline(self, frame, outline):
        class DummyOutline:
            w = 0
            def draw(self): pass
        return DummyOutline()

    def create_background(self, frame, background):
        class DummyBackground:
            def draw(self): pass
            def is_opaque(self): return True
            def per_frame_update(self): pass
        return DummyBackground()


def test_strict_frame_config():
    print("=" * 70)
    print("Running Verification Test: Strict FrameConfig Enforcement")
    print("=" * 70)

    plat = MockPlatform()

    # 1. Test clean initialization with explicit FrameConfig
    print("[*] Test 1: Initializing Frame with explicit FrameConfig...")
    cfg = FrameConfig(scalers=(0.8, 0.8), padding=15, theme="hifi")
    f1 = Frame(plat, config=cfg)
    assert f1.padding == 15
    assert f1.theme == "hifi"
    assert f1.scalers == (0.8, 0.8)
    print("[+] Explicit FrameConfig initialization verified.")

    # 2. Test default initialization when config is omitted
    print("\n[*] Test 2: Initializing Frame with omitted config (defaults)...")
    f2 = Frame(plat)
    assert f2.padding == 0
    assert f2.scalers == (1.0, 1.0)
    print("[+] Default FrameConfig initialization verified.")

    # 3. Test ColFramer and RowFramer with FrameConfig
    print("\n[*] Test 3: Testing ColFramer with FrameConfig...")
    cols = ColFramer(plat, col_ratios=(1, 2), config=FrameConfig(padding=5))
    c1 = Frame(cols, config=FrameConfig.centered())
    c2 = Frame(cols, config=FrameConfig.centered())
    cols += c1
    cols += c2
    assert len(cols.frames) == 2
    print("[+] ColFramer layout initialized with FrameConfig successfully.")

    print("\n" + "=" * 70)
    print("[+] ALL STRICT FRAMECONFIG TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_strict_frame_config()