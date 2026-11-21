#!/usr/bin/env python3
"""
Analogue & Digital VU Meter Test Screens
Part of pyvisualiser v2.1.0 (Refactored to pristine dataclass API)
"""

from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.styles.presets import *
from pyvisualiser.styles.styles import *
from pyvisualiser.core.base_defs import Channel
from pyvisualiser.core.framecore import Frame, ColFramer, RowFramer
from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.visualisers.metadata import MetaDataFrame, PlayProgressFrame, TextFrame


class VUTungstenScreen(Frame):
    @property
    def title(self): return 'Analogue VU Meter - Tungsten Style'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='meter2', padding=0))
  
        MARKS_METER2 = {
            0.1: {'text': '-40', 'width': 2, 'colour': 'dark'},
            0.3: {'text': '-20', 'width': 2, 'colour': 'dark'},
            0.5: {'text': '-5',  'width': 2, 'colour': 'dark'},
            0.65: {'text': '-3', 'width': 2, 'colour': 'dark'},
            0.72: {'text': '+0', 'width': 3, 'colour': 'alert'},
            0.8: {'text': '+3',  'width': 4, 'colour': 'alert'},
            0.9: {'text': '+6',  'width': 4, 'colour': 'alert'}
        }

        NEEDLE_METER2 = VUNeedleStyle(colour='foreground', width=3, length=0.8, radius_pc=1.0)

        METER_BACKGROUND = BackgroundStyle(
            colour='dark',
            ambient_glow=AmbientGlowStyle(colour='light', opacity=0.6, radius=1.5, softness=0.7)
        )

        METER_OUTLINE = OutlineStyle(width=15, radius=25, colour='dark', glow_intensity=0.05)

        cols = self.add_cols(padpc=0.05, config=FrameConfig(padding=30))
        for channel in (Channel.LEFT, Channel.RIGHT):
            meter_style = VUMeterStyle(
                pivot=-0.5,
                endstops=(3 * PI / 4, 5 * PI / 4),
                needle=NEEDLE_METER2,
                show_peak=True,
                scale=VUMeterScale(marks=MARKS_METER2, arcs=None, annotate={'text': channel})
            )
            cols += VUMeter(cols, channel=channel, visuals=meter_style, config=FrameConfig(square=False, outline=METER_OUTLINE, background=METER_BACKGROUND))
        
        cols += MetaDataFrame(cols, config=FrameConfig(padding=0, background=None, z_order=10))


class VUTestScreen1(Frame):
    @property
    def title(self): return 'Analogue VU Meters, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        back = BackgroundStyle(texture_path='carbonfibre.jpg', texture_opacity=1.0)
        super().__init__(platform, config=FrameConfig(background=back, theme='meter1', padding=0))
  
        NEEDLE = VUNeedleStyle(
            colour='foreground', width=2, length=0.8, radius_pc=1.0, 
            glow_intensity=0.5, glow_colour='dark', tip_glow=True, shadow=True
        )     
        ENDSTOPS = (3 * PI / 4, 5 * PI / 4)
        PIVOT = -0.5

        meter = VUMeterStyle(pivot=PIVOT, endstops=ENDSTOPS, needle=NEEDLE)

        cols = self.add_cols(padpc=0.05, config=FrameConfig(padding=30))
        cols += VUMeter(cols, channel=Channel.LEFT, visuals=meter, config=FrameConfig(square=False, outline=VUOutline, background=VUBackground))
        cols += MetaDataFrame(cols, config=FrameConfig(padding=0, background=None, z_order=10))
        cols += VUMeter(cols, channel=Channel.RIGHT, visuals=meter, config=FrameConfig(square=False, outline=VUOutline, background=VUBackground))


