#!/usr/bin/env python3
"""
Test Harness for Phase 4.1: Component Dataclass API Harmonisation
Verifies that VUMeter, VUFrame, SpectrumFrame, MetaImages, TextFrame, MetaData, 
PlayProgressFrame, and ShaderFrame instantiate cleanly using FrameConfig and harmonised visuals.
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
import numpy as np
import moderngl
from pyvisualiser.core.render import RenderContext, DisplayMetrics
from pyvisualiser.core.base_defs import Channel, MetadataKey
from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.styles.ballistics import MeterBallistics, FFTBallistics
from pyvisualiser.styles.styles import (
    VUMeterStyle, BarStyle, SpectrumStyle, ImageStyle, TextStyle, ProgressStyle, ShaderStyle
)
from pyvisualiser.visualisers.vumeters import VUMeter, VUFrame
from pyvisualiser.visualisers.spectrum import SpectrumFrame
from pyvisualiser.visualisers.metadata import MetaImages, TextFrame, MetaData, PlayProgressFrame, ArtFrame, MetaDataFrame
from pyvisualiser.visualisers.glvisualisers import ShaderFrame
from pyvisualiser.core.framecore import Frame
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.presets import EmbeddedHiFiProfile
from pyvisualiser.core.state import AudioSnapshot, MediaSnapshot

from pyvisualiser.styles.styles import (
    BarStyle, SpectrumStyle, OscillogrammeStyle, TextStyle
)
from pyvisualiser.visualisers.metadata import CircularProgress
from pyvisualiser.visualisers.oscillogramme import (
    Oscilogramme, OscilogrammeBar, SamplesFrame
)
from pyvisualiser.visualisers.spectrum import (
    Diamondiser, Octaviser
)
from pyvisualiser.visualisers.vumeters import (
    VU2chFrame, VUFlipFrame
)
# from ../../tests.test_spectrum import StereoSpectrumFrame, Spectrum2chFrame

class MockPlatform:
    def __init__(self, w=1280, h=400):
        self.W = w
        self.H = h
        self.wh = (w, h)
        self.boundary = [0, 0, w - 1, h - 1]
        self.vu = {'left': 0.5, 'right': 0.5, 'mono': 0.5}
        self.track = "Test Track"
        self.artist = "Test Artist"
        self.album = "Test Album"
        self.duration = 300.0
        self.elapsed = 150.0
        self.framesize = 1024
        self.samples = {
            'mono': np.zeros(1024, dtype=np.int16),
            'left': np.zeros(1024, dtype=np.int16),
            'right': np.zeros(1024, dtype=np.int16)
        }
        # Standalone headless ModernGL context for safe headless shader testing
        self.mgl_ctx = moderngl.create_context(standalone=True)
        self.metrics = DisplayMetrics(logical_w=w, logical_h=h)
        self.render_context = RenderContext(self.mgl_ctx, self.metrics)

        class MockRenderer:
            def draw_rect(self, *args, **kwargs): pass
            def draw_line(self, *args, **kwargs): pass
            def draw_lines(self, *args, **kwargs): pass
            def blit(self, *args, **kwargs): pass
        self.renderer = MockRenderer()

        class MockDriver:
            def __init__(self, rc):
                self.render_context = rc
                class MockComp:
                    def add_pre_pass(self, p): pass
                    def add_ui_pass(self, p): pass
                self.compositor = MockComp()

        self.gfx_driver = MockDriver(self.render_context)

    def createBands(self, spacing, flast=None):
        return [100.0 * (i + 1) for i in range(24)]

    def packFFT(self, freqs, channel):
        return [0.5] * len(freqs)

    def create_outline(self, frame, outline):
        class Dummy:
            w = 0
            def draw(self): pass
        return Dummy()

    def reduceSamples(self, channel, reduce_by, rms=True):
        return [0.5] * 32

    def create_background(self, frame, background):
        class Dummy:
            def draw(self): pass
            def is_opaque(self): return True
            def per_frame_update(self): pass
        return Dummy()


def test_component_harmonisation():
    print("=" * 70)
    print("Running Verification Test: Component Harmonisation (4.1)")
    print("=" * 70)
    ProfileManager.set_profile(EmbeddedHiFiProfile)

    plat = MockPlatform()
    root = Frame(plat, config=FrameConfig())
    audio_snap = AudioSnapshot()
    media_snap = MediaSnapshot(duration=240.0, elapsed=60.0)

    # 1. VUMeter
    vu = VUMeter(root, channel=Channel.LEFT, config=FrameConfig(), visuals=VUMeterStyle(), ballistics=MeterBallistics())
    assert vu.channel == Channel.LEFT
    print("[+] VUMeter constructor harmonised.")

    # 2. VUFrame
    vuf = VUFrame(root, channel=Channel.RIGHT, config=FrameConfig(), visuals=BarStyle(barsize_pc=0.6))
    assert vuf.bar_style.barsize_pc == 0.6
    print("[+] VUFrame constructor harmonised.")

    # 3. SpectrumFrame
    spec = SpectrumFrame(root, channel=Channel.MONO, config=FrameConfig(), visuals=SpectrumStyle(), ballistics=FFTBallistics())
    assert spec.channel == Channel.MONO
    print("[+] SpectrumFrame constructor harmonised.")

    # 4. MetaImages
    img = MetaImages(root, key=MetadataKey.ALBUM, config=FrameConfig(), visuals=ImageStyle(opacity=0.9))
    assert img.image_style.opacity == 0.9
    print("[+] MetaImages constructor harmonised.")

    img = ArtFrame(root, config=FrameConfig(), visuals=ImageStyle(opacity=0.9))
    assert img.image_style.opacity == 0.9
    print("[+] ArtFrame constructor harmonised.")

    # 5. TextFrame & MetaData
    txt = TextFrame(root, text="Hello Hi-Fi", config=FrameConfig(), visuals=TextStyle(colour="light"))
    assert txt.style.colour == "light"

    meta = MetaData(root, key=MetadataKey.ARTIST, config=FrameConfig(), visuals=TextStyle())
    assert meta.metadata_key == "artist"
    print("[+] TextFrame & MetaData constructors harmonised.")

    # 6. PlayProgressFrame
    prog = PlayProgressFrame(root, config=FrameConfig(), visuals=ProgressStyle())
    assert isinstance(prog.bar_style, BarStyle)
    print("[+] PlayProgressFrame constructor harmonised.")

    # 7. ShaderFrame
    shader = ShaderFrame(root, shader=ShaderStyle(shader_name="liquidorb", colour="alert"))
    assert shader.shader_style.shader_name == "liquidorb"
    print("[+] ShaderFrame constructor harmonised.")

   # 1. CircularProgress
    print("[*] 1. Testing CircularProgress...")
    circ = CircularProgress(root, config=FrameConfig(square=True), visuals=TextStyle(colour='alert'))
    circ.update_screen(audio=audio_snap, media=media_snap)
    print("[+] CircularProgress verified.")

    # 2. Oscilogramme & OscilogrammeBar
    print("\n[*] 2. Testing Oscilogramme & OscilogrammeBar...")
    osc = Oscilogramme(root, channel=Channel.LEFT, config=FrameConfig(), visuals=OscillogrammeStyle())
    osc.update_screen(audio=audio_snap, media=media_snap)

    osc_bar = OscilogrammeBar(root, channel=Channel.MONO, config=FrameConfig(), visuals=OscillogrammeStyle(), bar_visuals=BarStyle(led_gap=0))
    osc_bar.update_screen(audio=audio_snap, media=media_snap)
    print("[+] Oscilogramme & OscilogrammeBar verified.")

    # 3. SamplesFrame
    print("\n[*] 3. Testing SamplesFrame...")
    samples_f = SamplesFrame(root, config=FrameConfig(), visuals=OscillogrammeStyle())
    samples_f.update_screen(audio=audio_snap, media=media_snap)
    print("[+] SamplesFrame verified.")

    # 4. Diamondiser & Octaviser
    print("\n[*] 4. Testing Diamondiser & Octaviser...")
    diam = Diamondiser(root, channel=Channel.MONO, config=FrameConfig(square=True), visuals=SpectrumStyle(barsize_pc=1.0), ballistics=FFTBallistics())
    diam.update_screen(audio=audio_snap, media=media_snap)

    octav = Octaviser(root, channel=Channel.MONO, config=FrameConfig(), visuals=SpectrumStyle())
    octav.update_screen(audio=audio_snap, media=media_snap)
    print("[+] Diamondiser & Octaviser verified.")

    # # 5. StereoSpectrumFrame & Spectrum2chFrame
    # print("\n[*] 5. Testing StereoSpectrumFrame & Spectrum2chFrame...")
    # stereo_spec = StereoSpectrumFrame(root, config=FrameConfig(), visuals=SpectrumStyle(barw_min=10))
    # stereo_spec.update_screen(audio=audio_snap, media=media_snap)

    # spec_2ch = Spectrum2chFrame(root, config=FrameConfig())
    # spec_2ch.update_screen(audio=audio_snap, media=media_snap)
    # print("[+] StereoSpectrumFrame & Spectrum2chFrame verified.")

    # 6. VU2chFrame & VUFlipFrame
    print("\n[*] 6. Testing VU2chFrame & VUFlipFrame...")
    vu_2ch = VU2chFrame(root, config=FrameConfig(), visuals=BarStyle(orient='vert'), ballistics=MeterBallistics())
    vu_2ch.update_screen(audio=audio_snap, media=media_snap)

    vu_flip = VUFlipFrame(root, config=FrameConfig(), visuals=BarStyle(orient='horz'), ballistics=MeterBallistics())
    vu_flip.update_screen(audio=audio_snap, media=media_snap)
    print("[+] VU2chFrame & VUFlipFrame verified.")


    print("\n" + "=" * 70)
    print("[+] ALL COMPONENT HARMONISATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_component_harmonisation()