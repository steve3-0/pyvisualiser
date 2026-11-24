#!/usr/bin/env python3
"""
Background and Surface Effects Test Screens
Part of pyvisualiser v2.1.0 (Refactored to pristine dataclass API)
"""

from pyvisualiser.core.base_defs import Channel, MetadataKey, HorizontalAlign, VerticalAlign
from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.framecore import Frame, ColFramer, RowFramer
from pyvisualiser.styles.styles import (
    BackgroundStyle,
    OutlineStyle,
    VignetteStyle,
    NoiseStyle,
    AmbientGlowStyle,
    ReactiveGlowStyle,
    PeakAccentStyle,
    StarfieldStyle,
    CloudStyle,
    EdgeLightStyle,
    ImageStyle,
    TextStyle,
    BarStyle,
    BarEffects,
    ShadowStyle,
    VUBarStyle,
)
from pyvisualiser.visualisers.vumeters import VU2chFrame, VU2chHorzFrame
from pyvisualiser.visualisers.metadata import MetaImages, TextFrame
from pyvisualiser.visualisers.oscillogramme import Oscilogramme


class F9(Frame):
    """Multi-layer background test: textures, outlines, and semi-transparent panels."""
    @property
    def title(self):
        return 'Background layers test'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        bg = BackgroundStyle(texture_path='stream.png', texture_opacity=0.78)
        super().__init__(platform, config=FrameConfig(theme='blue', background=bg, padding=30))

        sub_bg = BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.5)
        subframe = self.add_cols(ratios=(1, 1, 1), padpc=0.1, config=FrameConfig(padding=40, background=sub_bg))

        # 1. Dual Channel Bar VU
        vubar_vis = VUBarStyle(barsize_pc=1.0, bar_style=BarStyle(led_h=7, led_gap=2))
        out_vu = OutlineStyle(colour='foreground', width=5)
        bg_vu = BackgroundStyle(colour='mid', colour_opacity=0.39)
        subframe += VU2chFrame(
            subframe,
            visuals=vubar_vis,
            config=FrameConfig(outline=out_vu, background=bg_vu)
        )

        # 2. Album Art
        subframe += MetaImages(
            subframe,
            key=MetadataKey.ALBUM,
            visuals=ImageStyle(opacity=1.0)
        )

        # 3. Text Label
        out_txt = OutlineStyle(colour='foreground', width=1)
        bg_txt = BackgroundStyle(colour='dark', colour_opacity=0.78)
        subframe += TextFrame(
            subframe,
            text='Volume',
            config=FrameConfig(outline=out_txt, background=bg_txt, padding=0),
            visuals=TextStyle(colour='foreground', justify=('right', 'middle'))
        )


class BloomImageTestScreen(Frame):
    """Bloom & Additive Glow over image backgrounds."""
    @property
    def title(self):
        return 'Bloom Effect over Image Background'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        bg = BackgroundStyle(texture_path='artist', texture_opacity=0.6)
        super().__init__(platform, config=FrameConfig(background=bg))

        cols = self.add_cols(ratios=(1, 2), config=FrameConfig(padding=20))

        # Left: Album Art with outline
        out_art = OutlineStyle(colour='light', width=2)
        cols += MetaImages(
            cols,
            key=MetadataKey.ALBUM,
            visuals=ImageStyle(opacity=0.78),
            config=FrameConfig(outline=out_art)
        )

        # Right: Horizontal Stereo VU with BarEffects bloom
        eff = BarEffects(threshold=0.5, scale=2.0, blur=0.8, alpha=80)
        bar_vis = VUBarStyle(barsize_pc=0.8, bar_style=BarStyle(orient='horz', effects=eff))
        bg_vu = BackgroundStyle(colour='dark', colour_opacity=0.0)
        cols += VU2chHorzFrame(
            cols,
            visuals=bar_vis,
            config=FrameConfig(background=bg_vu)
        )


