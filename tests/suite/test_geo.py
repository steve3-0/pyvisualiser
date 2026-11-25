#!/usr/bin/env python3
"""
Geometry layout, bounding boxes, and hybrid test screens.
Part of pyvisualiser v2.1.0 (Refactored to pristine dataclass API)
"""

from pyvisualiser.core.base_defs import Channel, MetadataKey, HorizontalAlign, VerticalAlign
from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.framecore import Frame, ColFramer, RowFramer
from pyvisualiser.styles.styles import (
    BackgroundStyle,
    OutlineStyle,
    TextStyle,
    ImageStyle,
    BarStyle,
    SpectrumStyle,
    VUBarStyle,
)
from pyvisualiser.visualisers.vumeters import VU2chFrame, VUFrame
from pyvisualiser.visualisers.metadata import MetaImages, TextFrame, MetaData, MetaDataFrame
from pyvisualiser.visualisers.spectrum import SpectrumFrame
from pyvisualiser.visualisers.oscillogramme import OscilogrammeBar


class MixedLEDScreen(Frame):
    """Volume/Source on left - Stereo Spectrum overlaid"""
    @property
    def title(self): return 'Mixed LED Screen'
    @property
    def type(self): return 'Hi-Fi'

    def __init__(self, platform):
        bg = BackgroundStyle(colour='background', colour_opacity=1.0)
        super().__init__(platform, config=FrameConfig(padding=50, background=bg, outline=OutlineStyle(width=2, colour='alert'), theme='hifi'))
        
        col_bg = BackgroundStyle(colour='dark', colour_opacity=0.08)
        cols = self.add_cols(ratios=(4, 1), config=FrameConfig(background=col_bg, padding=0, outline=OutlineStyle(width=4, colour='mid')))
        
        spec_vis = SpectrumStyle(barw_min=6, barsize_pc=0.2, bar_style=BarStyle(peak_h=2, led_gap=3, led_h=5))
        cols += SpectrumFrame(cols, channel=Channel.MONO, visuals=spec_vis, config=FrameConfig(theme='leds'))
        cols += VU2chFrame(cols, config=FrameConfig(background=None), visuals=VUBarStyle(bar_style=BarStyle(orient='vert', flip=False, led_gap=3, led_h=5)))


class TestScreen(Frame):
    @property
    def title(self): return 'Tests out Frames, nesting and components'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig())
        subframe = Frame(parent=self, config=FrameConfig(scalers=(1.0, 0.5), align=(HorizontalAlign.CENTRE, VerticalAlign.TOP)))
        self += Frame(parent=self, config=FrameConfig(scalers=(0.5, 0.3), align=(HorizontalAlign.LEFT, VerticalAlign.TOP)))
        self += Frame(parent=self, config=FrameConfig(scalers=(0.5, 0.3), align=(HorizontalAlign.RIGHT, VerticalAlign.BOTTOM)))
        self += Frame(parent=self, config=FrameConfig(scalers=(1.0, 0.25), align=(HorizontalAlign.CENTRE, VerticalAlign.MIDDLE)))


class ColAlignedScreen(Frame):
    @property
    def title(self): return 'ColAlignedScreen> Creates 3 box frames and aligns them horizontally, evenly'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', outline=OutlineStyle(width=20, colour='alert'), padding=0))
        self.create()

    def create(self):
        self += Frame(parent=self, config=FrameConfig(scalers=(0.5, 0.5), align=(HorizontalAlign.LEFT, VerticalAlign.MIDDLE), background=BackgroundStyle(colour='light'), outline=OutlineStyle(colour='alert', width=5)))
        self += Frame(parent=self, config=FrameConfig(scalers=(0.5, 0.5), align=(HorizontalAlign.RIGHT, VerticalAlign.BOTTOM), background=BackgroundStyle(colour='mid'), outline=OutlineStyle(colour='alert', width=5)))


class RowAlignedScreen(Frame):
    @property
    def title(self): return 'RowAlignedScreen> Aligns box frames horizontally'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi'))
        out = OutlineStyle(width=10, colour='alert')
        rowframe = self.add_rows(config=FrameConfig(scalers=(1.0, 1.0), padding=10, background=BackgroundStyle(colour='dark'), outline=out))
        rowframe += TextFrame(parent=rowframe, text='left', config=FrameConfig(scalers=(1.0, 1.0), background=BackgroundStyle(colour='light'), outline=out))
        rowframe += TextFrame(parent=rowframe, text='mid on a very long string that needs to be even longer', visuals=TextStyle(wrap=True), config=FrameConfig(background=BackgroundStyle(colour='mid'), outline=out))
        rowframe += MetaData(parent=rowframe, key=MetadataKey.TRACK, config=FrameConfig(outline=out), visuals=TextStyle(colour='foreground'))


