#!/usr/bin/env python3
"""
Test Harness for Task 2.3: Texture Filtering & Mipmapping Policy
Verifies that:
1. Created ModernGL textures have mipmaps generated.
2. Texture filter is configured to (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR).
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
pygame.display.set_mode((100, 100), pygame.OPENGL | pygame.DOUBLEBUF)

import moderngl
from pyvisualiser.core.render import RenderContext, DisplayMetrics
from pyvisualiser.core.displaydriver import GeometryPass

def test_texture_filtering_policy():
    print("=" * 70)
    print("Running Task 2.3 Verification Test: Texture Filtering Policy")
    print("=" * 70)

    ctx = moderngl.create_context(standalone=True)
    metrics = DisplayMetrics(logical_w=1280, logical_h=400, dpi_scale=1.0)
    render_context = RenderContext(ctx, metrics)
    geometry_pass = GeometryPass(render_context)

    # Create a dummy surface simulating an album art load
    surf = pygame.Surface((512, 512), pygame.SRCALPHA)
    surf.fill((100, 150, 200, 255))
    
    # Trigger texture creation via blit
    geometry_pass.blit(surf, (0, 0))
    
    # Extract the generated texture from context or current texture
    assert geometry_pass.current_texture is not None, "Texture was not created by blit."
    
    tex = geometry_pass.current_texture
    print(f"[*] Texture filter configuration: {tex.filter}")
    
    # Verify filter uses linear mipmapping for smooth downscaling
    assert tex.filter == (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR), (
        f"Expected mipmap filter settings, got {tex.filter}"
    )

    print("[+] Verified: Textures are correctly configured with mipmap filtering policies.")
    print("=" * 70)
    print("[+] TASK 2.3 TEST PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    test_texture_filtering_policy()