"""
All top level screens. Screens are comprised of Frames

Part of pyvisualiser v2.1.0 (Refactored to pristine dataclass API)
"""

from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
from pyvisualiser.visualisers.oscillogramme import *
from pyvisualiser.core.framecore import Frame, ColFramer, RowFramer
from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.base_defs import Channel, MetadataKey
from pyvisualiser.styles.styles import (
    TextStyle, ImageStyle, ProgressStyle, SpectrumStyle, BarStyle, 
    BarEffects, OutlineStyle, BackgroundStyle, ReflectionStyle, 
    VUMeterStyle, VUMeterScale, VUNeedleStyle
)
from test_spectrum import *

PI = 3.14159265358979323846


class Screen1(Frame):
    """Horizontal VUs with full meta data"""
    @property
    def title(self): return 'Horizontal VUs with full meta data'
    @property
    def type(self): return 'Visualiser and metadata'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', padding=0))

        BACK = BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.5, ambient_glow=True)
        cols = self.add_cols(ratios=(2, 3, 1.8), padpc=0.05, config=FrameConfig(outline=OutlineStyle(width=0, colour='light'), padding=0, background=BACK))

        cols += MetaImages(cols, key=MetadataKey.ALBUM, config=FrameConfig(background=None, outline=OutlineStyle(colour='light', width=5, opacity=1.0, radius=20)))
        cols += MetaDataFrame(cols, config=FrameConfig(background=None))
        cols += Diamondiser(cols, channel=Channel.MONO, config=FrameConfig(background=None))


class Screen2(Frame):
    """Base spectrum screen with artist background"""
    @property
    def title(self): return 'Base spectrum screen with artist background'
    @property
    def type(self): return 'Visualiser and metadata'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='std', background='background'))
        
        bg_art = BackgroundStyle(texture_path='artist', texture_opacity=1.0)
        colframe = self.add_cols(config=FrameConfig(background=bg_art))
        
        colframe += StereoSpectrumFrame(colframe)
        colframe += MetaDataFrame(colframe, config=FrameConfig(background=None))


class Screen3(Frame):
    """Multi-column structured layout with spectrum and progress bars"""
    @property
    def title(self): return 'Structured Multi-Column Dashboard'
    @property
    def type(self): return 'Visualiser and metadata'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='space', padding=5))

        colframe = self.add_cols(ratios=(1, 2, 1), padpc=0.1, config=FrameConfig(padding=10))

        row1 = colframe.add_rows(ratios=(5, 1))
        row1 += MetaImages(row1, key=MetadataKey.ALBUM, config=FrameConfig(outline=OutlineStyle(colour='light', width=5, opacity=0.8, radius=10)))
        row1 += MetaData(row1, key=MetadataKey.ALBUM, visuals=TextStyle(justify=('centre', 'middle'), colour='mid'))

        row2 = colframe.add_rows(ratios=(5, 0.3, 1), padpc=0.0)
        spec_style = SpectrumStyle(barw_min=3, barsize_pc=1, bar_style=BarStyle(led_gap=5, peak_h=3, radius=4, tip=True))
        row2 += SpectrumFrame(row2, channel=Channel.MONO, visuals=spec_style)
        row2 += PlayProgressFrame(row2)
        row2 += MetaData(row2, key=MetadataKey.TRACK, visuals=TextStyle(justify=('centre', 'middle')))

        row3 = colframe.add_rows(ratios=(5, 1), padpc=0.0)
        row3 += MetaImages(row3, key=MetadataKey.ARTIST, config=FrameConfig(outline=OutlineStyle(colour='light', width=5, opacity=0.8, radius=10)))
        row3 += MetaData(row3, key=MetadataKey.ARTIST, visuals=TextStyle(justify=('centre', 'middle'), colour='mid'))


class Screen4(Frame):
    """Atmospheric particle background with offset album art and spectrum"""
    def __init__(self, parent):
        particles = {'count': 80, 'colour': 'light', 'speed': 0.2, 'size': 1, 'softness': 0.1}
        bg = BackgroundStyle(colour='background', colour_opacity=0.0)
        super().__init__(parent, config=FrameConfig(background=bg, theme='tea'))

        back = BackgroundStyle(colour='background', colour_opacity=0.0)
        cols = self.add_cols(ratios=(1, 2), config=FrameConfig(padding=5))
        
        cols += MetaImages(cols, key=MetadataKey.ALBUM, config=FrameConfig(outline=OutlineStyle(colour='mid', width=3, radius=10), padding=10, background=BackgroundStyle(colour_opacity=0.0)))
        
        rows = cols.add_rows(ratios=(3, 1), padpc=0.0)
        rows += MetaDataFrame(rows, config=FrameConfig(background=back))
        
        spec_style = SpectrumStyle(barsize_pc=4, bar_style=BarStyle(led_gap=0))
        rows += SpectrumFrame(cols, channel=Channel.MONO, visuals=spec_style, config=FrameConfig(background=back))


