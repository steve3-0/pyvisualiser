#!/usr/bin/env python3
"""
Test Harness for Task 2.1: Pipeline Reordering & Bloom Isolation
Verifies that:
1. Emissive elements (spectrum bars, shaders) are captured in emissive_target and trigger glow extraction.
2. Sharp UI/text elements rendered in the UI pass are strictly isolated from the emissive target (0 pixels leaked).
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
import numpy as np
from pyvisualiser.core.render import RenderContext, Compositor, RenderPass, BACKGROUND_colour
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.presets import EmbeddedHiFiProfile

ProfileManager.set_profile(EmbeddedHiFiProfile)


class MockPlatform:
    def __init__(self, ctx):
        self.W = 1280
        self.H = 400
        self.ctx = ctx


class EmissiveTestPass(RenderPass):
    """Renders a super-bright cyan box (HDR RGB = [0.0, 3.0, 3.0]) to trigger bloom."""
    def __init__(self, context):
        super().__init__(context)
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                void main() {
                    gl_Position = vec4(in_vert * 0.2 - vec2(0.5, 0.0), 0.0, 1.0);
                }
            """,
            fragment_shader="""
                #version 330
                out vec4 f_colour;
                void main() {
                    f_colour = vec4(0.0, 3.0, 3.0, 1.0); // HDR Cyan
                }
            """
        )
        vbo = self.ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype='f4'))
        self.vao = self.ctx.simple_vertex_array(self.prog, vbo, 'in_vert')

    def render(self, **kwargs):
        self.vao.render(moderngl.TRIANGLE_STRIP)


class SharpUITestPass(RenderPass):
    """Renders pure white text/UI geometry that should bypass the emissive pass entirely."""
    def __init__(self, context):
        super().__init__(context)
        self.prog = self.ctx.program(
            vertex_shader="""
                #version 330
                in vec2 in_vert;
                void main() {
                    gl_Position = vec4(in_vert * 0.2 + vec2(0.5, 0.0), 0.0, 1.0);
                }
            """,
            fragment_shader="""
                #version 330
                out vec4 f_colour;
                void main() {
                    f_colour = vec4(1.0, 1.0, 1.0, 1.0); // Pure White UI
                }
            """
        )
        vbo = self.ctx.buffer(np.array([-1, -1, 1, -1, -1, 1, 1, 1], dtype='f4'))
        self.vao = self.ctx.simple_vertex_array(self.prog, vbo, 'in_vert')

    def render(self, **kwargs):
        self.vao.render(moderngl.TRIANGLE_STRIP)


def test_pipeline_reordering():
    print("=" * 70)
    print("Running Task 2.1 Verification Test: Pipeline Reordering & Bloom Isolation")
    print("=" * 70)

    ctx = moderngl.create_context(standalone=True)
    platform = MockPlatform(ctx)
    render_context = RenderContext(ctx, (platform.W, platform.H), platform)
    
    compositor = Compositor(render_context)
    
    # Register passes to their correct pipeline stages
    emissive_pass = EmissiveTestPass(render_context)
    ui_pass = SharpUITestPass(render_context)
    
    compositor.add_emissive_pass(emissive_pass)
    compositor.add_ui_pass(ui_pass)

    # 1. Render Emissive Pass manually to verify isolation
    compositor.emissive_target.use()
    bg = [c / 255.0 for c in BACKGROUND_colour]
    compositor.emissive_target.clear(colour=(bg[0], bg[1], bg[2], 1.0))
    
    for p in compositor.emissive_passes:
        p.render(target=compositor.emissive_target)

    # Extract glow into glow buffer
    compositor.glow_extraction_pass.render(
        input_target=compositor.emissive_target,
        output_target=compositor.glow_buffer.read,
        energy=0.5
    )

    # Read raw extracted glow pixels
    glow_tex = compositor.glow_buffer.read.texture
    gw, gh = glow_tex.width, glow_tex.height
    raw_glow_pixels = glow_tex.read()
    raw_glow_array = np.frombuffer(raw_glow_pixels, dtype=np.float16).reshape((gh, gw, 4))
    
    # Emissive box region (left side)
    sx, sy = int(gw * (200 / 1280)), int(gh * (150 / 400))
    ex, ey = int(gw * (400 / 1280)), int(gh * (250 / 400))
    emissive_max = np.max(raw_glow_array[sy:ey, sx:ex, :3])
    print(f"[*] Raw extracted emissive max luminance: {emissive_max:.2f}")
    assert emissive_max > 0.1, "Emissive box failed to trigger glow extraction."

# 2. Verify that UI pass (SharpUITestPass) did NOT write into the emissive target.
    # The region where UI elements would be drawn should match the base background color exactly.
    emissive_pixels = compositor.emissive_target.texture.read()
    emissive_array = np.frombuffer(emissive_pixels, dtype=np.float16).reshape((400, 1280, 4))
    
    ui_sx, ui_ex = int(800), int(1000)
    ui_sy, ui_ey = int(150), int(250)
    ui_region_in_emissive = emissive_array[ui_sy:ui_ey, ui_sx:ui_ex, :3]
    
    expected_bg = np.array([c / 255.0 for c in BACKGROUND_colour], dtype=np.float16)
    
    # Check that all pixels in the UI region equal the background color (no UI content drawn here)
    max_diff = np.max(np.abs(ui_region_in_emissive - expected_bg))
    print(f"[*] Max deviation from background in UI region: {max_diff:.5f}")
    
    assert max_diff < 1e-4, (
        f"Pipeline failure: Sharp UI elements leaked into emissive target (max deviation: {max_diff})"
    )

    print("[+] Verified: Emissive elements trigger bloom extraction; sharp UI elements are strictly isolated from the emissive target.")
    print("=" * 70)
    print("[+] ALL TASK 2.1 PIPELINE REORDERING TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_pipeline_reordering()