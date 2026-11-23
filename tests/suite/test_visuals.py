#!/usr/bin/env python3
"""
Advanced Visualiser Test Script
Tests instantiation and layout of advanced 3D frames, glow passes, and tuning screens.
Part of pyvisualiser v2.1.0 (Refactored to pristine dataclass API)
"""

from pyvisualiser import *
from pyvisualiser.core.base_defs import Channel, MetadataKey, HorizontalAlign, VerticalAlign
from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.backgrounds import BackgroundBase
from pyvisualiser.styles.presets import NeonGlow
from pyvisualiser.styles.styles import (
    BackgroundStyle, OutlineStyle, TextStyle, ImageStyle, PI,
    BarStyle, SpectrumStyle, BarEffects, VUMeterStyle, VUBarStyle,
    AmbientGlowStyle, VignetteStyle, NoiseStyle, OscillogrammeStyle
)
import numpy as np
import math
import time
import pygame
from typing import Optional, Union, Tuple, Dict, Any


class BarTest(Frame):
    """Creates static bars with varying levels of effects for visual inspection."""
    def __init__(
        self,
        parent,
        channel: float,
        config: Optional[FrameConfig] = None,
        update_fn=None,
        bar_style: Optional[BarStyle] = None,
        barsize_pc: float = 0.7
    ):
        self.level = channel
        self.update_fn = update_fn
        self.bar_style = bar_style if bar_style is not None else BarStyle()
        self.barsize_pc=barsize_pc
        
        resolved_config = config if config is not None else FrameConfig()
        super().__init__(parent, config=resolved_config)
        self.configure()

    def configure(self):
        self.barw = self.abs_w * self.barsize_pc if self.bar_style.orient == 'vert' else self.abs_h * self.barsize_pc
        box = (self.barw, self.h) if self.bar_style.orient == 'vert' else (self.w, self.barw)
        self.bar = Bar(self, box_size=box, bar_style=self.bar_style)

    def update_screen(self, audio=None, media=None):
        if self.update_fn is not None:
            height = self.update_fn()
            peaks = height
        else:
            height, peaks = self.level, self.level
        self.bar.draw(0, height, self.barw, peaks)
        return True


class AdvancedVisualsScreen(Frame):
    @property
    def title(self): return 'Advanced Visuals Test'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        bg = BackgroundStyle(texture_path='metal.jpg', texture_opacity=0.9)
        super().__init__(platform, config=FrameConfig(theme='hifi', background=bg))
        
        rows = self.add_rows(config=FrameConfig(padding=10), padpc=0.02)
        top = rows.add_cols(config=FrameConfig(padding=10), padpc=0.02)
        
        top += TextFrame(
            top,
            text="Freq Wave\n(Scrolling)",
            config=FrameConfig(background=BackgroundStyle(colour='dark')),
            visuals=TextStyle(colour='light', justify=('centre', 'middle'))
        )
        top += FreqWaveFrame(
            top,
            channel=Channel.MONO,
            config=FrameConfig(background=BackgroundStyle(colour='background', colour_opacity=0.78), outline=OutlineStyle(colour='mid', width=1))
        )


class GlowTestScreen(Frame):
    @property
    def title(self): return 'Glow Extraction Test'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', background=BackgroundStyle(colour='background')))
        
        cols = self.add_cols(ratios=(1, 1, 1, 1), padpc=0.1, config=FrameConfig(padding=50))

        cols += BarTest(cols, 0.5, bar_style=BarStyle(colour_mode='solid', orient='vert', effects=None))
        cols += BarTest(cols, 0.9, bar_style=BarStyle(colour_mode='solid', orient='vert', effects=BarEffects(threshold=0.1, scale=2.0, blur=0.5, alpha=150)))
        cols += BarTest(cols, 0.7, bar_style=BarStyle(orient='vert', effects=BarEffects(threshold=0.1, scale=2.0, blur=0.5, alpha=150)))
        cols += BarTest(cols, 0.3, bar_style=BarStyle(orient='vert', effects=BarEffects(threshold=0.1, scale=2.0, blur=0.5, alpha=150)))

        self.text_frame = TextFrame(
            self,
            text="Viewing Glow Buffer. Left bar is normal, others are additive.",
            config=FrameConfig(scalers=(1.0, 0.1), align=(HorizontalAlign.CENTRE, VerticalAlign.TOP)),
            visuals=TextStyle(colour='light')
        )
        self += self.text_frame

    def update_screen(self, audio=None, media=None):
        if hasattr(self.platform, 'compositor'):
            self.platform.compositor.glow_extraction_pass.threshold = 0.5
        super().update_screen(audio=audio, media=media)