class VUTestScreen2(Frame):
    @property
    def title(self): return 'Analogue VU Meters, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        back = BackgroundStyle(texture_path='carbonfibre.jpg', texture_opacity=1.0)
        super().__init__(platform, config=FrameConfig(background=back, theme='meter2', padding=0))

        glow = AmbientGlowStyle(colour='mid', radius=0.2, softness=0.3, opacity=0.95)
        outline = OutlineStyle(colour='mid', width=10, opacity=1.0, radius=25, glow_intensity=0.3, softness=0.1)  
        background = BackgroundStyle(colour='background', ambient_glow=glow, texture_path='carbonfibre.jpg', texture_opacity=0.3)
        self += VUMeterFrame4(self, config=FrameConfig(theme='meter2', background=background, outline=outline))


class VUNeedleEffectsScreen(Frame):
    @property
    def title(self): return 'VU Needle Effects Test'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        back = BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.5)
        super().__init__(platform, config=FrameConfig(theme='hifi', background=back))
        
        cols = self.add_cols(config=FrameConfig(padding=30), padpc=0.05)
        
        meter_bg = BackgroundStyle(
            colour='background', 
            ambient_glow=AmbientGlowStyle(colour='light', opacity=0.3, radius=2.0, softness=0.8),
            vignette=VignetteStyle(strength=0.6, radius=0.4, softness=0.6),
            noise=NoiseStyle(strength=0.4)
        )

        # 1. Standard Needle
        needle_style = VUNeedleStyle(colour='alert', width=4, shadow=True, glow_colour='alert')
        cols += VUMeter(cols, channel=Channel.MONO, visuals=VUMeterStyle(needle=needle_style), config=FrameConfig(background=meter_bg, outline=OutlineStyle(width=4, radius=10, colour='mid', glow_intensity=0.1, softness=0.2)))
        
        # 2. Glowing Needle
        glow_style = VUNeedleStyle(colour='alert', width=4, glow_intensity=0.3, glow_colour='alert')
        cols += VUMeter(cols, channel=Channel.MONO, visuals=VUMeterStyle(needle=glow_style), config=FrameConfig(background=meter_bg, outline=OutlineStyle(width=4, radius=10, colour='mid', glow_intensity=0.1, softness=0.2)))
        
        # 3. Tip Glow (High Level)
        tip_style = VUNeedleStyle(colour='light', width=4, tip_glow=True, glow_colour='alert')
        cols += VUMeter(cols, channel=Channel.MONO, visuals=VUMeterStyle(needle=tip_style), config=FrameConfig(background=meter_bg, outline=OutlineStyle(width=4, radius=10, colour='mid', glow_intensity=0.1, softness=0.2)))


class VUNeedleStylesScreen(Frame):
    @property
    def title(self): return 'VU Needle Styles Gallery'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='std', background=BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.5)))
        
        cols = self.add_cols(config=FrameConfig(padding=30), padpc=0.05)
        
        # 1. Standard Hi-Fi Needle
        needle1 = VUNeedleStyle(colour='foreground', width=3, length=0.85, radius_pc=1.0, glow_intensity=0.0)
        style1 = VUMeterStyle(needle=needle1)
        c1 = cols.add_rows(ratios=(5, 1))
        c1 += VUMeter(c1, channel=Channel.MONO, visuals=style1, config=FrameConfig(background='dark', outline=OutlineStyle(colour='mid', width=2)))
        c1 += TextFrame(c1, text="Standard Hi-Fi", config=FrameConfig(align=('centre', 'top')))

        # 2. Glowing "Laser" Needle
        needle2 = VUNeedleStyle(colour='alert', width=4, length=1.0, radius_pc=0.9, glow_intensity=0.2, glow_colour='alert', tip_glow=True)
        style2 = VUMeterStyle(needle=needle2)
        c2 = cols.add_rows(ratios=(5, 1))
        c2 += VUMeter(c2, channel=Channel.MONO, visuals=style2, config=FrameConfig(background='dark', outline=OutlineStyle(colour='mid', width=2)))
        c2 += TextFrame(c2, text="Laser Glow", config=FrameConfig(align=('centre', 'top')))

        # 3. Floating Tick
        needle3 = VUNeedleStyle(colour='light', width=5, length=0.95, radius_pc=0.15)
        style3 = VUMeterStyle(needle=needle3)
        c3 = cols.add_rows(ratios=(5, 1))
        c3 += VUMeter(c3, channel=Channel.MONO, visuals=style3, config=FrameConfig(background='dark', outline=OutlineStyle(colour='mid', width=2)))
        c3 += TextFrame(c3, text="Floating Tick", config=FrameConfig(align=('centre', 'top')))


