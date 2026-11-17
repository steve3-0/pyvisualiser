#!/usr/bin/env python3
"""
Refactored Desktop Visualiser Hero Screens for pyvisualiser.
Fixes typography overlaps, VU meter scaling/clipping, and shader color injection.
"""

from pyvisualiser import *
from pyvisualiser.visualisers.glvisualisers import ShaderFrame
from pyvisualiser.visualisers.oscillogramme import Oscilogramme
from pyvisualiser.visualisers.spectrum import SpectrumFrame
from pyvisualiser.visualisers.vumeters import VUMeter, VUMeterStyle, VUNeedleStyle, VUMeterScale
from pyvisualiser.visualisers.metadata import MetaDataFrame, MetaImages, MetaData, PlayProgressFrame, TextFrame
from pyvisualiser.core.framecore import Frame, ColFramer, RowFramer
from pyvisualiser.styles.presets import Centred, PI
from pyvisualiser.styles.styles import (
    BackgroundStyle, AmbientGlowStyle, VignetteStyle, NoiseStyle, 
    BarEffects, BarStyle, SpectrumStyle, OutlineStyle
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
        super().__init__(platform, theme='hifi', background=bg, padding=15)

        cols = ColFramer(self, col_ratios=(1.2, 1.8, 1.2), padpc=0.04, padding=10)

        # Left Column: Album Art + Stacked Metadata
        left_stack = RowFramer(cols, row_ratios=(4, 3, 2, 1), padpc=0.04)
        left_stack += MetaImages(left_stack, art_type='album', reflection={'size': 0.3, 'opacity': 0.3}, outline=WidgetOutline)
        
        meta_stack = RowFramer(left_stack, row_ratios=(1, 1), padpc=0.0)
        meta_state = ProfileManager.get_profile()
        meta_stack += MetaData(meta_stack, metadata_type='track', colour='foreground', justify=('left', 'middle'))
        meta_stack += MetaData(meta_stack, metadata_type='artist', colour='light', justify=('left', 'middle'))
        left_stack += meta_stack
        
        left_stack += MetaData(left_stack, metadata_type='source', colour='mid', justify=('left', 'middle'))

        # Center Column: 3D Liquid Orb Shader (Fixed to receive theme palette colors)
        center_stack = RowFramer(cols, row_ratios=(5, 1), padpc=0.02)
        center_stack += ShaderFrame(center_stack, shader='liquidorb', colour='mid')
        center_stack += PlayProgressFrame(center_stack, barsize_pc=0.25, bar_style=BarStyle(led_gap=0))

        # Right Column: Stereo Spectrum Analyzer
        right_stack = RowFramer(cols, row_ratios=(1, 1), padpc=0.05, padding=10)
        right_stack += SpectrumFrame(right_stack, channel='left', bar_style=BarStyle(led_h=6, led_gap=1, tip=True), spectrum_style=SpectrumStyle(barw_min=4, barsize_pc=0.5))
        right_stack += SpectrumFrame(right_stack, channel='right', bar_style=BarStyle(flip=True, led_h=6, led_gap=1, tip=True), spectrum_style=SpectrumStyle(barw_min=4, barsize_pc=0.5))


class AuraCanvasScreen(Frame):
    """
    Hero Screen 2: 'Aura Canvas' (Refactored)
    Fixed overlapping typography and progress bar collisions. Features an organic 
    warping background and a smooth rolling oscilloscope.
    """
    @property
    def title(self): return 'Desktop Hero 2: Aura Canvas (Refactored)'
    @property
    def type(self): return 'Desktop Widget'

    def __init__(self, platform):
        bg = BackgroundStyle(colour='background', shader='warping', vignette=VignetteStyle(strength=0.8, radius=0.2))
        super().__init__(platform, theme='ocean', background=bg, padding=20)

        cols = ColFramer(self, col_ratios=(1, 1.5), padpc=0.05, padding=10)

        # Left Column: Album Art with reflection
        cols += MetaImages(cols, art_type='album', reflection={'size': 0.4, 'opacity': 0.4}, outline=OutlineStyle(colour='light', width=2, radius=12, glow_intensity=0.6, softness=0.8))

        # Right Column: Clean non-overlapping MetaDataFrame + Oscilloscope + Progress
        right_stack = RowFramer(cols, row_ratios=(1.2, 2.2, 1), padpc=0.04)
        
        # Fixed typography stack using MetaDataFrame (handles vertical rhythm automatically)
        right_stack += MetaDataFrame(right_stack, justify='left', background=None)

        # Oscilloscope Waveform in dedicated card
        # osc_frame = RowFramer(right_stack, row_ratios=(1,1), background=WidgetBg, outline=WidgetOutline, padding=10)
        right_stack += Oscilogramme(right_stack, channel='mono', background=WidgetBg, outline=WidgetOutline, padding=10)
        # right_stack += osc_frame

        right_stack += PlayProgressFrame(right_stack, barsize_pc=0.35, bar_style=BarStyle(led_gap=0))


class StellarPulseScreen(Frame):
    """
    Hero Screen 3: 'Stellar Pulse' (Refactored into a Meter Bridge)
    Removes visual clutter, featuring dual luxury analogue VU meters flanking 
    a clean central supernova core and horizon spectrum.
    """
    @property
    def title(self): return 'Desktop Hero 3: Stellar Pulse (Refactored Meter Bridge)'
    @property
    def type(self): return 'Desktop Widget'

    def __init__(self, platform):
        bg = BackgroundStyle(colour='background', colour_opacity=0.95, vignette=VignetteStyle(strength=0.7, radius=0.3))
        super().__init__(platform, theme='space', background=bg, padding=15)

        rows = RowFramer(self, row_ratios=(1, 3.5, 1.5), padpc=0.03)

        # Header: Track & Source
        header = ColFramer(rows, col_ratios=(3, 1), padding=5)
        header += MetaData(header, metadata_type='track', colour='foreground', justify=('left', 'middle'))
        header += MetaData(header, metadata_type='source', colour='light', justify=('right', 'middle'))

        # Middle: Dual Custom Analogue VU Meters flanking a clean Supernova core
        mid_cols = ColFramer(rows, col_ratios=(1.2, 1.6, 1.2), padpc=0.03)
        
        # Compact scale marks preventing number overflow
        clean_marks = {
            0.2: {'text':'-20', 'width': 2, 'colour': 'light'},
            0.5: {'text':'-10', 'width': 2, 'colour': 'light'},
            0.7: {'text':'0', 'width': 3, 'colour': 'alert'},
            0.9: {'text':'+3', 'width': 3, 'colour': 'alert'}
        }
        vu_scale = VUMeterScale(marks=clean_marks, arcs=None, annotate={'text':'dB', 'colour':'mid'}, scale_radius=0.75, font_height=0.07)
        needle_style = VUNeedleStyle(colour='foreground', width=3, length=0.75, radius_pc=0.85, glow_intensity=0.2, glow_colour='foreground')
        meter_style = VUMeterStyle(pivot=-0.6, endstops=(3*PI/4, 5*PI/4), needle=needle_style, scale=vu_scale, show_peak=True)

        vu_bg = BackgroundStyle(colour='background', colour_opacity=0.9, ambient_glow=AmbientGlowStyle(colour='foreground', opacity=0.4, radius=0.4))

        mid_cols += VUMeter(mid_cols, 'left', style=meter_style, background=vu_bg, outline=WidgetOutline)
        mid_cols += ShaderFrame(mid_cols, shader='supernova', colour='mid')
        mid_cols += VUMeter(mid_cols, 'right', style=meter_style, background=vu_bg, outline=WidgetOutline)

        # Bottom: Horizon Spectrum & Progress Bar
        bottom_stack = RowFramer(rows, row_ratios=(2, 1), padpc=0.04)
        
        spec_style = SpectrumStyle(barw_min=6, barsize_pc=0.6, barw_max=16)
        bar_style = BarStyle(led_gap=2, peak_h=2, radius=1, tip=True)
        bottom_stack += SpectrumFrame(bottom_stack, 'mono', spectrum_style=spec_style, bar_style=bar_style, background=WidgetBg, outline=WidgetOutline)
        
        bottom_stack += PlayProgressFrame(bottom_stack, barsize_pc=0.3)