class BarEffectsTestScreen(Frame):
    @property
    def title(self): return 'Bar Parameters Test Screen'    
    @property
    def type(self): return 'Test'

    def __init__(self, platform):   
        super().__init__(platform, config=FrameConfig(theme='hifi', background=BackgroundStyle(colour='background')))
  
        cols = self.add_cols(config=FrameConfig(padding=0), padpc=0.05)
        horzbars = cols.add_rows(config=FrameConfig(padding=20), padpc=0.5)
        vertbars = cols.add_cols(config=FrameConfig(padding=20), padpc=0.5)

        for level in np.arange(0.1, 1.1, 0.1):
            eff_h = BarEffects(threshold=0.8, scale=1.0 * level, alpha=200, blur=1.5)
            horzbars += BarTest(horzbars, level, bar_style=BarStyle(orient='horz', effects=eff_h))
            eff_v = BarEffects(threshold=0.8, scale=1.0 * level, alpha=200, blur=0.5)
            vertbars += BarTest(vertbars, level, bar_style=BarStyle(orient='vert', effects=eff_v))


class AudioTest(Frame):
    def __init__(self, parent, metadata: str):
        super().__init__(parent, config=FrameConfig())
        self.metadata = metadata
        r1 = self.add_rows(config=FrameConfig(padding=0), padpc=0.05)
        r1 += TextFrame(r1, update_fn=self.get_audio_metadata_str, visuals=TextStyle(colour='light'))
        r1 += BarTest(r1, 0.0, bar_style=BarStyle(orient='vert'), update_fn=self.get_audio_metadata)

    def get_audio_metadata_str(self):
        return f"{self.metadata}\n{self.get_audio_metadata():.2f}"

    def get_audio_metadata(self):
        return float(self.platform.audioanalysis.get(self.metadata, 0.0))


ANALYSIS_METADATA = ["beat", "bpm", "centroid", "kurtosis", "flux", "volume"]


class AudioTestScreen(Frame):
    @property
    def title(self): return 'Audio Parameters Test Screen'    
    @property
    def type(self): return 'Test'

    def __init__(self, platform):   
        super().__init__(platform, config=FrameConfig(theme='hifi', background=BackgroundStyle(colour='background')))
        cols = self.add_cols(config=FrameConfig(padding=0), padpc=0.05)
        for metadata in ANALYSIS_METADATA:
            cols += AudioTest(cols, metadata)


class AudioTestScreen1(Frame):
    @property
    def title(self): return 'Audio Parameters Test Screen'    
    @property
    def type(self): return 'Test'

    def __init__(self, platform):   
        super().__init__(platform, config=FrameConfig(theme='hifi', background=BackgroundStyle(colour='background')))

        cols = self.add_cols(config=FrameConfig(padding=0), padpc=0.05)
        r1 = cols.add_rows(config=FrameConfig(padding=0), padpc=0.05)
        r2 = cols.add_rows(config=FrameConfig(padding=0), padpc=0.05)
        r3 = cols.add_rows(config=FrameConfig(padding=0), padpc=0.05)

        r1 += TextFrame(r1, update_fn=self.get_bass_str, visuals=TextStyle(colour='light'))
        r1 += BarTest(r1, 0.0, bar_style=BarStyle(orient='vert'), update_fn=self.get_bass)

        r2 += TextFrame(r2, update_fn=self.get_treble_str, visuals=TextStyle(colour='light'))
        r2 += BarTest(r2, 0.0, bar_style=BarStyle(orient='vert'), update_fn=self.get_treble)

        r3 += TextFrame(r3, update_fn=self.get_bpm_str, visuals=TextStyle(colour='light'))
        r3 += BarTest(r3, 0.0, bar_style=BarStyle(orient='vert'), update_fn=self.get_bpm)

    def get_bass_str(self):
        return f"Bass\n{self.get_bass():.2f}"

    def get_treble_str(self):
        return f"Treble\n{self.get_treble():.2f}"

    def get_bpm_str(self):
        return f"BPM\n{self.get_bpm() * 160:.2f}"

    def get_bass(self):
        return self.platform.bass * 15

    def get_treble(self):
        return self.platform.treble * 400

    def get_bpm(self):
        return self.platform.bpm / 160


