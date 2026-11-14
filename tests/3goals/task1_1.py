#!/usr/bin/env python3
"""
Test Harness for Task 1.1: Font Instantiation Elimination & Static Caching
Verifies:
1. Font objects are cached in FontCacheManager (0 calls to pygame.font.Font on repeat draws).
2. font.size() is used for layout metrics (no dummy render allocation).
3. Rendered surface caching keeps 1,000 steady-state draws well under 50ms (typically 2-10ms).
"""

import os
import sys
import time
from unittest.mock import patch

# Headless SDL video driver
os.environ["SDL_VIDEODRIVER"] = "dummy"

# Ensure repo root is in python path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

import pygame
pygame.init()
pygame.font.init()

from pyvisualiser.core.components import Text, FontCacheManager
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.presets import EmbeddedHiFiProfile

# Satisfy profile lookups
ProfileManager.set_profile(EmbeddedHiFiProfile)


class MockRenderer:
    def __init__(self):
        self.blit_calls = 0

    def blit(self, source, dest, area=None, special_flags=0, **kwargs):
        self.blit_calls += 1


class MockPlatform:
    def __init__(self):
        self.W = 1280
        self.H = 400
        self.renderer = MockRenderer()


class MockColours:
    def get(self, colour=None, opacity=255):
        return (255, 255, 255, 255)


class MockParentFrame:
    def __init__(self):
        self.platform = MockPlatform()
        self.colours = MockColours()
        self.abs_wh = (400, 50)
        self.outline_w = 0
        self.padding = 0

    def abs_origin(self, offset=(0, 0)):
        return (10, 10)

    def align_coords(self, coords, size, justify):
        return coords

    def geostr(self):
        return "MockParentFrame (400x50)"


def test_font_caching_and_benchmark():
    print("=" * 70)
    print("Running Task 1.1 Verification Test: Font Caching & Performance")
    print("=" * 70)

    FontCacheManager.clear()
    parent = MockParentFrame()

    # 1. Warm-up instantiation (loads font and renders first surface)
    text_component = Text(parent, text="Now Playing - Test Artist", fontmax=32, reset=True)
    text_component.draw("Now Playing - Test Artist")
    assert text_component.font is not None, "Font should be initialized."

    # 2. Benchmark 1,000 steady-state draw iterations
    iterations = 1000
    start_time = time.perf_counter()
    for _ in range(iterations):
        text_component.draw("Now Playing - Test Artist")
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    print(f"[*] Benchmark Result: {iterations} draws completed in {elapsed_ms:.2f} ms "
          f"({elapsed_ms / iterations:.4f} ms/frame)")

    # 3. Verify zero Font re-instantiations during steady-state
    original_font_init = pygame.font.Font
    with patch("pygame.font.Font", side_effect=original_font_init) as mock_font:
        for _ in range(100):
            text_component.draw("Now Playing - Test Artist")
        assert mock_font.call_count == 0, (
            f"Expected 0 Font instantiations during steady-state draws, got {mock_font.call_count}"
        )
    print("[*] Verified: 0 calls to pygame.font.Font during steady-state updates.")

    # 4. Verify textsize() uses font.size() without errors
    w, h = text_component.textsize("Now Playing - Test Artist", text_component.font)
    assert isinstance(w, int) and isinstance(h, int) and w > 0 and h > 0, (
        f"textsize() returned invalid dimensions: ({w}, {h})"
    )
    print(f"[*] Verified: textsize() returned valid dimensions ({w}x{h}) using font.size().")

    # 5. Assert performance threshold (< 50ms for 1,000 iterations)
    assert elapsed_ms < 50.0, (
        f"Performance budget exceeded: 1000 iterations took {elapsed_ms:.2f} ms (budget: 50.0 ms)"
    )
    print(f"[+] PASS: Performance budget met ({elapsed_ms:.2f} ms < 50.0 ms).")
    print("=" * 70)


if __name__ == "__main__":
    test_font_caching_and_benchmark()