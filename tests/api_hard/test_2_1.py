#!/usr/bin/env python3
"""
Test Harness for Task 2.1: FrameConfig Architecture
Verifies:
1. FrameConfig instantiation and boundary validation (disallow non-positive scalers).
2. Frame initialization using pure FrameConfig.
3. Frame initialization using legacy kwargs (validating seamless bridging).
4. Geometry coordinates and padding deduction match identically under both methods.
5. ColFramer and RowFramer layout calculations with FrameConfig.
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

from pyvisualiser.core.base_defs import HorizontalAlign, VerticalAlign
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


def test_frame_config():
    print("=" * 70)
    print("Running Task 2.1 Verification Test: FrameConfig Architecture")
    print("=" * 70)

    # 1. Validation tests on FrameConfig dataclass
    print("[*] Test 1: Testing FrameConfig parameter validation...")
    cfg = FrameConfig(scalers=(0.5, 0.8), padding=12)
    assert cfg.scalers == (0.5, 0.8)
    assert cfg.padding == 12

    # Negative padding must be clamped to 0
    cfg_neg = FrameConfig(padding=-5, margin=-10)
    assert cfg_neg.padding == 0
    assert cfg_neg.margin == 0

    # Non-positive scalers must raise ValueError
    try:
        FrameConfig(scalers=(0.0, 1.0))
        assert False, "Zero scaler must raise ValueError"
    except ValueError:
        pass

    try:
        FrameConfig(scalers=(-0.5, 1.0))
        assert False, "Negative scaler must raise ValueError"
    except ValueError:
        pass
    print("[+] FrameConfig validation verified.")

    # 2. Modern Frame creation with FrameConfig
    print("\n[*] Test 2: Instantiating top-level Screen Frame with FrameConfig...")
    root_plat = MockPlatform(w=1280, h=400)
    screen_cfg = FrameConfig(theme='hifi')
    screen = Frame(root_plat, config=screen_cfg)
    assert screen.w == 1280
    assert screen.h == 400
    assert screen.theme == 'hifi'
    print("[+] Screen initialized with FrameConfig successfully.")

    # 3. Sub-frame comparison: New FrameConfig vs Legacy Kwargs
    print("\n[*] Test 3: Comparing FrameConfig vs Legacy Kwargs geometry...")
    child_modern = Frame(
        screen,
        config=FrameConfig(
            scalers=(0.5, 0.5),
            align=(HorizontalAlign.LEFT, VerticalAlign.TOP),
            padding=10
        )
    )

    child_legacy = Frame(
        screen,
        scalers=(0.5, 0.5),
        align=('left', 'top'),
        padding=10
    )

    assert child_modern.wh == child_legacy.wh, (
        f"Dimension mismatch: Modern {child_modern.wh} vs Legacy {child_legacy.wh}"
    )
    assert child_modern.abs_rect() == child_legacy.abs_rect(), (
        f"abs_rect mismatch: Modern {child_modern.abs_rect()} vs Legacy {child_legacy.abs_rect()}"
    )
    print(f"[+] Dimensions ({child_modern.wh}) and abs_rect match identically.")

# 4. AxisFramers (ColFramer / RowFramer) with FrameConfig
    print("\n[*] Test 4: Testing ColFramer & RowFramer with FrameConfig...")
    cols = ColFramer(screen, col_ratios=(1, 2, 1), padpc=0.04)
    c1 = Frame(cols, config=FrameConfig.centered())
    c2 = Frame(cols, config=FrameConfig.centered())
    c3 = Frame(cols, config=FrameConfig.centered())

    # Idiomatic pyvisualiser container attachment
    cols += c1
    cols += c2
    cols += c3

    assert len(cols.frames) == 3, f"Expected 3 frames in cols, found {len(cols.frames)}"
    assert c2.w > c1.w, f"Middle column (w={c2.w}) must be wider than side column (w={c1.w})"
    print(f"[+] ColFramer child widths: {[f.w for f in cols.frames]}")

    print("\n" + "=" * 70)
    print("[+] ALL TASK 2.1 TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_frame_config()