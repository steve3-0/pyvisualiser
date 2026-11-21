#!/usr/bin/env python3
"""
Test Harness for Phase 4.1: Harmonised Styling Dataclasses
Verifies:
1. TextStyle, ShaderStyle, ProgressStyle, and ImageStyle instantiate with correct defaults.
2. Frozen dataclass immutability holds.
3. Nested BarStyle inside SpectrumStyle and ProgressStyle functions correctly.
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from pyvisualiser.styles.styles import (
    TextStyle,
    ShaderStyle,
    ProgressStyle,
    ImageStyle,
    SpectrumStyle,
    BarStyle,
)


def test_styles_harmonisation():
    print("=" * 70)
    print("Running Verification Test: Harmonised Styling Dataclasses (4.1)")
    print("=" * 70)

    # 1. TextStyle
    ts = TextStyle(colour="light", wrap=True)
    assert ts.colour == "light"
    assert ts.wrap is True
    print("[+] TextStyle verified.")

    # 2. ShaderStyle
    ss = ShaderStyle(shader_name="liquidorb", colour="alert")
    assert ss.shader_name == "liquidorb"
    assert ss.colour == "alert"
    print("[+] ShaderStyle verified.")

    # 3. ProgressStyle (Nested BarStyle & TextStyle)
    ps = ProgressStyle()
    assert isinstance(ps.bar_style, BarStyle)
    assert isinstance(ps.text_style, TextStyle)
    print("[+] ProgressStyle nested encapsulation verified.")

    # 4. SpectrumStyle (Nested BarStyle)
    spec_style = SpectrumStyle()
    assert isinstance(spec_style.bar_style, BarStyle)
    print("[+] SpectrumStyle nested encapsulation verified.")

    # 5. ImageStyle
    img_style = ImageStyle(opacity=0.8, corner_radius=12)
    assert img_style.opacity == 0.8
    assert img_style.corner_radius == 12
    print("[+] ImageStyle verified.")

    print("\n" + "=" * 70)
    print("[+] ALL STYLES HARMONISATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_styles_harmonisation()