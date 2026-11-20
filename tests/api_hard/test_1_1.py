#!/usr/bin/env python3
"""
Test Harness for Task 1.1: Core Foundational Definitions (base_defs.py)
Verifies:
1. Python 3.10+ StrEnum equality with raw strings (e.g., Channel.LEFT == 'left').
2. Identity and hashing behaviour in dictionaries and sets.
3. Case-insensitivity parsing helper (Channel.from_str('LEFT')).
4. British English alignment with American aliases (HorizontalAlign.CENTRE == HorizontalAlign.CENTER).
5. Clean package-level imports from pyvisualiser.
"""

import os
import sys

# Ensure repo root and src are on python path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from pyvisualiser.core.base_defs import (
    Channel,
    Orientation,
    HorizontalAlign,
    VerticalAlign,
    ThemeColour,
    MetadataKey,
    RenderLayer,
)


def test_base_defs():
    print("=" * 70)
    print("Running Task 1.1 Verification Test: base_defs.py")
    print("=" * 70)

    # 1. String Equality (Backwards Compatibility)
    print("[*] Test 1: Testing String Equality...")
    assert Channel.LEFT == "left", "Channel.LEFT must equal 'left'"
    assert Channel.RIGHT == "right", "Channel.RIGHT must equal 'right'"
    assert Channel.MONO == "mono", "Channel.MONO must equal 'mono'"

    assert Orientation.VERTICAL == "vert", "Orientation.VERTICAL must equal 'vert'"
    assert Orientation.HORIZONTAL == "horz", "Orientation.HORIZONTAL must equal 'horz'"

    assert HorizontalAlign.LEFT == "left"
    assert HorizontalAlign.CENTRE == "centre"
    assert HorizontalAlign.RIGHT == "right"
    assert HorizontalAlign.COLUMN == "col"

    assert VerticalAlign.TOP == "top"
    assert VerticalAlign.MIDDLE == "middle"
    assert VerticalAlign.BOTTOM == "bottom"
    assert VerticalAlign.ROW == "row"

    assert ThemeColour.FOREGROUND == "foreground"
    assert ThemeColour.BACKGROUND == "background"
    assert ThemeColour.ALERT == "alert"

    assert MetadataKey.TRACK == "track"
    assert MetadataKey.ARTIST == "artist"
    assert MetadataKey.SAMPLE_RATE == "sample_rate"
    print("[+] String equality verified for all enum members.")

    # 2. Aliases and British English
    print("[*] Test 2: Testing Aliases & British English...")
    assert HorizontalAlign.CENTRE == HorizontalAlign.CENTER, "CENTRE must alias CENTER"
    assert Orientation.VERTICAL == Orientation.VERT
    assert Orientation.HORIZONTAL == Orientation.HORZ
    print("[+] Aliases verified.")

    # 3. String Methods & Dictionary Key Usage
    print("[*] Test 3: Testing Dictionary Key & Set Hashing...")
    sample_dict = {
        Channel.LEFT: 10,
        "left": 20,  # Should overwrite or match cleanly
    }
    # In Python StrEnum, Channel.LEFT and "left" hash identically
    assert sample_dict[Channel.LEFT] == 20
    assert sample_dict["left"] == 20

    channel_set = {Channel.LEFT, Channel.RIGHT, "left"}
    assert len(channel_set) == 2, "Set should collapse identical enum and string"
    print("[+] Dictionary and Set semantics verified.")

    # 4. Helper Deserialisation
    print("[*] Test 4: Testing from_str() helper...")
    assert Channel.from_str("left") == Channel.LEFT
    assert Channel.from_str("RIGHT") == Channel.RIGHT
    assert Channel.from_str(" Mono ") == Channel.MONO

    try:
        Channel.from_str("surround")
        assert False, "Unknown channel must raise ValueError"
    except ValueError:
        pass
    print("[+] from_str() parsing verified.")

    # 5. Root Package Import Verification
    print("[*] Test 5: Verifying exports from root pyvisualiser module...")
    import pyvisualiser
    assert hasattr(pyvisualiser, "Channel")
    assert hasattr(pyvisualiser, "Orientation")
    assert hasattr(pyvisualiser, "HorizontalAlign")
    assert hasattr(pyvisualiser, "VerticalAlign")
    assert hasattr(pyvisualiser, "ThemeColour")
    assert hasattr(pyvisualiser, "MetadataKey")
    assert hasattr(pyvisualiser, "RenderLayer")
    print("[+] Root package exports verified.")

    print("=" * 70)
    print("[+] ALL TASK 1.1 TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_base_defs()