class F1(Frame):
    @property
    def title(self): return 'F1> Creates 4 quadrant box frames'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        bg = BackgroundStyle(texture_path='stream.png', texture_opacity=1.0)
        super().__init__(platform, config=FrameConfig(theme='hifi', outline=OutlineStyle(width=10, colour='alert'), padding=10, background=bg))
        self.create()

    def create(self):
        self += Frame(parent=self, config=FrameConfig(scalers=(0.5, 0.5), align=(HorizontalAlign.LEFT, VerticalAlign.BOTTOM), outline=OutlineStyle(colour='foreground', width=10)))
        self += Frame(parent=self, config=FrameConfig(scalers=(0.5, 0.5), align=(HorizontalAlign.RIGHT, VerticalAlign.BOTTOM), background=None, outline=OutlineStyle(colour='foreground', width=10)))
        self += Frame(parent=self, config=FrameConfig(scalers=(0.5, 0.5), align=(HorizontalAlign.LEFT, VerticalAlign.TOP), background=None, outline=OutlineStyle(colour='foreground', width=10)))
        self += Frame(parent=self, config=FrameConfig(scalers=(0.5, 0.5), align=(HorizontalAlign.RIGHT, VerticalAlign.TOP), background=None, outline=OutlineStyle(colour='foreground', width=10)))


class F2(Frame):
    @property
    def title(self): return 'F2> Multi-position grid frames'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', outline=OutlineStyle(width=20, colour='alert'), padding=20))
        self += Frame(parent=self, config=FrameConfig(scalers=(0.3, 0.3), align=(HorizontalAlign.CENTRE, VerticalAlign.BOTTOM), background=BackgroundStyle(colour='light'), outline=OutlineStyle(colour='foreground', width=5)))
        self += Frame(parent=self, config=FrameConfig(scalers=(0.3, 0.3), align=(HorizontalAlign.RIGHT, VerticalAlign.BOTTOM), background=BackgroundStyle(colour='mid'), outline=OutlineStyle(colour='foreground', width=5)))
        self += Frame(parent=self, config=FrameConfig(scalers=(0.3, 0.3), align=(HorizontalAlign.LEFT, VerticalAlign.TOP), background=BackgroundStyle(colour='light'), outline=OutlineStyle(colour='foreground', width=5)))
        self += Frame(parent=self, config=FrameConfig(scalers=(0.3, 0.3), align=(HorizontalAlign.RIGHT, VerticalAlign.TOP), background=BackgroundStyle(colour='mid'), outline=OutlineStyle(colour='foreground', width=5)))
        self += Frame(parent=self, config=FrameConfig(scalers=(0.3, 0.3), align=(HorizontalAlign.LEFT, VerticalAlign.MIDDLE), background=BackgroundStyle(colour='light'), outline=OutlineStyle(colour='foreground', width=5)))
        self += Frame(parent=self, config=FrameConfig(scalers=(0.3, 0.3), align=(HorizontalAlign.RIGHT, VerticalAlign.MIDDLE), background=BackgroundStyle(colour='mid'), outline=OutlineStyle(colour='foreground', width=5)))


class F3(Frame):
    @property
    def title(self): return 'F3> Checks out Text Frames'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', outline=OutlineStyle(width=20, colour='foreground'), padding=30))
        self += TextFrame(parent=self, text='one', config=FrameConfig(scalers=(0.33, 1.0), align=(HorizontalAlign.LEFT, VerticalAlign.MIDDLE), background=BackgroundStyle(colour='mid'), outline=OutlineStyle(colour='alert', width=10), padding=10))
        self += TextFrame(parent=self, text='two', config=FrameConfig(scalers=(0.33, 1.0), align=(HorizontalAlign.CENTRE, VerticalAlign.MIDDLE), background=BackgroundStyle(colour='mid'), outline=OutlineStyle(colour='alert', width=10), padding=10))
        self += TextFrame(parent=self, text='three', config=FrameConfig(scalers=(0.33, 1.0), align=(HorizontalAlign.RIGHT, VerticalAlign.MIDDLE), background=BackgroundStyle(colour='mid'), outline=OutlineStyle(colour='alert', width=10), padding=10))