class VUImageScreen(Frame):
    @property
    def title(self): return 'VU meters with image background'
    @property
    def type(self): return 'VU Image'

    def __init__(self, platform, type='blueVU'):
        back = BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.8)
        super().__init__(platform, config=FrameConfig(theme='hifi', background=back, padding=0))

        rows = self.add_rows(ratios=(15, 1), padpc=0.05, config=FrameConfig(padding=0))
        rows += VUMeterImageFrame(rows, type=type, config=FrameConfig(outline=None))
        rows += PlayProgressFrame(rows, config=FrameConfig(background=None))


class VUVintageScreen(Frame):
    @property
    def title(self): return 'Vintage VU meters with image background'
    @property
    def type(self): return 'VU Image'

    def __init__(self, platform, type='Vintage-VU.png'):
        glow = AmbientGlowStyle(colour='foreground', radius=0.5, softness=0.1, opacity=0.6)
        back = BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.8, ambient_glow=glow)
        super().__init__(platform, config=FrameConfig(theme='hifi', background=back, padding=0))
        self += VUMeterImageFrame(self, type='OldVU', config=FrameConfig(outline=OutlineDefault))


class VUModernScreen(Frame):
    @property
    def title(self): return 'Modern VU meters with image background'
    @property
    def type(self): return 'VU Image'

    def __init__(self, platform, type='blueVU'):       
        back = BackgroundStyle(texture_path='metal.jpg', texture_opacity=0.8)
        super().__init__(platform, config=FrameConfig(theme='hifi', background=back, padding=0))
        self += VUMeterImageFrame(self, type='ModVU', config=FrameConfig(outline=None))


class TestVUImageScreen1(Frame):
    @property
    def title(self): return 'Test multiple VU meters with image backgrounds'
    @property
    def type(self): return 'Test'

    def __init__(self, platform, type=None):
        back = BackgroundStyle(colour='background', colour_opacity=1.0)
        super().__init__(platform, config=FrameConfig(background=back))

        self += VUMeterImageFrame(self, type='blueVU', config=FrameConfig(scalers=(0.5, 0.5), align=('left', 'top')))
        self += VUMeterImageFrame(self, type='goldVU', config=FrameConfig(scalers=(0.5, 0.5), align=('left', 'bottom')))
        self += VUMeterImageFrame(self, type='blackVU', config=FrameConfig(scalers=(0.5, 0.5), align=('right', 'top')))
        self += VUMeterImageFrame(self, type='rainVU', config=FrameConfig(scalers=(0.5, 0.5), align=('right', 'bottom')))


class TestVUImageScreen2(Frame):
    @property
    def title(self): return 'Test multiple VU meters with image backgrounds'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig())
        self += VUMeterImageFrame(self, type='redVU', config=FrameConfig(scalers=(0.5, 0.5), align=('left', 'top')))
        self += VUMeterImageFrame(self, type='vintVU', config=FrameConfig(scalers=(0.5, 0.5), align=('left', 'bottom')))
        self += VUMeterImageFrame(self, type='whiteVU', config=FrameConfig(scalers=(0.5, 0.5), align=('right', 'top')))
        self += VUMeterImageFrame(self, type='greenVU', config=FrameConfig(scalers=(0.5, 0.5), align=('right', 'bottom')))


