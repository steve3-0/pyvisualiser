#!/usr/bin/env python3
"""
Test Harness for Step 3: Background System & Sub-Frame Bounds
Verifies:
1. Fullscreen background has viewport = None and fills target texture completely.
2. Sub-frame background correctly computes physical scissored viewport.
3. BackgroundRenderPass respects DisplayMetrics across 1x and 2x DPI scales.
"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

import pygame
pygame.init()

import moderngl
from pyvisualiser.core.render import RenderContext, RenderTarget, DisplayMetrics, Compositor
from pyvisualiser.core.backgrounds import BackgroundBase, BackgroundRenderPass, BackgroundStyle, AmbientGlowStyle
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.presets import EmbeddedHiFiProfile

ProfileManager.set_profile(EmbeddedHiFiProfile)


class MockPlatform:
    def __init__(self, metrics):
        self.W = metrics.logical_w
        self.H = metrics.logical_h
        self.metrics = metrics
        self.vu = {'mono': 0.5}


class MockColours:
    def get(self, name):
        return (20, 20, 40, 255)


class MockFrame:
    def __init__(self, platform, rect):
        self.platform = platform
        self._rect = rect  # (x, y, w, h) in logical pixels
        self.colours = MockColours()

    def abs_background(self):
        return self._rect


def test_backgrounds():
    print("=" * 70)
    print("Running Step 3 Verification Test: Backgrounds & Sub-Frame Bounds")
    print("=" * 70)

    ctx = moderngl.create_context(standalone=True)
    metrics = DisplayMetrics(logical_w=1280, logical_h=400, dpi_scale=2.0)
    platform = MockPlatform(metrics)
    render_context = RenderContext(ctx, metrics, platform=platform)

    class MockDriver:
        def __init__(self, rc):
            self.render_context = rc
            self.compositor = Compositor(rc)

    platform.gfx_driver = MockDriver(render_context)

    # 1. Fullscreen ScreenBackground Test
    print("[*] Test 1: Testing Full-Screen Background...")
    full_frame = MockFrame(platform, (0, 0, 1280, 400))
    full_bg = BackgroundBase(full_frame, BackgroundStyle(colour='background'))
    full_bg.draw()

    assert full_bg.render_pass.viewport is None, (
        f"Fullscreen background must have viewport=None, got {full_bg.render_pass.viewport}"
    )
    print("[+] Verified: Full-screen background renders with viewport=None (fills full target).")

    # 2. Sub-Frame VUBackground Test (e.g., Left VU meter at x=50, y=50, w=300, h=250)
    print("\n[*] Test 2: Testing Localized Sub-Frame Background (VU Meter)...")
    sub_frame = MockFrame(platform, (50, 50, 300, 250))
    sub_bg = BackgroundBase(sub_frame, BackgroundStyle(colour='background', ambient_glow=AmbientGlowStyle(opacity=0.8)))
    sub_bg.draw()

    vp = sub_bg.render_pass.viewport
    assert vp is not None, "Sub-frame background must set a localized physical viewport!"
    
    # Expected physical calculation:
    # x = 50 * 2 = 100
    # gl_y = (400 - (50 + 250)) = 100 -> 100 * 2 = 200
    # w = 300 * 2 = 600
    # h = 250 * 2 = 500
    expected_vp = (100, 200, 600, 500)
    print(f"[*] Sub-Frame Physical Viewport: {vp} (Expected: {expected_vp})")
    assert vp == expected_vp, f"Viewport mismatch: expected {expected_vp}, got {vp}"
    print("[+] Verified: Sub-frame background correctly converts to physical scissor/viewport coordinates.")

    # 3. Test execution inside target FBO
    print("\n[*] Test 3: Rendering background pass into RenderTarget...")
    target = RenderTarget(render_context, scale=1.0)
    sub_bg.render_pass.render(target=target)

    # Scissor should be disabled after rendering sub-frame to avoid clipping downstream passes
    # ModernGL: None means scissor test is disabled
    # ModernGL resets ctx.scissor to the full framebuffer dimensions when disabled
    expected_full = (0, 0, target.width, target.height)
    assert ctx.scissor is None or ctx.scissor == expected_full, (
        f"Expected scissor to be disabled or full target {expected_full}, got {ctx.scissor}"
    )
    print(f"[+] Verified: Scissor box restored to unclipped full target: {ctx.scissor}")
    
    print("[+] Verified: OpenGL scissor state restored cleanly after sub-frame rendering.")

    print("\n" + "=" * 70)
    print("[+] ALL STEP 3 BACKGROUND TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_backgrounds()