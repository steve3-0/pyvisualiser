#!/usr/bin/env python3
"""
Refactored Desktop Visualiser Hero Screens for pyvisualiser.
Part of pyvisualiser v2.1.0 (Refactored to pristine dataclass API)
"""

from pyvisualiser import *
from pyvisualiser.core.base_defs import Channel, MetadataKey, HorizontalAlign, VerticalAlign
from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.framecore import Frame, ColFramer, RowFramer
from pyvisualiser.visualisers.glvisualisers import ShaderFrame
from pyvisualiser.visualisers.oscillogramme import Oscilogramme
from pyvisualiser.visualisers.spectrum import SpectrumFrame
from pyvisualiser.visualisers.vumeters import VUMeter, VUMeterStyle, VUNeedleStyle, VUMeterScale
from pyvisualiser.visualisers.metadata import MetaDataFrame, MetaImages, MetaData, PlayProgressFrame, TextFrame
from pyvisualiser.styles.styles import (
    BackgroundStyle, AmbientGlowStyle, VignetteStyle, NoiseStyle, 
    BarEffects, BarStyle, SpectrumStyle, OutlineStyle, TextStyle, 
    ImageStyle, PlayProgressStyle, ShaderStyle,PI
)

# --- Standardized Widget Aesthetics ---
WidgetOutline = OutlineStyle(colour='light', width=1, radius=12, opacity=0.4, glow_intensity=0.3, softness=0.6)
WidgetBg = BackgroundStyle(colour='background', colour_opacity=0.2, vignette=VignetteStyle(strength=0.6, radius=0.4))


class DesktopNexusScreen(Frame):
    """
    Hero Screen 1: 'Desktop Nexus' (Refactored)
    Clean 3-column layout featuring a theme-tinted 3D liquid orb shader, 
    left-hand album art + metadata, and right-hand stereo spectrum.
    """
    @property
    def title(self): return 'Desktop Hero 1: Cybernetic Nexus (Refactored)'
    @property
    def type(self): return 'Desktop Widget'

    def __init__(self, platform):
        bg = BackgroundStyle(
            colour='background', colour_opacity=0.8, 
            noise=NoiseStyle(strength=0.1), 
            vignette=VignetteStyle(strength=0.8, radius=0.2)
        )
        super().__init__(platform, config=FrameConfig(theme='hifi', background=bg, padding=15))

        cols = self.add_cols(ratios=(1.2, 1.8, 1.2), padpc=0.04, config=FrameConfig(padding=10))

        # Left Column: Album Art + Stacked Metadata
        left_stack = cols.add_rows(ratios=(4, 3, 2, 1), padpc=0.04)
        left_stack += MetaImages(left_stack, key=MetadataKey.ALBUM, visuals=ImageStyle(reflection=ReflectionStyle(size=0.3, opacity=0.3)), config=FrameConfig(outline=WidgetOutline))
        
        meta_stack = left_stack.add_rows(ratios=(1, 1), padpc=0.0)
        meta_stack += MetaData(meta_stack, key=MetadataKey.TRACK, visuals=TextStyle(colour='foreground', justify=('left', 'middle')))
        meta_stack += MetaData(meta_stack, key=MetadataKey.ARTIST, visuals=TextStyle(colour='light', justify=('left', 'middle')))
        left_stack += meta_stack
        
        left_stack += MetaData(left_stack, key=MetadataKey.SOURCE, visuals=TextStyle(colour='mid', justify=('left', 'middle')))

        # Center Column: 3D Liquid Orb Shader
        center_stack = cols.add_rows(ratios=(5, 1), padpc=0.02)
        center_stack += ShaderFrame(center_stack, visuals=ShaderStyle(shader_name='liquidorb', colour='mid'))
        center_stack += PlayProgressFrame(center_stack, visuals=PlayProgressStyle(barsize_pc=0.25,bar_style=BarStyle( led_gap=0)))

        # Right Column: Stereo Spectrum Analyzer
        right_stack = cols.add_rows(ratios=(1, 1), padpc=0.05, config=FrameConfig(padding=10))
        spec_l = SpectrumStyle(barw_min=4, barsize_pc=0.5, bar_style=BarStyle(led_h=6, led_gap=1, tip=True))
        spec_r = SpectrumStyle(barw_min=4, barsize_pc=0.5, bar_style=BarStyle(flip=True, led_h=6, led_gap=1, tip=True))
        
        right_stack += SpectrumFrame(right_stack, channel=Channel.LEFT, visuals=spec_l)
        right_stack += SpectrumFrame(right_stack, channel=Channel.RIGHT, visuals=spec_r)