class TestVUMetersScreen(Frame):
    @property
    def title(self): return 'Tests out multiple configurations of Stereo VU Meters'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        back = BackgroundStyle(colour='background', colour_opacity=1.0)
        super().__init__(platform, config=FrameConfig(background=back))

        self += VUMeterFrame1(self, config=FrameConfig(scalers=(0.5, 0.5), align=('left', 'top')))
        self += VUMeterFrame2(self, config=FrameConfig(scalers=(0.5, 0.5), align=('left', 'bottom')))
        self += VUMeterFrame3(self, config=FrameConfig(scalers=(0.5, 0.5), align=('right', 'top')))
        self += VUMeterFrame4(self, config=FrameConfig(scalers=(0.5, 0.5), align=('right', 'bottom')))


class VUMeterFrame1(Frame):
    def __init__(self, parent, config=None, scalers=None, align=('centre', 'middle')):
        cfg = config if config is not None else FrameConfig(scalers=scalers, align=align)
        super().__init__(parent, config=cfg)
        style = VUMeterStyle(
            endstops=(3 * PI / 4 - 0.2, 5 * PI / 4 + 0.2), 
            needle=VUNeedleStyle(width=4, colour='foreground', length=0.8, radius_pc=1.0),
            scale=VUMeterScale(arcs={})
        )
        self += VUMeter(self, channel=Channel.LEFT, config=FrameConfig(scalers=(0.5, 1.0), align=('left', 'bottom')), visuals=style)
        self += VUMeter(self, channel=Channel.RIGHT, config=FrameConfig(scalers=(0.5, 1.0), align=('right', 'bottom')), visuals=style)