class OutlineGlowTestScreen(Frame):
    @property
    def title(self): return 'Outline Glow Effects Test'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        bg = BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.2)
        super().__init__(platform, config=FrameConfig(theme='hifi', background=bg))
        
        rows = self.add_rows(config=FrameConfig(padding=30), padpc=0.2)
        
        # Row 1: Intensity Variations
        r1 = rows.add_cols(ratios=(1, 1, 1), padpc=0.3, config=FrameConfig(padding=20))
        
        r1 += TextFrame(r1, text="Subtle Glow\nInt: 0.2, Soft: 0.5", config=FrameConfig(outline=OutlineStyle(colour='foreground', width=2, radius=10, glow_intensity=0.2, softness=0.5), background=BackgroundStyle(colour='dark')), visuals=TextStyle(justify=('centre', 'middle')))
        r1 += TextFrame(r1, text="Medium Glow\nInt: 1.0, Soft: 0.5", config=FrameConfig(outline=OutlineStyle(colour='alert', width=3, radius=10, glow_intensity=1.0, softness=0.5), background=BackgroundStyle(colour='dark')), visuals=TextStyle(justify=('centre', 'middle')))
        r1 += TextFrame(r1, text="Intense Glow\nInt: 2.0, Soft: 0.5", config=FrameConfig(outline=OutlineStyle(colour='foreground', width=2, radius=10, glow_intensity=2.0, softness=0.5), background=BackgroundStyle(colour='dark')), visuals=TextStyle(justify=('centre', 'middle')))

        # Row 2: Softness Variations
        r2 = rows.add_cols(ratios=(1, 1, 1), padpc=0.3, config=FrameConfig(padding=20))
        r2 += TextFrame(r2, text="Sharp Glow\nSoft: 0.1", config=FrameConfig(outline=OutlineStyle(colour='mid', width=2, radius=5, glow_intensity=1.0, softness=0.1), background=BackgroundStyle(colour='dark')), visuals=TextStyle(justify=('centre', 'middle')))
        r2 += TextFrame(r2, text="Soft Glow\nSoft: 1.0", config=FrameConfig(outline=OutlineStyle(colour='mid', width=2, radius=5, glow_intensity=1.0, softness=1.0), background=BackgroundStyle(colour='dark')), visuals=TextStyle(justify=('centre', 'middle')))
        r2 += TextFrame(r2, text="Diffuse Glow\nSoft: 2.0", config=FrameConfig(outline=OutlineStyle(colour='mid', width=2, radius=5, glow_intensity=1.0, softness=2.0), background=BackgroundStyle(colour='dark')), visuals=TextStyle(justify=('centre', 'middle')))


class ParameterTuner:
    def __init__(self, target_object, parameters):
        self.target = target_object
        self.params = parameters
        self.selected_index = 0

    def handle_key(self, key):
        if key >= pygame.K_1 and key <= pygame.K_9:
            idx = key - pygame.K_1
            if idx < len(self.params):
                self.selected_index = idx
        elif key == pygame.K_UP:
            self._adjust(1)
        elif key == pygame.K_DOWN:
            self._adjust(-1)
            
    def _adjust(self, direction):
        p = self.params[self.selected_index]
        attr = p['attr']
        current_val = getattr(self.target, attr)
        new_val = max(p['min'], min(p['max'], current_val + (p['step'] * direction)))
        setattr(self.target, attr, new_val)

    def get_display_text(self):
        lines = [f"Parameter Tuner (Keys 1-{len(self.params)}, Up/Down)"]
        for i, p in enumerate(self.params):
            val = getattr(self.target, p['attr'])
            prefix = ">> " if i == self.selected_index else "   "
            lines.append(f"{prefix}{i+1}. {p['name']}: {val:.2f}")
        lines.append("\nPress 'S' to print Preset code")
        return "\n".join(lines)


class AmbientGlowTunerScreen(Frame):
    @property
    def title(self): return 'Ambient Glow Tuner'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        self.glow_style = AmbientGlowStyle(colour='light', opacity=0.5, radius=1.0, softness=0.5)
        bg_style = BackgroundStyle(colour='background', ambient_glow=self.glow_style)
        
        super().__init__(platform, config=FrameConfig(theme='hifi', background=bg_style))
        
        params = [
            {'name': 'Radius',   'attr': 'radius',   'min': 0.0, 'max': 3.0, 'step': 0.1},
            {'name': 'Softness', 'attr': 'softness', 'min': 0.0, 'max': 2.0, 'step': 0.05},
            {'name': 'Opacity',  'attr': 'opacity',  'min': 0.0, 'max': 1.0, 'step': 0.05},
        ]
        self.tuner = ParameterTuner(self.glow_style, params)
        
        self.info_display = TextFrame(
            self,
            text="",
            config=FrameConfig(scalers=(0.6, 0.4), align=(HorizontalAlign.CENTRE, VerticalAlign.MIDDLE), background=BackgroundStyle(colour='dark', colour_opacity=0.6), outline=OutlineStyle(colour='mid', width=1)),
            visuals=TextStyle(colour='light', justify=('centre', 'middle'))
        )
        self += self.info_display

    def handle_key(self, key):
        if key == pygame.K_s:
            g = self.glow_style
            print(f"\nAmbientGlowStyle(colour='{g.colour}', radius={g.radius:.2f}, softness={g.softness:.2f}, opacity={g.opacity:.2f})\n")
        else:
            self.tuner.handle_key(key)

    def update_screen(self, audio=None, media=None):
        self.info_display.textcomp.text = self.tuner.get_display_text()
        super().update_screen(audio=audio, media=media)


