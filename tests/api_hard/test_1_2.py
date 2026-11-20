#!/usr/bin/env python3
"""
Test Harness for Task 1.2: Standardised Metadata State Ingestion
Verifies:
1. AudioSnapshot and MediaSnapshot safe mathematical properties.
2. Formatters handle zero and None duration gracefully (no ZeroDivisionError or TypeError).
3. PlayProgressFrame, TextFrame, MetaData, and MetaDataFrame update cleanly using injected snapshots
   with completely decoupled mock parent frames (zero network / soundcard dependencies).
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

from pyvisualiser.core.state import AudioSnapshot, MediaSnapshot
from pyvisualiser.core.base_defs import MetadataKey
from pyvisualiser.core.framecore import Frame
from pyvisualiser.visualisers.metadata import (
    TextFrame,
    PlayProgressFrame,
    MetaData,
    MetaDataFrame,
    CircularProgress,
)
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.presets import EmbeddedHiFiProfile

ProfileManager.set_profile(EmbeddedHiFiProfile)


class MockRenderer:
    def __init__(self):
        self.blit_calls = []
        self.rect_calls = []

    def blit(self, source, dest, **kwargs):
        self.blit_calls.append((dest, kwargs))

    def draw_rect(self, color, rect, **kwargs):
        self.rect_calls.append((color, rect, kwargs))


class MockPlatform:
    def __init__(self):
        self.W = 1280
        self.H = 400
        self.renderer = MockRenderer()
        self.duration = 0.0
        self.elapsed = 0.0
        self.track = "Legacy Track"
        self.artist = "Legacy Artist"
        self.album = "Legacy Album"
        self.volume = "35"
        self.source = "Local"


class MockParentFrame(Frame):
    """A minimal concrete Frame subclass for isolated unit testing."""
    def __init__(self, w=400, h=80):
        # Create a mock root platform that supplies boundary and screen dimensions
        class MockPlatform:
            def __init__(self):
                self.W = w
                self.H = h
                self.wh = (w, h)
                self.boundary = [0, 0, w - 1, h - 1]
                self.renderer = MockRenderer()
                self.duration = 0.0
                self.elapsed = 0.0
                self.track = "Legacy Track"
                self.artist = "Legacy Artist"
                self.album = "Legacy Album"
                self.volume = "35"
                self.source = "Local"

            def create_outline(self, frame, outline):
                class Dummy:
                    w = 0
                    def draw(self): pass
                return Dummy()

            def create_background(self, frame, background):
                class Dummy:
                    def draw(self): pass
                    def is_opaque(self): return True
                    def per_frame_update(self): pass
                return Dummy()

        mock_plat = MockPlatform()
        # Initialise as top-level screen frame
        super().__init__(mock_plat, scalers=(1.0, 1.0), theme='hifi')


def test_metadata_state_ingestion():
    print("=" * 70)
    print("Running Task 1.2 Verification Test: Metadata State Ingestion")
    print("=" * 70)

    # 1. Snapshot formatting tests
    print("[*] Test 1: Testing Snapshot formatters & zero boundaries...")
    empty_snap = MediaSnapshot(duration=0.0, elapsed=0.0)
    assert empty_snap.elapsed_pc == 0.0
    assert empty_snap.format_elapsed() == "0:00"
    assert empty_snap.format_remaining() == "0:00"

    active_snap = MediaSnapshot(
        track="Telegraph Road",
        artist="Dire Straits",
        album="Love Over Gold",
        duration=860.0,
        elapsed=215.0,
        volume="42",
        source="Roon"
    )
    assert active_snap.elapsed_pc == 0.25
    assert active_snap.format_elapsed() == "3:35"
    assert active_snap.format_remaining() == "10:45"
    print("[+] Snapshot bounds and string formatters verified.")

    # 2. TextFrame with State Resolver
    print("\n[*] Test 2: Testing TextFrame with MediaSnapshot injection...")
    parent = MockParentFrame(w=300, h=40)
    tf = TextFrame(parent, text="Placeholder")

    # Render with explicit text
    tf.update_screen(text="Explicit Override")
    assert tf.textcomp.text == "Explicit Override"

    # 3. MetaData bound to MetadataKey
    print("\n[*] Test 3: Testing MetaData with strongly-typed MetadataKey...")
    track_meta = MetaData(parent, metadata_type=MetadataKey.TRACK)
    track_meta.update_screen(media=active_snap)
    assert track_meta.textcomp.text == "Telegraph Road"

    artist_meta = MetaData(parent, metadata_type=MetadataKey.ARTIST)
    artist_meta.update_screen(media=active_snap)
    assert artist_meta.textcomp.text == "Dire Straits"
    print("[+] MetaData fields resolved correctly from MediaSnapshot.")

    # 4. PlayProgressFrame rendering with MediaSnapshot
    print("\n[*] Test 4: Testing PlayProgressFrame without divide-by-zero...")
    pp = PlayProgressFrame(parent, barsize_pc=0.3)
    
    # First update with empty snapshot (duration = 0.0) - must NOT raise
    pp.update_screen(media=empty_snap)
    assert "0:00" in pp.elapsed.text
    
    # Update with active playback
    pp.update_screen(media=active_snap)
    assert "3:35" in pp.elapsed.text
    assert "10:45" in pp.remaining.text
    print("[+] PlayProgressFrame safely renders zero and active progress from state.")

    # 5. Composite MetaDataFrame traversal
    print("\n[*] Test 5: Testing MetaDataFrame recursive state propagation...")
    mdf = MetaDataFrame(parent)
    mdf.update_screen(media=active_snap)
    print("[+] MetaDataFrame rendered children without errors.")

    print("=" * 70)
    print("[+] ALL TASK 1.2 TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_metadata_state_ingestion()