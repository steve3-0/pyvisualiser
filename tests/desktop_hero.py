#!/usr/bin/env python3
"""
Novel Desktop Visualiser Hero Screens for pyvisualiser.
Designed for a floating, high-end desktop widget aesthetic.
"""

from pyvisualiser import *
from pyvisualiser.visualisers.glvisualisers import ShaderFrame
from pyvisualiser.visualisers.oscillogramme import Oscilogramme
from pyvisualiser.visualisers.spectrum import SpectrumFrame
from pyvisualiser.visualisers.vumeters import VUMeter, VUFrame
from pyvisualiser.visualisers.metadata import MetaDataFrame, MetaImages, MetaData, PlayProgressFrame, TextFrame
from pyvisualiser.core.framecore import Frame, ColFramer, RowFramer
from pyvisualiser.styles.presets import Centred, PI
from pyvisualiser.styles.styles import (
    BackgroundStyle, AmbientGlowStyle, VignetteStyle, NoiseStyle, 
    BarEffects, BarStyle, SpectrumStyle, OutlineStyle, VUMeterStyle, VUNeedleStyle
)

# --- Common Desktop Widget Styles ---
WidgetOutline = OutlineStyle(colour='light', width=1, radius=16, opacity=0.4, glow_intensity=0.4, softness=0.8)
WidgetBg      = BackgroundStyle(colour='background', colour_opacity=0.85, vignette=VignetteStyle(strength=0.7, radius=0.3))


class DesktopNexusScreen(Frame):
    """
    Hero Screen 1: 'Desktop Nexus'
    A floating widget featuring a central 3D liquid orb shader surrounded by a 
    split-channel spectrum and floating high-contrast metadata.
    """
    @property
    def title(self): return 'Desktop Hero 1: Cybernetic Nexus'
    @property
    def type(self): return 'Desktop Widget'

    def __init__(self, platform):
        # Semi-transparent dark background for widget floating feel
        bg = BackgroundStyle(colour='background', colour_opacity=0.7, noise=NoiseStyle(strength=0.15), vignette=VignetteStyle(strength=0.8, radius=0.2))
        super().__init__(platform, theme='hifi', background=bg, padding=15)

        # 3-Column Layout: Left (Mini VU + Track info), Center (Shader Orb), Right (Spectrum + Controls)
        cols = ColFramer(self, col_ratios=(1, 2, 1), padpc=0.03, padding=10)

        # Left Column: Track Meta + Minimal VU
        left_stack = RowFramer(cols, row_ratios=(2, 3, 1), padpc=0.05)
        left_stack += MetaData(left_stack, metadata_type='track', colour='foreground', justify=('left', 'middle'))
        left_stack += MetaImages(left_stack, art_type='album', reflection={'size': 0.3, 'opacity': 0.4}, outline=WidgetOutline)
        left_stack += MetaData(left_stack, metadata_type='source', colour='light', justify=('left', 'middle'))

        # Center Column: Interactive 3D Liquid Orb Shader (Audio-Reactive)
        center_stack = RowFramer(cols, row_ratios=(5, 1), padpc=0.02)
        center_stack += ShaderFrame(center_stack, shader='liquidorb', colour='mid')
        center_stack += PlayProgressFrame(center_stack, barsize_pc=0.2, bar_style=BarStyle(led_gap=0))

        # Right Column: Stereo Spectrum Analyzer
        right_stack = RowFramer(cols, row_ratios=(1, 1), padpc=0.05)
        right_stack += SpectrumFrame(right_stack, channel='left', bar_style=BarStyle(led_h=4, led_gap=1, tip=True), spectrum_style=SpectrumStyle(barw_min=3, barsize_pc=0.6))
        right_stack += SpectrumFrame(right_stack, channel='right', bar_style=BarStyle(flip=True, led_h=4, led_gap=1, tip=True), spectrum_style=SpectrumStyle(barw_min=3, barsize_pc=0.6))