class BackgroundEffectsScreen1(Frame):
    """Background procedural effects without image textures."""
    @property
    def title(self):
        return 'Background Effects 1: No Texture'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        s0 = BackgroundStyle(
            colour='background',
            ambient_glow=AmbientGlowStyle(colour='foreground', opacity=0.7, radius=0.5, softness=0.5)
        )
        super().__init__(platform, config=FrameConfig(theme='std', background=s0))

        outline = OutlineStyle(colour='mid', width=3, radius=5)
        rows = self.add_rows(padpc=0.02, config=FrameConfig(padding=20, outline=outline))

        top = rows.add_cols(padpc=0.02, config=FrameConfig(padding=10))
        bot = rows.add_cols(padpc=0.02, config=FrameConfig(padding=10))

        # 1. Vignette (Top-Left)
        s1 = BackgroundStyle(colour='mid', vignette=VignetteStyle(strength=1.0, radius=0.2, softness=0.8))
        top += TextFrame(
            top,
            text='Vignette (Strong)',
            config=FrameConfig(background=s1, outline=outline),
            visuals=TextStyle(colour='foreground', justify=('centre', 'middle'))
        )

        # 2. Noise & Peak Accent (Top-Right)
        peak_style = PeakAccentStyle(colour='alert')
        s2 = BackgroundStyle(colour='mid', noise=NoiseStyle(strength=0.2, speed=0.5), peak_accent=peak_style)
        top += TextFrame(
            top,
            text='Noise (Heavy)',
            config=FrameConfig(background=s2, outline=outline),
            visuals=TextStyle(colour='light', justify=('centre', 'middle'))
        )

        # 3. Ambient Glow (Bottom-Left)
        s3 = BackgroundStyle(colour='dark', ambient_glow=AmbientGlowStyle(colour='foreground', opacity=0.8, radius=0.5, softness=0.2))
        bot += TextFrame(
            bot,
            text='Ambient Glow (Pulse)',
            config=FrameConfig(background=s3, outline=outline),
            visuals=TextStyle(colour='foreground', justify=('centre', 'middle'))
        )

        # 4. Reactive Glow (Bottom-Right)
        s4 = BackgroundStyle(colour='dark', reactive_glow=ReactiveGlowStyle(colour='light', attack=0.1, decay=0.1, threshold=0.0))
        bot += TextFrame(
            bot,
            text='Reactive Glow (Audio)',
            config=FrameConfig(background=s4, outline=outline),
            visuals=TextStyle(colour='light', justify=('centre', 'middle'))
        )


class BackgroundEffectsScreen2(Frame):
    """Background procedural effects combined with textures."""
    @property
    def title(self):
        return 'Background Effects 2: With Texture'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='zomp'))

        rows = self.add_rows(config=FrameConfig(padding=30))
        top = rows.add_cols(padpc=0.02, config=FrameConfig(padding=10))
        bot = rows.add_cols(padpc=0.02, config=FrameConfig(padding=10))

        tex = 'metal.jpg'

        # 1. Texture + Vignette
        s1 = BackgroundStyle(colour='foreground', texture_path=tex, texture_opacity=0.1, vignette=VignetteStyle(strength=1.8, radius=0.2))
        top += TextFrame(
            top,
            text='Tex + Vignette',
            config=FrameConfig(background=s1),
            visuals=TextStyle(colour='light', justify=('centre', 'middle'))
        )

        # 2. Texture + Noise
        s2 = BackgroundStyle(colour='background', texture_path=tex, texture_opacity=0.1, noise=NoiseStyle(strength=0.15))
        top += TextFrame(
            top,
            text='Tex + Noise',
            config=FrameConfig(background=s2),
            visuals=TextStyle(colour='light', justify=('centre', 'middle'))
        )

        # 3. Texture + Ambient Glow
        s3 = BackgroundStyle(colour='foreground', texture_path=tex, texture_opacity=0.9, ambient_glow=AmbientGlowStyle(colour='mid', opacity=0.8))
        bot += TextFrame(
            bot,
            text='Tex + Ambient',
            config=FrameConfig(background=s3),
            visuals=TextStyle(colour='light', justify=('centre', 'middle'))
        )

        # 4. Texture + Starfield
        s4 = BackgroundStyle(colour='dark', texture_path=tex, texture_opacity=0.1, starfield=StarfieldStyle(density=50.0, speed=0.5))
        bot += TextFrame(
            bot,
            text='Tex + Stars',
            config=FrameConfig(background=s4),
            visuals=TextStyle(colour='light', justify=('centre', 'middle'))
        )


