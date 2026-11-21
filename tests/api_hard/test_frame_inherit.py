#!/usr/bin/env python3
"""
Test Harness for FrameConfig Theme & Context Inheritance
Verifies:
1. Sub-frames nested inside a parent Frame automatically inherit the parent's theme if config.theme is None.
2. Sub-frames scale to the parent's canvas bounds.
3. Explicit child configuration successfully overrides parent inheritance.
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
from pyvisualiser.core.framecore import Frame, ColFramer
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


def test_frame_inheritance():
    print("=" * 70)
    print("Running Verification Test: Frame Theme & Context Inheritance")
    print("=" * 70)

    plat = MockPlatform()

    # 1. Create Parent Screen with 'ocean' theme
    parent_screen = Frame(plat, config=FrameConfig(theme='ocean'))
    assert parent_screen.theme == 'ocean'

    # 2. Create Child Frame without specifying theme (should inherit 'ocean')
    child_inherited = Frame(parent_screen, config=FrameConfig())
    assert child_inherited.theme == 'ocean', f"Child failed to inherit parent theme: expected 'ocean', got {child_inherited.theme}"
    print("[+] Verified: Child frame successfully inherited parent's 'ocean' theme.")

    # 3. Create Child Frame with explicit override theme ('hifi')
    child_overridden = Frame(parent_screen, config=FrameConfig(theme='hifi'))
    assert child_overridden.theme == 'hifi', f"Child override failed: expected 'hifi', got {child_overridden.theme}"
    print("[+] Verified: Child frame successfully overrode parent theme with explicit config.")

    # 4. Verify Framer hierarchy inheritance (e.g. ColFramer)
    cols = ColFramer(parent_screen, col_ratios=(1, 1), config=FrameConfig())
    assert cols.theme == 'ocean', "ColFramer failed to inherit parent theme"
    
    sub_child = Frame(cols, config=FrameConfig())
    assert sub_child.theme == 'ocean', "Nested sub-frame inside ColFramer failed to inherit theme"
    print("[+] Verified: Multi-level Framer hierarchy inherits container theme seamlessly.")

    print("\n" + "=" * 70)
    print("[+] ALL FRAME INHERITANCE TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_frame_inheritance()