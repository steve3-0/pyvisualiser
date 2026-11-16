#!/usr/bin/env python3
"""
Test Harness for Task 3.1: Pythonic Decoupling of Platform & UI Frames
Verifies:
1. Platform uses composition (holds distinct .audio, .media, .gfx, .hw attributes).
2. Transparent delegation preserves backward compatibility for frames.
3. Snapshots (AudioSnapshot, MediaSnapshot) instantiate and decouple cleanly.
"""

import os
import sys

# Force headless dummy driver for testing platform logic without hardware displays
os.environ["SDL_VIDEODRIVER"] = "dummy"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

import pygame
pygame.init()

from unittest.mock import MagicMock
from pyvisualiser.core.state import AudioSnapshot, MediaSnapshot
from pyvisualiser.core.screenhandler import Platform
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.presets import EmbeddedHiFiProfile

ProfileManager.set_profile(EmbeddedHiFiProfile)


def test_platform_composition_and_state():
    print("=" * 70)
    print("Running Task 3.1 Verification Test: Decoupled Platform & State Carriers")
    print("=" * 70)

    # 1. Test Snapshots in Isolation (Zero Hardware Dependency)
    print("[*] Test 1: Testing AudioSnapshot and MediaSnapshot...")
    audio_snap = AudioSnapshot(
        vu={'left': 0.7, 'right': 0.8, 'mono': 0.75},
        bass=0.6,
        bpm=120.0,
        is_beat=True
    )
    assert audio_snap.vu['mono'] == 0.75
    assert audio_snap.is_beat is True

    media_snap = MediaSnapshot(
        track="Sultans of Swing",
        artist="Dire Straits",
        album="Dire Straits",
        duration=348.0,
        elapsed=174.0
    )
    assert media_snap.elapsedpc == 0.5
    assert media_snap.remaining == 174.0
    print("[+] Verified: Snapshots calculate duration and values with zero dependencies.")

    # 2. Test Platform Composition & Delegation
    print("\n[*] Test 2: Testing Platform Composition & Delegation...")
    mock_events = MagicMock()
    # Use CPU driver ('mac') for headless testing without hardware display/OpenGL constraints
    hw_config = {'gfx': 'mac', 'loopback': 'mock', 'roon_zone': 'mock'}

    platform = Platform(mock_events, hw_config)

    # Verify subsystems exist as distinct composed attributes
    assert hasattr(platform, 'audio'), "Missing platform.audio"
    assert hasattr(platform, 'media'), "Missing platform.media"
    assert hasattr(platform, 'gfx'), "Missing platform.gfx"
    assert hasattr(platform, 'hw'), "Missing platform.hw"
    print("[+] Verified: Platform uses composition (holds distinct .audio, .media, .gfx, .hw).")

    # Verify transparent backward-compatible delegation
    assert hasattr(platform, 'vu'), "Delegation failed: platform.vu not accessible"
    assert hasattr(platform, 'track'), "Delegation failed: platform.track not accessible"
    assert hasattr(platform, 'renderer'), "Delegation failed: platform.renderer not accessible"
    assert hasattr(platform, 'volume'), "Delegation failed: platform.volume not accessible"
    print("[+] Verified: Transparent delegation forwards lookups to correct subsystems.")

    # Verify snapshot generators
    snap_a = platform.get_audio_snapshot()
    snap_m = platform.get_media_snapshot()
    assert isinstance(snap_a, AudioSnapshot)
    assert isinstance(snap_m, MediaSnapshot)
    print("[+] Verified: Platform cleanly generates typed immutable snapshots.")

    # Teardown
    platform.stop()

    print("\n" + "=" * 70)
    print("[+] ALL TASK 3.1 DECOUPLING TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_platform_composition_and_state()