class APICoverageScreen(Frame):
    @property
    def title(self): return 'API Coverage Test Screen'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        bg = BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.5)
        super().__init__(platform, config=FrameConfig(theme='hifi', background=bg))
        
        rows = self.add_rows(ratios=(1, 1, 1), padpc=0.05, config=FrameConfig(padding=20))
        
        # --- ROW 1: Core Visual Components ---
        r1 = rows.add_cols(ratios=(1, 1, 1, 1), config=FrameConfig(padding=10))
        
        r1 += TextFrame(r1, text="TextFrame\nWrapped & Centred", config=FrameConfig(background=BackgroundStyle(colour='mid'), outline=OutlineStyle(colour='light', width=1, radius=5)), visuals=TextStyle(wrap=True, justify=('centre', 'middle'), colour='alert'))
        r1 += MetaImages(r1, key=MetadataKey.ALBUM, config=FrameConfig(outline=OutlineStyle(colour='foreground', width=2)), visuals=ImageStyle(opacity=0.86, reflection=ReflectionStyle(size=0.4, opacity=0.6)))
        r1 += MetaData(r1, key=MetadataKey.ARTIST, config=FrameConfig(background=BackgroundStyle(colour='dark', colour_opacity=0.6), outline=OutlineStyle(width=0)), visuals=TextStyle(colour='light', justify=('left', 'top')))
        r1 += PlayProgressFrame(r1, config=FrameConfig(background=BackgroundStyle(colour='mid', colour_opacity=0.4)), 
                                visuals=PlayProgressStyle(bar_style=BarStyle(led_h=4, led_gap=1), barsize_pc=0.4))

        # --- ROW 2: Audio Visualisers (Bars & Spectrums) ---
        r2 = rows.add_cols(ratios=(1, 1, 1), config=FrameConfig(padding=10))
        
        r2 += VUFrame(r2, channel=Channel.LEFT, config=FrameConfig(), 
                      visuals=VUBarStyle(bar_style=BarStyle(orient='vert', segment_size=8, segment_gap=2, corner_radius=3, edge_softness=0.1)))
        
        spec_style = SpectrumStyle(
            barsize_pc=0.2, barw_min=5,
            bar_style=BarStyle(led_h=3, led_gap=1, peak_h=2, effects=BarEffects(threshold=0.5, scale=3.0, blur=2.0, alpha=0.8))
        )
        r2 += SpectrumFrame(r2, channel=Channel.MONO, config=FrameConfig(background=BackgroundStyle(colour='dark', colour_opacity=0.8)), visuals=spec_style)
        
        r2 += Diamondiser(r2, channel=Channel.MONO, config=FrameConfig(background=BackgroundStyle(colour='mid'), square=True), visuals=SpectrumStyle(barsize_pc=1.0))

        # --- ROW 3: Audio Visualisers (Meters & Waveforms) & Z-Order ---
        r3 = rows.add_cols(ratios=(1, 1, 1), config=FrameConfig(padding=10))
        
        r3 += VUMeter(r3, channel=Channel.MONO, config=FrameConfig(background=BackgroundStyle(colour='light', colour_opacity=0.2), outline=OutlineStyle(colour='alert', width=1)), visuals=VUMeterStyle(pivot=-0.2, endstops=(-PI/4, 3*PI/4)))
        r3 += Oscilogramme(r3, channel=Channel.LEFT, config=FrameConfig(background=BackgroundStyle(colour='background')))
        
        z_test = Frame(r3, config=FrameConfig(background=BackgroundStyle(colour='mid'), outline=OutlineStyle(colour='foreground', width=1)))
        z_test += TextFrame(parent=z_test, text="Background\n(z=0)", config=FrameConfig(scalers=(1.0, 1.0), align=(HorizontalAlign.CENTRE, VerticalAlign.MIDDLE)), visuals=TextStyle(colour='mid'))
        z_test += TextFrame(parent=z_test, text="Foreground\n(z=1)", config=FrameConfig(scalers=(0.6, 0.4), align=(HorizontalAlign.RIGHT, VerticalAlign.BOTTOM), background=BackgroundStyle(colour='alert'), outline=OutlineStyle(colour='foreground', width=2), z_order=1), visuals=TextStyle(colour='background'))
        r3 += z_test