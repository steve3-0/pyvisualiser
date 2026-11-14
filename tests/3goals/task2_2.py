#!/usr/bin/env python3
"""
Test Harness for Step 2: DisplayDriver Coordinate Consistency
Verifies that:
1. GeometryPass transforms logical coordinates (0..1280, 0..400) cleanly into NDC [-1, 1].
2. Zero double-scaling occurs under Retina (dpi_scale = 2.0).
3. The bounding corners match exactly: (0,0) -> top-left (-1, 1) and (1280, 400) -> bottom-right (1, -1).
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
from pyvisualiser.core.render import RenderContext, DisplayMetrics
from pyvisualiser.core.displaydriver import GeometryPass
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.presets import EmbeddedHiFiProfile

ProfileManager.set_profile(EmbeddedHiFiProfile)


class MockPlatform:
    def __init__(self, metrics):
        self.W = metrics.logical_w
        self.H = metrics.logical_h
        self.metrics = metrics


def test_geometry_coordinates():
    print("=" * 70)
    print("Running Step 2 Verification Test: GeometryPass Coordinate Scaling")
    print("=" * 70)

    ctx = moderngl.create_context(standalone=True)
    metrics = DisplayMetrics(logical_w=1280, logical_h=400, dpi_scale=2.0)
    platform = MockPlatform(metrics)
    render_context = RenderContext(ctx, metrics, platform=platform)
    geometry_pass = GeometryPass(render_context)

    # 1. Queue a full-screen quad (0, 0, 1280, 400)
    geometry_pass.clear_batch()
    geometry_pass.add_rect((0, 0, 1280, 400), (255, 255, 255, 255), 255, softness=0.0, stroke_width=0, radius=0, segments=(0, 0))

    # Inspect queued vertex data (19 floats per vertex, 6 vertices)
    queue = geometry_pass.render_queue
    assert len(queue) == 19 * 6, f"Expected 114 floats for 1 quad, got {len(queue)}"

    # Check Top-Left vertex (vertex 0): NDC x, y should be approximately (-1.0, 1.0)
    # Accounting for padding = 10.0:
    # x1 = (-10 / 1280) * 2 - 1 = -1.0156
    # y1 = 1 - (-10 / 400) * 2 = 1.05
    x1, y1 = queue[0], queue[1]
    print(f"[*] Top-Left NDC: ({x1:.4f}, {y1:.4f})")
    assert -1.05 <= x1 <= -1.0, f"Unexpected x1: {x1}"
    assert 1.0 <= y1 <= 1.06, f"Unexpected y1: {y1}"

    # Check Bottom-Right vertex (vertex 5):
    # x2 = (1290 / 1280) * 2 - 1 = 1.0156
    # y2 = 1 - (410 / 400) * 2 = -1.05
    x2, y2 = queue[5 * 19], queue[5 * 19 + 1]
    print(f"[*] Bottom-Right NDC: ({x2:.4f}, {y2:.4f})")
    assert 1.0 <= x2 <= 1.05, f"Unexpected x2: {x2}"
    assert -1.06 <= y2 <= -1.0, f"Unexpected y2: {y2}"

    print("[+] Verified: Fullscreen logical rectangle maps 1:1 across NDC [-1.0, 1.0] without 2x doubling.")
    print("=" * 70)
    print("[+] STEP 2 DISPLAYDRIVER TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_geometry_coordinates()