class AuraCanvasScreen(Frame):
    """
    Hero Screen 2: 'Aura Canvas'
    Optimized for ambient desktop listening. Uses an organic warping background shader,
    a floating rolling oscilloscope waveform, and minimal typography.
    """
    @property
    def title(self): return 'Desktop Hero 2: Aura Canvas'
    @property
    def type(self): return 'Desktop Widget'

    def __init__(self, platform):
        # Organic slow-moving warping fluid background
        bg = BackgroundStyle(colour='background', shader='warping', vignette=VignetteStyle(strength=0.9, radius=0.15))
        super().__init__(platform, theme='ocean', background=bg, padding=20)

        # Asymmetric layout: Album art banner on the left, waveform & metadata floating on the right
        cols = ColFramer(self, col_ratios=(1, 2), padpc=0.04, padding=10)

        # Left: Clean square album frame with deep glow outline
        cols += MetaImages(cols, art_type='album', reflection={'size': 0.4, 'opacity': 0.5}, outline=OutlineStyle(colour='light', width=2, radius=12, glow_intensity=0.8, softness=1.0))

        # Right: Stacked metadata, live oscilloscope waveform, and timer
        right_stack = RowFramer(cols, row_ratios=(1, 2, 1), padpc=0.04)
        
        meta_row = RowFramer(right_stack, row_ratios=(1, 1), padpc=0.0)
        meta_row += MetaData(meta_row, metadata_type='track', colour='foreground', justify=('left', 'middle'))
        meta_row += MetaData(meta_row, metadata_type='artist', colour='light', justify=('left', 'middle'))

        # Floating Oscilogramme wave inside a styled sub-frame container
        right_stack += Oscilogramme(right_stack, channel='mono', background=WidgetBg, outline=WidgetOutline)
        
        right_stack += PlayProgressFrame(right_stack, barsize_pc=0.4, bar_style=BarStyle(led_gap=0))


class StellarPulseScreen(Frame):
    """
    Hero Screen 3: 'Stellar Pulse'
    High-energy dynamic screen featuring the 'starvis' reactive mood shader,
    mirrored stereo spectrum bars, and a clean glassmorphism metadata overlay.
    """
    @property
    def title(self): return 'Desktop Hero 3: Stellar Pulse'
    @property
    def type(self): return 'Desktop Widget'

    def __init__(self, platform):
        # Deep space backdrop with dynamic starfield
        bg = BackgroundStyle(colour='background', shader='starvis', starfield=True, vignette=VignetteStyle(strength=0.5, radius=0.5))
        super().__init__(platform, theme='space', background=bg, padding=15)

        # Center-weighted composition
        rows = RowFramer(self, row_ratios=(1, 4, 1), padpc=0.04)

        # Top Bar: Compact Metadata Header
        header = ColFramer(rows, col_ratios=(3, 1), padding=5)
        header += MetaData(header, metadata_type='track', colour='foreground', justify=('left', 'middle'))
        header += MetaData(header, metadata_type='source', colour='light', justify=('right', 'middle'))

        # Middle: Starburst Visualiser flanked by dual analog needle meters
        mid_cols = ColFramer(rows, col_ratios=(1, 3, 1), padpc=0.02)
        
        needle_style = VUMeterStyle(pivot=-0.5, endstops=(3*PI/4, 5*PI/4), needle=VUNeedleStyle(width=3, colour='light', tip_glow=True))
        mid_cols += VUMeter(mid_cols, 'left', style=needle_style, background=WidgetBg, outline=WidgetOutline)
        
        # Center Starburst / Supernova shader frame
        mid_cols += ShaderFrame(mid_cols, shader='supernova', colour='mid')
        
        mid_cols += VUMeter(mid_cols, 'right', style=needle_style, background=WidgetBg, outline=WidgetOutline)

        # Bottom Bar: Mirrored Stereo Spectrum & Progress
        bottom_stack = RowFramer(rows, row_ratios=(2, 1), padpc=0.02)
        
        spec_split = ColFramer(bottom_stack, padpc=0.01)
        spec_split += SpectrumFrame(spec_split, channel='left', bar_style=BarStyle(flip=True, led_gap=0, tip=True), spectrum_style=SpectrumStyle(barw_min=2, barsize_pc=0.8))
        spec_split += SpectrumFrame(spec_split, channel='right', bar_style=BarStyle(led_gap=0, tip=True), spectrum_style=SpectrumStyle(barw_min=2, barsize_pc=0.8))
        
        bottom_stack += PlayProgressFrame(bottom_stack, barsize_pc=0.3)