class F4(Frame):
    @property
    def title(self): return 'F4> Checks out Col Framer'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        bg = BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.4)
        super().__init__(platform, config=FrameConfig(theme='hifi', outline=OutlineStyle(width=5, colour='alert'), background=bg, padding=30))
        
        back = BackgroundStyle(colour='dark', colour_opacity=0.39, ambient_glow=True)
        colframe = self.add_cols(ratios=(1.0, 1.0, 1, 1), padpc=0.1, config=FrameConfig(align=(HorizontalAlign.CENTRE, VerticalAlign.MIDDLE), background=None, padding=0, outline=OutlineStyle(colour='alert', width=0)))
        
        colframe += TextFrame(parent=colframe, text='oneRT', config=FrameConfig(background=back, padding=0, outline=OutlineStyle(colour='foreground', width=1)), visuals=TextStyle(colour='foreground', justify=('right', 'top')))
        colframe += TextFrame(parent=colframe, text='wideC', config=FrameConfig(background=BackgroundStyle(colour='light'), outline=OutlineStyle(colour='alert', width=1)), visuals=TextStyle(colour='dark', justify=('centre', 'middle')))
        colframe += TextFrame(parent=colframe, text='threeLB', config=FrameConfig(background=back, outline=OutlineStyle(colour='mid', width=1)), visuals=TextStyle(colour='foreground', justify=('left', 'bottom')))
        
        rowframe = colframe.add_rows(padpc=0.0, config=FrameConfig(align=(HorizontalAlign.RIGHT, VerticalAlign.MIDDLE), background=back, padding=0.0, outline=OutlineStyle(colour='foreground', width=1)))
        rowframe += TextFrame(parent=rowframe, text='top', config=FrameConfig(scalers=(1.0, 1.0), background=BackgroundStyle(colour='mid'), outline=OutlineStyle(colour='foreground', width=0)))
        rowframe += TextFrame(parent=rowframe, text='rhs', config=FrameConfig(background=BackgroundStyle(colour='dark'), outline=OutlineStyle(colour='mid', width=0)), visuals=TextStyle(justify=('left', 'top')))
        rowframe += TextFrame(parent=rowframe, text='next', config=FrameConfig(background=BackgroundStyle(colour='dark'), outline=OutlineStyle(colour='mid', width=0)), visuals=TextStyle(justify=('centre', 'middle')))
        rowframe += TextFrame(parent=rowframe, text='b', config=FrameConfig(scalers=(1.0, 1.0), background=BackgroundStyle(colour='light')), visuals=TextStyle(justify=('right', 'bottom')))