class VUMeterFrame2(Frame):
    def __init__(self, parent, config=None, scalers=None, align=('centre', 'middle')):
        cfg = config if config is not None else FrameConfig(scalers=scalers, align=align)
        super().__init__(parent, config=cfg)
        
        TICK_W = 3
        TICKLEN = 0.8
        TICK_PC = 0.1
        SCALESLEN = 0.9
        ARCLEN = TICKLEN * (1 - TICK_PC)

        MARKS = {
            0.0: {'text': '0', 'width': TICK_W, 'colour': 'mid'},
            0.14: {'text': '1', 'width': TICK_W, 'colour': 'mid'},
            0.28: {'text': '2', 'width': TICK_W, 'colour': 'mid'},
            0.42: {'text': '3', 'width': TICK_W, 'colour': 'mid'},
            0.56: {'text': '4', 'width': TICK_W, 'colour': 'light'},
            0.70: {'text': '5', 'width': TICK_W, 'colour': 'light'},
            0.84: {'text': '6', 'width': TICK_W, 'colour': 'alert'},
            1.0: {'text': '7', 'width': TICK_W, 'colour': 'alert'}
        }
        ARCS = {ARCLEN: {'width': TICK_W // 2, 'colour': 'mid'}}
        ANNOTATE = {'Valign': 'middle', 'text': 'PPM', 'colour': 'mid'}
        
        style = VUMeterStyle(
            endstops=(PI / 2, 3 * PI / 2),
            pivot=-0.4, 
            needle=VUNeedleStyle(width=4, colour='foreground', length=0.8, radius_pc=1.0),
            scale=VUMeterScale(marks=MARKS, arcs=ARCS, annotate=ANNOTATE, tick_width=TICK_W, tick_length=TICKLEN, tick_radius_pc=TICK_PC, scale_radius=SCALESLEN), 
            show_peak=True
        )

        self += VUMeter(self, channel=Channel.LEFT, config=FrameConfig(scalers=(0.5, 1.0), align=('left', 'bottom')), visuals=style)
        self += VUMeter(self, channel=Channel.RIGHT, config=FrameConfig(scalers=(0.5, 1.0), align=('right', 'bottom')), visuals=style)


class VUMeterFrame3(Frame):
    def __init__(self, parent, config=None, scalers=None, align=('left', 'bottom')):
        cfg = config if config is not None else FrameConfig(scalers=scalers, align=align)
        super().__init__(parent, config=cfg)
        
        TICK_W = 3
        ARCLEN = 0.70
        MARKS = {
            0.0: {'text': '0', 'width': TICK_W, 'colour': 'mid'},
            0.14: {'text': '1', 'width': TICK_W, 'colour': 'mid'},
            0.28: {'text': '2', 'width': TICK_W, 'colour': 'mid'},
            0.42: {'text': '3', 'width': TICK_W, 'colour': 'mid'},
            0.56: {'text': '4', 'width': TICK_W, 'colour': 'light'},
            0.70: {'text': '5', 'width': TICK_W, 'colour': 'light'},
            0.84: {'text': '6', 'width': TICK_W, 'colour': 'alert'},
            1.0: {'text': '7', 'width': TICK_W, 'colour': 'alert'}
        }
        ARCS = {ARCLEN: {'width': TICK_W // 2, 'colour': 'mid'}}
        ANNOTATE = {'Valign': 'bottom', 'text': 'Peak RMS', 'colour': 'mid'}
        
        style = VUMeterStyle(
            pivot=0,
            endstops=(PI / 4, 7 * PI / 4),
            scale=VUMeterScale(marks=MARKS, arcs=ARCS, annotate=ANNOTATE, tick_width=TICK_W)
        )

        self += VUMeter(self, channel=Channel.LEFT, config=FrameConfig(scalers=(0.5, 1.0), align=('left', 'bottom')), visuals=style)
        self += VUMeter(self, channel=Channel.RIGHT, config=FrameConfig(scalers=(0.5, 1.0), align=('right', 'bottom')), visuals=style)


class VUMeterFrame4(Frame):
    def __init__(self, parent, theme='meter1', background=VUBackground, outline=VUOutline, config=None, scalers=None, align=('left', 'bottom')):
        cfg = config if config is not None else FrameConfig(theme=theme, background=background, outline=outline, scalers=scalers, align=align)
        super().__init__(parent, config=cfg)
        
        TICK_W = 3
        TICK_PC = 0.1
        ARCLEN = 0.8
        MARKS = {
            0.0: {'text': '-20', 'width': TICK_W, 'colour': 'mid'},
            0.1: {'text': '-15', 'width': TICK_W, 'colour': 'mid'},
            0.2: {'text': '-10', 'width': TICK_W, 'colour': 'mid'},
            0.3: {'text': '-7', 'width': TICK_W, 'colour': 'mid'},
            0.4: {'text': '-5', 'width': TICK_W, 'colour': 'mid'},
            0.5: {'text': '-3', 'width': TICK_W, 'colour': 'mid'},
            0.6: {'text': '-1', 'width': TICK_W, 'colour': 'mid'},
            0.7: {'text': '0', 'width': TICK_W * 2, 'colour': 'alert'},
            0.8: {'text': '+1', 'width': TICK_W * 2, 'colour': 'alert'},
            0.9: {'text': '+2', 'width': TICK_W * 2, 'colour': 'alert'},
            1.0: {'text': '+3', 'width': TICK_W * 2, 'colour': 'alert'}
        }
        ARCS = {ARCLEN * (1 - TICK_PC): {'width': TICK_W - 1, 'colour': 'mid'}}
        ANNOTATE = {'Valign': 'middle', 'text': 'dB', 'colour': 'mid'}
        
        style = VUMeterStyle(
            pivot=-0.7,
            endstops=(3 * PI / 4, 5 * PI / 4),
            pivotcovercolour='foreground',
            pivotcoverpc=0.28,
            needle=VUNeedleStyle(width=2, colour='foreground', length=0.8, radius_pc=0.7, glow_intensity=0.3, glow_colour='foreground', tip_glow=True, shadow=True),
            scale=VUMeterScale(marks=MARKS, arcs=ARCS, annotate=ANNOTATE, tick_width=TICK_W, tick_radius_pc=TICK_PC)
        )

        cols = self.add_cols(config=FrameConfig(padding=30), padpc=0.05)
        cols += VUMeter(cols, channel=Channel.LEFT, visuals=style, config=FrameConfig(background=background, outline=outline, theme=theme))
        cols += VUMeter(cols, channel=Channel.RIGHT, visuals=style, config=FrameConfig(background=background, outline=outline, theme=theme))