class AuraCanvasScreen(Frame):
    """
    Hero Screen 2: 'Aura Canvas' (Refactored)
    Organic warping background and smooth rolling oscilloscope.
    """
    @property
    def title(self): return 'Desktop Hero 2: Aura Canvas (Refactored)'
    @property
    def type(self): return 'Desktop Widget'

    def __init__(self, platform):
        bg = BackgroundStyle(colour='background', shader='warping', vignette=VignetteStyle(strength=0.8, radius=0.2))
        super().__init__(platform, config=FrameConfig(theme='ocean', background=bg, padding=20))

        cols = self.add_cols(ratios=(1, 1.5), padpc=0.05, config=FrameConfig(padding=10))

        # Left Column: Album Art with reflection
        art_out = OutlineStyle(colour='light', width=2, radius=12, glow_intensity=0.6, softness=0.8)
        cols += MetaImages(cols, key=MetadataKey.ALBUM, visuals=ImageStyle(reflection=ReflectionStyle(size=0.4, opacity=0.4)), config=FrameConfig(outline=art_out))

        # Right Column: MetaDataFrame + Oscilloscope + Progress
        right_stack = cols.add_rows(ratios=(1.2, 2.2, 1), padpc=0.04)
        
        right_stack += MetaDataFrame(right_stack, justify='left', config=FrameConfig(background=None))
        right_stack += Oscilogramme(right_stack, channel=Channel.MONO, config=FrameConfig(background=WidgetBg, outline=WidgetOutline, padding=10))
        right_stack += PlayProgressFrame(right_stack, visuals=PlayProgressStyle(barsize_pc=0.35, bar_style=BarStyle(led_gap=0)))


class StellarPulseScreen(Frame):
    """
    Hero Screen 3: 'Stellar Pulse' (Refactored into a Meter Bridge)
    Dual luxury analogue VU meters flanking a clean central supernova core and horizon spectrum.
    """
    @property
    def title(self): return 'Desktop Hero 3: Stellar Pulse (Refactored Meter Bridge)'
    @property
    def type(self): return 'Desktop Widget'

    def __init__(self, platform):
        bg = BackgroundStyle(colour='background', colour_opacity=0.95, vignette=VignetteStyle(strength=0.7, radius=0.3))
        super().__init__(platform, config=FrameConfig(theme='space', background=bg, padding=15))

        rows = self.add_rows(ratios=(1, 3.5, 1.5), padpc=0.03)

        # Header: Track & Source
        header = rows.add_cols(ratios=(3, 1), config=FrameConfig(padding=5))
        header += MetaData(header, key=MetadataKey.TRACK, visuals=TextStyle(colour='foreground', justify=('left', 'middle')))
        header += MetaData(header, key=MetadataKey.SOURCE, visuals=TextStyle(colour='light', justify=('right', 'middle')))

        # Middle: Dual Custom Analogue VU Meters flanking a clean Supernova core
        mid_cols = rows.add_cols(ratios=(1.2, 1.6, 1.2), padpc=0.03)
        
        clean_marks = {
            0.2: {'text': '-20', 'width': 2, 'colour': 'light'},
            0.5: {'text': '-10', 'width': 2, 'colour': 'light'},
            0.7: {'text': '0', 'width': 3, 'colour': 'alert'},
            0.9: {'text': '+3', 'width': 3, 'colour': 'alert'}
        }
        vu_scale = VUMeterScale(marks=clean_marks, arcs=None, annotate={'text': 'dB', 'colour': 'mid'}, scale_radius=0.75, font_height=0.07)
        needle_style = VUNeedleStyle(colour='foreground', width=3, length=0.75, radius_pc=0.85, glow_intensity=0.2, glow_colour='foreground')
        meter_style = VUMeterStyle(pivot=-0.6, endstops=(3 * PI / 4, 5 * PI / 4), needle=needle_style, scale=vu_scale, show_peak=True)

        vu_bg = BackgroundStyle(colour='background', colour_opacity=0.9, ambient_glow=AmbientGlowStyle(colour='foreground', opacity=0.4, radius=0.4))

        mid_cols += VUMeter(mid_cols, channel=Channel.LEFT, visuals=meter_style, config=FrameConfig(background=vu_bg, outline=WidgetOutline))
        mid_cols += ShaderFrame(mid_cols, visuals=ShaderStyle(shader_name='supernova', colour='mid'))
        mid_cols += VUMeter(mid_cols, channel=Channel.RIGHT, visuals=meter_style, config=FrameConfig(background=vu_bg, outline=WidgetOutline))

        # Bottom: Horizon Spectrum & Progress Bar
        bottom_stack = rows.add_rows(ratios=(2, 1), padpc=0.04)
        
        spec_style = SpectrumStyle(
            barsize_pc=0.6, barw_min=6, barw_max=16,
            bar_style=BarStyle(led_gap=2, peak_h=2, radius=1, tip=True)
        )
        bottom_stack += SpectrumFrame(bottom_stack, channel=Channel.MONO, visuals=spec_style, config=FrameConfig(background=WidgetBg, outline=WidgetOutline))
        bottom_stack += PlayProgressFrame(bottom_stack, visuals=PlayProgressStyle(bar_style=BarStyle(),barsize_pc=0.3))