class F5(Frame):
    @property
    def title(self): return 'F5 Checks background images'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        bg = BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.4)
        super().__init__(platform, config=FrameConfig(theme='hifi', outline=OutlineStyle(width=0, colour='alert'), padding=30, background=bg))
        
        colframe = self.add_cols(ratios=(1, 1, 2), config=FrameConfig(scalers=(1.0, 1.0), background=None, outline=OutlineStyle(colour='foreground', width=1), padding=0))
        colframe += TextFrame(parent=colframe, text='twoCM', config=FrameConfig(scalers=(1.0, 1.0), align=(HorizontalAlign.RIGHT, VerticalAlign.TOP), background=BackgroundStyle(colour='light'), outline=OutlineStyle(colour='alert', width=1)), visuals=TextStyle(justify=('centre', 'middle'), colour='dark'))
        colframe += VUFrame(parent=colframe, channel=Channel.LEFT, config=FrameConfig(align=(HorizontalAlign.RIGHT, VerticalAlign.MIDDLE), scalers=(1.0, 1.0), background=BackgroundStyle(colour='dark')), 
                            visuals=VUBarStyle(barsize_pc=1.0,bar_style=BarStyle(orient='horz',  led_gap=0, tip=True)))
        
        rowframe = colframe.add_rows(ratios=(1, 3, 1), config=FrameConfig(scalers=(1.0, 1.0), align=(HorizontalAlign.RIGHT, VerticalAlign.MIDDLE), background=BackgroundStyle(colour='dark'), padding=0.0))
        rowframe += TextFrame(parent=rowframe, text='row sub', config=FrameConfig(scalers=(1.0, 1.0), background=BackgroundStyle(colour='light')), visuals=TextStyle(colour='dark'))
        
        colframe2 = rowframe.add_cols(padpc=0, config=FrameConfig(scalers=(1.0, 1.0), align=(HorizontalAlign.CENTRE, VerticalAlign.MIDDLE), background=BackgroundStyle(colour='mid'), padding=0, outline=OutlineStyle(colour='alert', width=0)))
        colframe2 += TextFrame(parent=colframe2, text='a', config=FrameConfig(scalers=(1.0, 1.0), background=BackgroundStyle(colour='light')), visuals=TextStyle(colour='dark'))
        colframe2 += TextFrame(parent=colframe2, text='two', config=FrameConfig(scalers=(1.0, 1.0), background=BackgroundStyle(colour='dark'), outline=OutlineStyle(colour='mid', width=30)), visuals=TextStyle(colour='light'))
        colframe2 += TextFrame(parent=colframe2, text='mleftj',  config=FrameConfig(background=BackgroundStyle(colour='mid'), outline=OutlineStyle(colour='alert', width=1)), 
                               visuals=TextStyle(colour='foreground',wrap=True))
        
        rowframe += TextFrame(parent=rowframe, text='five', config=FrameConfig(scalers=(1.0, 0.5), align=(HorizontalAlign.LEFT, VerticalAlign.BOTTOM), background=BackgroundStyle(colour='dark'), outline=OutlineStyle(colour='mid', width=2)), visuals=TextStyle(colour='foreground'))


class F6(Frame):
    @property
    def title(self): return 'F6 Checks background images & VUs'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        bg = BackgroundStyle(texture_path='stream.png', texture_opacity=1.0)
        super().__init__(platform, config=FrameConfig(theme='hifi', outline=OutlineStyle(width=0, colour='alert'), padding=10, background=bg))
        self.create()

    def create(self):
        colframe = self.add_cols(ratios=(1, 1, 1), config=FrameConfig(scalers=(1.0, 1.0), background=None, outline=OutlineStyle(colour='foreground', width=1), padding=10))
        colframe += MetaDataFrame(parent=colframe)
        colframe += VUFrame(parent=colframe, channel=Channel.LEFT, config=FrameConfig(align=(HorizontalAlign.RIGHT, VerticalAlign.MIDDLE), scalers=(1.0, 1.0), background=BackgroundStyle(colour='dark')), visuals=VUBarStyle(barsize_pc=1.0,bar_style=BarStyle(orient='vert',  led_gap=0, tip=True)))


class F7(Frame):
    @property
    def title(self): return 'F7> Checks out Bars'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        bg = BackgroundStyle(texture_path='stream.png', texture_opacity=1.0)
        super().__init__(platform, config=FrameConfig(theme='std', outline=OutlineStyle(width=20, colour='foreground'), padding=30, background=bg))
        self.create()

    def create(self):
        col = self.add_cols(ratios=(2, 1, 1), config=FrameConfig(background=BackgroundStyle(colour='dark')))
        col += VUFrame(parent=col, channel=Channel.LEFT, config=FrameConfig(align=(HorizontalAlign.RIGHT, VerticalAlign.MIDDLE), scalers=(1.0, 1.0), background=BackgroundStyle(colour='dark')), 
                       visuals=VUBarStyle(barsize_pc=1.0, bar_style=BarStyle(orient='horz', led_gap=0, tip=True)))


class F8(Frame):
    @property
    def title(self): return 'F8 > Check out Spectrum Analyser'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='white', background=BackgroundStyle(colour='background')))
        cols = self.add_cols(config=FrameConfig(background=BackgroundStyle(colour='background')))
        
        spec_style = SpectrumStyle(barw_min=3, barsize_pc=2, bar_style=BarStyle(led_gap=0, peak_h=1, radius=0, tip=True))
        cols += SpectrumFrame(parent=cols, channel=Channel.MONO, visuals=spec_style, config=FrameConfig(background=BackgroundStyle(colour='background')))
        
        artoutline = OutlineStyle(colour='background', width=5)
        cols += MetaImages(parent=cols, key=MetadataKey.ARTIST, visuals=ImageStyle(opacity=0.6), config=FrameConfig(outline=artoutline))
        cols += MetaDataFrame(parent=cols)