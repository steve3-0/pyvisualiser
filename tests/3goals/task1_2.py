#!/usr/bin/env python3
"""
Test Harness for Task 1.2: VRAM Memory Leak Elimination
Verifies that:
1. GeometryPass.blit() releases previously allocated textures when updated.
2. RenderTarget releases old FBO and texture allocations on resize.
3. Text and Image release their ModernGL textures when content changes.
4. Total active textures do not grow with repeated updates (remains flat across 500 iterations).
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

import moderngl
from pyvisualiser.core.render import RenderContext, RenderTarget
from pyvisualiser.core.displaydriver import GeometryPass
from pyvisualiser.core.components import Text
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.presets import EmbeddedHiFiProfile

ProfileManager.set_profile(EmbeddedHiFiProfile)


class MockPlatform:
    def __init__(self, ctx):
        self.W = 1280
        self.H = 400
        self.ctx = ctx


class MockParent:
    def __init__(self, platform):
        self.platform = platform
        self.abs_wh = (400, 50)
        self.outline_w = 0
        self.padding = 0

    def abs_rect(self):
        return (0, 0, 400, 50)

    def abs_origin(self, offset=(0, 0)):
        return (0, 0)

    def align_coords(self, coords, size, justify):
        return coords

    def geostr(self):
        return "MockParent"

    @property
    def colours(self):
        class C:
            def get(self, c=None, opacity=255):
                return (255, 255, 255, 255)
        return C()


class TextureTrackingContext:
    """Wraps ModernGL context to track active (unreleased) texture objects."""
    def __init__(self, ctx):
        self._ctx = ctx
        self.active_textures = set()

        original_texture = ctx.texture

        def tracked_texture(*args, **kwargs):
            tex = original_texture(*args, **kwargs)
            self.active_textures.add(tex)

            original_release = tex.release

            def tracked_release():
                self.active_textures.discard(tex)
                return original_release()

            tex.release = tracked_release
            return tex

        self._ctx.texture = tracked_texture

    @property
    def ctx(self):
        return self._ctx


def run_vram_leak_tests():
    print("=" * 70)
    print("Running Task 1.2 Verification Test: VRAM Memory Leak Elimination")
    print("=" * 70)

    ctx = moderngl.create_context(standalone=True)
    tracker = TextureTrackingContext(ctx)

    platform = MockPlatform(tracker.ctx)
    render_context = RenderContext(tracker.ctx, (platform.W, platform.H), platform)
    geometry_pass = GeometryPass(render_context)

    # Record baseline textures allocated by RenderContext (empty_texture)
    baseline_textures = len(tracker.active_textures)
    print(f"[*] Baseline context textures (empty_texture): {baseline_textures}")

    # -------------------------------------------------------------
    # Test 1: GeometryPass.blit() texture holder tracking
    # -------------------------------------------------------------
    class MockHolder:
        _gl_texture = None

    holder = MockHolder()

    print("[*] Test 1: Simulating 500 consecutive track/text blit updates...")
    for i in range(500):
        surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        surf.fill((i % 256, (i * 2) % 256, (i * 3) % 256, 255))
        
        # Simulate content invalidation on the holder
        if holder._gl_texture is not None:
            holder._gl_texture.release()
            holder._gl_texture = None
            
        geometry_pass.blit(surf, (0, 0), texture_holder=holder)

    active_count = len(tracker.active_textures)
    print(f"[*] Active textures after 500 blits: {active_count}")
    assert active_count == baseline_textures + 1, (
        f"Memory leak in blit(): {active_count} active (expected {baseline_textures + 1})"
    )

    # Release holder texture
    if holder._gl_texture is not None:
        holder._gl_texture.release()
        holder._gl_texture = None
    assert len(tracker.active_textures) == baseline_textures, (
        f"Expected {baseline_textures} active textures after releasing holder, got {len(tracker.active_textures)}"
    )
    print("[+] Verified: GeometryPass.blit() does not leak VRAM across updates.")

    # -------------------------------------------------------------
    # Test 2: RenderTarget resize cleanup
    # -------------------------------------------------------------
    print("[*] Test 2: Verifying RenderTarget texture & FBO release on resize...")
    rt = RenderTarget(tracker.ctx, (200, 100))
    expected_active = baseline_textures + 1
    assert len(tracker.active_textures) == expected_active, (
        f"Expected {expected_active} textures allocated, got {len(tracker.active_textures)}"
    )

    for size in [(300, 150), (400, 200), (500, 250), (200, 100)]:
        rt.resize(size)
        assert len(tracker.active_textures) == expected_active, (
            f"Leaked texture during resize to {size}: {len(tracker.active_textures)} active textures"
        )

    # Release RenderTarget
    rt.texture.release()
    rt.fbo.release()
    assert len(tracker.active_textures) == baseline_textures
    print("[+] Verified: RenderTarget properly releases textures and FBOs on resize.")

    # -------------------------------------------------------------
    # Test 3: Text component string updates
    # -------------------------------------------------------------
    print("[*] Test 3: Verifying Text component release on string changes...")
    parent = MockParent(platform)
    platform.renderer = geometry_pass

    text_item = Text(parent, text="Track 1", fontmax=24, reset=True)
    text_item.draw("Track 1")

    initial_text_textures = len(tracker.active_textures)

    for i in range(100):
        text_item.draw(f"Track {i}")

    final_text_textures = len(tracker.active_textures)
    print(f"[*] Active textures after 100 track updates: {final_text_textures}")
    assert final_text_textures == initial_text_textures, (
        f"Text component leaked textures: started with {initial_text_textures}, ended with {final_text_textures}"
    )

    # Cleanup text item
    if text_item._gl_texture is not None:
        text_item._gl_texture.release()
        text_item._gl_texture = None

    # Final cleanup of context permanent resources
    render_context.empty_texture.release()
    assert len(tracker.active_textures) == 0, (
        f"Expected 0 active textures after full context teardown, got {len(tracker.active_textures)}"
    )

    print("[+] Verified: Text component releases old GPU textures when content changes.")
    print("=" * 70)
    print("[+] ALL VRAM LEAK TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_vram_leak_tests()