class Screen5(Frame):
    """Analogue VU Meters paired with metadata card"""
    @property
    def title(self): return 'Analogue VU Meters, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        back = BackgroundStyle(texture_path='carbonfibre.jpg', texture_opacity=1.0)
        super().__init__(platform, config=FrameConfig(background=back, theme='meter1', padding=30))

        ENDSTOPS = (3 * PI / 4, 5 * PI / 4)
        PIVOT = -0.5
        OUTLINE = OutlineStyle(colour='foreground', width=5, opacity=1.0, radius=10)
        BACK = BackgroundStyle(colour='dark', colour_opacity=0.04, ambient_glow=True)

        cols = self.add_cols(padpc=0.05)
        meter_style = VUMeterStyle(pivot=PIVOT, scale=VUMeterScale(arcs={}), endstops=ENDSTOPS, needle=VUNeedleStyle())

        cols += VUMeter(cols, channel=Channel.LEFT, visuals=meter_style, config=FrameConfig(square=False, outline=OUTLINE, background=BACK))
        cols += MetaDataFrame(cols, config=FrameConfig(padding=0, background=None))
        cols += VUMeter(cols, channel=Channel.RIGHT, visuals=meter_style, config=FrameConfig(square=False, outline=OUTLINE, background=BACK))


class Screen6(Frame):
    """Volume/Source on left - Spectrum on left - one channel"""
    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', background='waves.png', padding=20))
        rows = self.add_rows(ratios=(1, 7), padpc=0.1)
        rows += MetaData(rows, key=MetadataKey.TRACK, config=FrameConfig(background=None))
        rows += SpectrumFrame(rows, channel=Channel.MONO, config=FrameConfig(outline=OutlineStyle(width=0), background=BackgroundStyle(colour='background', colour_opacity=0.6, ambient_glow=True)),
                               visuals=SpectrumStyle(bar_style=BarStyle(edge_softness=0.1)))


class Screen7(Frame):
    """Oscillogram, Roon Album Art, Metadata and progress bar"""
    @property
    def title(self): return 'Oscillogram, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='red'))
        rows = self.add_rows(ratios=(3, 1), config=FrameConfig(background=BackgroundStyle(texture_path='stream.png', texture_opacity=0.4)))
        
        subframe = rows.add_cols(ratios=(1.5, 4, 0.1), padpc=0.1)
        subframe += MetaImages(subframe, key=MetadataKey.ALBUM, config=FrameConfig(background=None))
        subframe += MetaDataFrame(subframe, config=FrameConfig(scalers=(1.0, 1.0), background=None))
        
        rows += Oscilogramme(rows, channel=Channel.MONO, config=FrameConfig(background=None))


class ProfileTestScreen(Frame):
    """Profile Controls Tuning Screen"""
    @property
    def title(self): return 'Profile Controls Tuning'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='std', background=None, padding=20))
        
        rows = self.add_rows(ratios=(1, 4), config=FrameConfig(padding=10))
        text = "PROFILE CONTROLS TEST MENU\nPress 1(Luxury), 2(Neon), 3(Minimal). Press 'L' for HUD."
        rows += TextFrame(rows, text=text, visuals=TextStyle(colour='light', justify=('centre', 'middle')))

        cols = rows.add_cols(config=FrameConfig(padding=10))
        effects = BarEffects(reflection=ReflectionStyle(size=0.4, opacity=0.3))
        bar_style = BarStyle(led_gap=2, peak_h=3, radius=1, tip=True, flip=False, colour_mode='vert', effects=effects)
        spectrum_style = SpectrumStyle(barw_min=8, barsize_pc=0.5, barw_max=25, bar_style=bar_style)
        
        spectrum_wrapper = cols.add_rows(config=FrameConfig(padding=10))
        spectrum_wrapper += SpectrumFrame(spectrum_wrapper, channel=Channel.MONO, visuals=spectrum_style)
        
        cols += MetaImages(cols, key=MetadataKey.ALBUM, config=FrameConfig(outline=OutlineStyle(colour='light', width=4, glow_intensity=1.0, softness=0.5)))
        
        meter_style = VUMeterStyle(pivot=-0.5, endstops=(3 * PI / 4, 5 * PI / 4), needle=VUNeedleStyle(width=4, colour='light', length=0.8, radius_pc=1.0))
        cols += VUMeter(cols, channel=Channel.LEFT, visuals=meter_style, config=FrameConfig(square=False, background=None))