class BackgroundEffectsScreen0(Frame):
    """Volumetric Clouds & Panel Edge Lighting."""
    @property
    def title(self):
        return 'Background Effects 0: Caustic, background ambient'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        cloud_style = CloudStyle(opacity=0.5)
        edge = EdgeLightStyle(enabled=True, intensity=0.8, width=0.5, softness=2.0, audio_reactivity=0.0)
        s1 = BackgroundStyle(colour='mid', cloud=CloudStyle(opacity=0.5))
        s2 = BackgroundStyle(colour='background', cloud=cloud_style, edge_light=edge)

        super().__init__(platform, config=FrameConfig(theme='hifi', padding=10))
        cols = ColFramer(self, padpc=0.1)
        cols += Frame(cols, config=FrameConfig(background=s1))
        cols += Frame(cols, config=FrameConfig(background=s2))

class BackgroundEffectsScreen3(Frame):
    """Volumetric Clouds & Panel Edge Lighting."""
    @property
    def title(self):
        return 'Background Effects 0: Caustic, background ambient'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        cloud_style = CloudStyle(opacity=0.5)
        edge = EdgeLightStyle(enabled=True, intensity=0.8, width=0.5, softness=2.0, audio_reactivity=0.0)
        s1 = BackgroundStyle(texture_path='album', texture_opacity=0.6)
        s2 = BackgroundStyle(texture_path='artist', texture_opacity=0.8, edge_light=edge)
        s3 = BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.6)
        out= OutlineStyle(colour='foreground', width=5)

        super().__init__(platform, config=FrameConfig(theme='hifi', padding=10))
        cols = ColFramer(self, padpc=0.1)
        cols += TextFrame(cols, text="album", config=FrameConfig(background=s1,outline=out))
        cols += TextFrame(cols, text="artist", config=FrameConfig(background=s2,outline=out))
        cols += TextFrame(cols, text="path", config=FrameConfig(background=s3,outline=out))

class ShadowTestScreen(Frame):

    @property
    def title(self):
        return 'Drop Shadow Test'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(background=BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.5)))
        cols = self.add_cols(ratios=(1, 1, 1), padpc=0.2, config=FrameConfig(padding=40))

        # 1. Hard Offset Drop Shadow
        s1 = ShadowStyle(colour=(0, 0, 0), opacity=1.0, offset=(15, 15), softness=0.0)
        out1 = OutlineStyle(colour='foreground', width=2, radius=20)
        bg1 = BackgroundStyle(colour='light', colour_opacity=1.0, shadow=s1)
        cols += TextFrame(
            cols,
            text='Hard Shadow',
            config=FrameConfig(outline=out1, background=bg1),
            visuals=TextStyle(colour='dark', justify=('centre', 'middle'))
        )

        # 2. Soft Offset Drop Shadow
        s2 = ShadowStyle(colour=(0, 0, 0), opacity=0.8, offset=(20, 20), softness=0.8)
        out2 = OutlineStyle(colour='foreground', width=2, radius=20)
        bg2 = BackgroundStyle(colour='mid', colour_opacity=1.0, shadow=s2)
        cols += TextFrame(
            cols,
            text='Soft Shadow',
            config=FrameConfig(outline=out2, background=bg2),
            visuals=TextStyle(colour='foreground', justify=('centre', 'middle'))
        )

        # 3. Centered Red Glow (Offset 0, 0)
        s3 = ShadowStyle(colour=(255, 50, 50), opacity=1.0, offset=(0, 0), softness=0.9)
        out3 = OutlineStyle(colour='foreground', width=2, radius=30)
        bg3 = BackgroundStyle(colour='dark', colour_opacity=1.0, shadow=s3)
        cols += TextFrame(
            cols,
            text='Red Glow',
            config=FrameConfig(outline=out3, background=bg3),
            visuals=TextStyle(colour='light', justify=('centre', 'middle'))
        )