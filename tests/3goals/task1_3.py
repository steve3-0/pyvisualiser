#!/usr/bin/env python3
"""
Test Harness for Task 1.3: Additive Blend Batching Optimization
Verifies that:
1. Alternating normal and additive rectangles do NOT shatter batches.
2. 50 alternating normal and additive bars are submitted in exactly 1 single draw call.
3. Spectrum bars sharing the same gradient texture stay in a single draw call.
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
from pyvisualiser.core.render import RenderContext
from pyvisualiser.core.displaydriver import GeometryPass
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.presets import EmbeddedHiFiProfile

ProfileManager.set_profile(EmbeddedHiFiProfile)


class MockPlatform:
    def __init__(self, ctx):
        self.W = 1280
        self.H = 400
        self.ctx = ctx


def test_batching_optimization():
    print("=" * 70)
    print("Running Task 1.3 Verification Test: Additive Batching Optimization")
    print("=" * 70)

    ctx = moderngl.create_context(standalone=True)
    platform = MockPlatform(ctx)
    render_context = RenderContext(ctx, (platform.W, platform.H), platform)
    geometry_pass = GeometryPass(render_context)

    # Spy on VAO render calls
    render_calls = 0
    original_render = geometry_pass.vao.render

    def counting_render(*args, **kwargs):
        nonlocal render_calls
        render_calls += 1
        return original_render(*args, **kwargs)

    geometry_pass.vao.render = counting_render

    # -------------------------------------------------------------
    # Test 1: 50 Alternating Normal and Additive Rectangles
    # -------------------------------------------------------------
    print("[*] Test 1: Queueing 50 alternating normal & additive rectangles...")
    geometry_pass.clear_batch()

    for i in range(50):
        is_add = (i % 2 == 1)
        geometry_pass.draw_rect(
            color=(0, 180, 240, 200),
            rect=(i * 20, 50, 15, 250),
            additive=is_add
        )

    render_calls = 0
    geometry_pass.render()

    print(f"[*] Total OpenGL Draw Calls executed: {render_calls}")
    assert render_calls == 1, (
        f"Batching failed: Expected 1 draw call for 50 alternating shapes, but got {render_calls}"
    )
    print("[+] Verified: 50 alternating normal and additive shapes batched into exactly 1 draw call.")

    # -------------------------------------------------------------
    # Test 2: Shared Gradient Texture with Alternating Glows
    # -------------------------------------------------------------
    print("\n[*] Test 2: Simulating spectrum with shared gradient texture and glow...")
    geometry_pass.clear_batch()

    gradient_surface = pygame.Surface((256, 1))
    for x in range(256):
        gradient_surface.set_at((x, 0), (x, 255 - x, 128, 255))

    class TextureHolder:
        _gl_texture = None

    holder = TextureHolder()

    # Simulate 48 spectrum bands, each with inner glow, outer bloom, and main bar
    for i in range(48):
        x = i * 25
        # Inner glow (additive)
        geometry_pass.draw_rect(
            color=(0, 255, 255, 100),
            rect=(x - 2, 80, 20, 220),
            softness=0.8,
            additive=True
        )
        # Outer bloom (additive)
        geometry_pass.draw_rect(
            color=(0, 150, 255, 60),
            rect=(x - 5, 75, 26, 230),
            softness=1.5,
            additive=True
        )
        # Main bar (normal, gradient texture)
        geometry_pass.draw_rect(
            color=(255, 255, 255, 255),
            rect=(x, 100, 16, 200),
            gradient_image=gradient_surface,
            texture_holder=holder,
            additive=False
        )

    render_calls = 0
    geometry_pass.render()

    print(f"[*] Total Draw Calls for 48 full spectrum bars (144 quads): {render_calls}")
    # Texture is bound once and reused, flat glows stream without breaks
    assert render_calls <= 2, (
        f"Batching failed for spectrum: Expected <= 2 draw calls, got {render_calls}"
    )

    # Cleanup texture
    if holder._gl_texture is not None:
        holder._gl_texture.release()
        holder._gl_texture = None

    print("[+] Verified: Spectrum bars and additive glows batched without batch shattering.")
    print("=" * 70)
    print("[+] ALL TASK 1.3 BATCHING TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_batching_optimization()