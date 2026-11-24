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
    TextStyle, ImageStyle, PlayProgressStyle, SpectrumStyle, BarStyle, 
    BarEffects, OutlineStyle, BackgroundStyle, ReflectionStyle, 
    VUMeterStyle, VUMeterScale, VUNeedleStyle
)
from suite.test_spectrum import *

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
        super().__init__(platform, config=FrameConfig(theme='std', background=BackgroundStyle(colour='background')))
        
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
        super().__init__(platform, config=FrameConfig(theme='hifi', background=BackgroundStyle(texture_path='waves.png'), padding=20))       
        rows = self.add_rows(ratios=(1, 7), padpc=0.1)
        rows += MetaData(rows, key=MetadataKey.TRACK, config=FrameConfig(background=None))
        rows += SpectrumFrame(
            rows,
            channel=Channel.MONO,
            config=FrameConfig(
                outline=OutlineStyle(width=0),
                background=BackgroundStyle(colour='background', colour_opacity=0.6, ambient_glow=True)
            ),
            visuals=SpectrumStyle(bar_style=BarStyle(edge_softness=0.1))
        )


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


class LEDtestScreen(Frame):
    @property
    def title(self): return 'LED Test Screen'   
    @property
    def type(self): return 'Test'

    def __init__(self, platform):   
        super().__init__(platform, config=FrameConfig(theme='std', background=BackgroundStyle(colour='background')))
  
        col = self.add_cols(ratios=(10, 6), padpc=0.0, config=FrameConfig(padding=0))

        bars = BarStyle(led_gap=5, peak_h=3, radius=0, tip=False, effects=NeonGlow)
        spectrum = SpectrumStyle(barw_min=19, barsize_pc=0.1,  bar_style=bars)
        
        col += SpectrumFrame(col, channel=Channel.MONO, visuals=spectrum)
        col += VUFrame(col, channel=Channel.MONO, visuals=VUBarStyle(barsize_pc=1.0, bar_style=BarStyle(orient='vert', led_h=20, led_gap=2, tip=False, effects=NeonGlow)))


class TrackScreen(Frame):
    @property
    def title(self): return 'Roon Album Art, Metadata and progress bar - Trackscreen'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='ocean', background=BackgroundStyle(colour='background')))
        cols = self.add_cols(ratios=(1, 2, 1), padpc=0.05)
        cols += VU2chHorzFrame(cols)
        cols += MetaDataFrame(cols)
        cols += MetaImages(cols, config=FrameConfig(outline=OutlineStyle(colour='dark', width=2)))


class TrackVisScreen(Frame):
    @property
    def title(self): return 'Visualiser, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='blue'))

        self += MetaImages(self, key=MetadataKey.ALBUM, config=FrameConfig(scalers=(0.31, 1.0), align=('left', 'middle')))
        self += MetaDataFrame(self, config=FrameConfig(scalers=(0.38, 1.0), align=('centre', 'middle')))
        self += Diamondiser(self, channel=Channel.LEFT, config=FrameConfig(scalers=(0.31, 1.0), align=('right', 'middle')))


class TrackVisScreen2(Frame):
    @property
    def title(self): return 'Complex Visualiser, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='tea'))

        self += MetaData(self, key=MetadataKey.ARTIST, config=FrameConfig(scalers=(0.33, 0.2), align=('centre', 'top')))
        self += MetaData(self, key=MetadataKey.TRACK, config=FrameConfig(scalers=(0.33, 0.2), align=('centre', 'middle')))
        self += MetaData(self, key=MetadataKey.ALBUM, config=FrameConfig(scalers=(0.33, 0.2), align=('centre', 'bottom')))
        self += PlayProgressFrame(self, config=FrameConfig(scalers=(1.0, 0.05), align=('centre', 'bottom')))


class TrackSpectrumScreen(Frame):
    @property
    def title(self): return 'Spectrum Analyser, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='blue'))

        self += MetaDataFrame(self, config=FrameConfig(scalers=(0.33, 1.0), align=('centre', 'middle')))
        self += MetaImages(self, key=MetadataKey.ALBUM, config=FrameConfig(scalers=(0.31, 1.0), align=('right', 'middle')))
        
        spec_style = SpectrumStyle(barw_min=5, barsize_pc=0.6, bar_style=BarStyle(led_gap=0, peak_h=1, radius=0, tip=True))
        self += SpectrumFrame(self, channel=Channel.MONO, config=FrameConfig(scalers=(0.33, 1.0), align=('left', 'bottom')), visuals=spec_style)


class TrackSpectrumScreen2(Frame):
    @property
    def title(self): return 'Spectrum Analyser 2, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='white'))

        cols = self.add_cols(config=FrameConfig())
        cols += StereoSpectrumFrame(cols)
        
        artoutline = OutlineStyle(colour='background', width=5)
        cols += MetaImages(cols, key=MetadataKey.ARTIST, config=FrameConfig(scalers=(0.8, 1.0), align=('left', 'middle'), outline=artoutline), visuals=ImageStyle(opacity=0.9))
        cols += MetaDataFrame(cols, config=FrameConfig(scalers=(1.0, 1.0), align=('right', 'middle')))


class MetaArtFrame(Frame):
    """A subframe to nicely wrap the Metadata around the Art on the left"""
    def __init__(self, parent, config=None):
        super().__init__(parent, config=config)

        self += MetaDataFrame(self, config=FrameConfig(scalers=(0.6, 0.2), align=('right', 'middle')))
        self += MetaImages(self, key=MetadataKey.ALBUM, config=FrameConfig(scalers=(0.4, 1.0), align=('left', 'middle'), outline=OutlineStyle(colour='light', width=1)))


class TrackSpectrumScreen3(Frame):
    @property
    def title(self): return 'Full Spectrum Analyser, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='std'))

        spectrumframe = Frame(self, config=FrameConfig(scalers=(0.7, 1.0), align=('left', 'top')))
        
        spec_r = SpectrumStyle(barw_min=3, barsize_pc=0.5, bar_style=BarStyle(led_gap=0, flip=False, tip=True))
        spec_l = SpectrumStyle(barw_min=3, barsize_pc=0.5, bar_style=BarStyle(led_gap=0, tip=True, flip=True))
        
        spectrumframe += SpectrumFrame(spectrumframe, channel=Channel.RIGHT, config=FrameConfig(scalers=(1.0, 0.5), align=('centre', 'bottom')), visuals=spec_r)
        spectrumframe += SpectrumFrame(spectrumframe, channel=Channel.LEFT, config=FrameConfig(scalers=(1.0, 0.5), align=('centre', 'top')), visuals=spec_l)
        
        self += spectrumframe
        meta = self.add_rows(config=FrameConfig(scalers=(0.3, 1.0), align=('right', 'middle')))
        meta += MetaData(meta, key=MetadataKey.TRACK, visuals=TextStyle(colour='mid'))
        meta += MetaImages(meta, key=MetadataKey.ARTIST, visuals=ImageStyle(opacity=0.5))
        meta += MetaData(meta, key=MetadataKey.ARTIST, visuals=TextStyle(colour='dark'))


class TrackSpectrumScreen4(Frame):
    @property
    def title(self): return 'Spectrum Analyser 4, Artist & progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='ocean'))

        self += MetaImages(self, key=MetadataKey.ALBUM, config=FrameConfig(scalers=(1.0, 0.7), align=('right', 'middle'), outline=OutlineStyle(colour='light', width=1)), visuals=ImageStyle(opacity=1.0))
        self += PlayProgressFrame(self, config=FrameConfig(scalers=(0.9, 0.05), align=('centre', 'bottom')))

        spectrumframe = Frame(self, config=FrameConfig(scalers=(0.7, 0.8), align=('left', 'middle')))
        
        spec_r = SpectrumStyle(barw_min=15, barsize_pc=0.5, bar_style=BarStyle(flip=False, led_gap=5, peak_h=3, radius=0, tip=False))
        spec_l = SpectrumStyle(barw_min=15, barsize_pc=0.5, bar_style=BarStyle(flip=True, led_gap=5, peak_h=3, radius=0, tip=False))
        
        spectrumframe += SpectrumFrame(spectrumframe, channel=Channel.RIGHT, config=FrameConfig(scalers=(1.0, 0.5), align=('left', 'bottom')), visuals=spec_r)
        spectrumframe += SpectrumFrame(spectrumframe, channel=Channel.LEFT, config=FrameConfig(scalers=(1.0, 0.5), align=('left', 'top')), visuals=spec_l)
        
        self += MetaData(self, key=MetadataKey.TRACK, config=FrameConfig(scalers=(1.0, 0.2), align=('centre', 'top')))


class TrackVUMeterScreen(Frame):
    @property
    def title(self): return 'VU Meters, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='blue'))
        self += VUMeterImageFrame(self, type='blueVU', config=FrameConfig(scalers=(0.5, 0.5), align=('centre', 'middle'), outline=OutlineStyle(colour='light', width=1)))


class TrackVUMeterScreen21(Frame):
    @property
    def title(self): return 'Analogue VU Meters, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='meter1'))
  
        NEEDLE = VUNeedleStyle(colour='foreground', width=2, length=0.8, radius_pc=1.0)
        ENDSTOPS = (3 * PI / 4, 5 * PI / 4)
        PIVOT = -0.5
        OUTLINE = OutlineStyle(colour='light', width=2, opacity=0.8, radius=20)

        colframe = self.add_cols(config=FrameConfig(padding=0.01, scalers=(1.0, 1.0), align=('centre', 'top'), background=BackgroundStyle(colour='dark')))
        colframe += VUMeter(colframe, channel=Channel.LEFT, config=FrameConfig(scalers=(1.0, 1.0), outline=OUTLINE, background=BackgroundStyle(colour='dark')), visuals=VUMeterStyle(pivot=PIVOT, scale=VUMeterScale(arcs={}), endstops=ENDSTOPS, needle=NEEDLE))
        colframe += MetaDataFrame(colframe)
        self += VUMeter(self, channel=Channel.RIGHT, config=FrameConfig(scalers=(0.3, 1.0), outline=OUTLINE, background=BackgroundStyle(colour='dark')), visuals=VUMeterStyle(pivot=PIVOT, scale=VUMeterScale(arcs={}), endstops=ENDSTOPS, needle=NEEDLE))



class MinSpectrumArt(Frame):
    @property
    def title(self): return 'Base spectrum screen with al'
    @property
    def type(self): return 'Visualiser and metadata'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='std'))

        colframe = self.add_cols(config=FrameConfig())
        colframe += StereoSpectrumFrame(colframe)
        colframe += MetaDataFrame(colframe)
        colframe += MetaImages(colframe, key=MetadataKey.ARTIST)


class ArtMetaSpectrumScreen(Frame):
    @property
    def title(self): return 'Base spectrum screen with al'
    @property
    def type(self): return 'Visualiser and metadata'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='std'))

        self += MetaImages(self, key=MetadataKey.ALBUM, config=FrameConfig(scalers=(0.33, 1.0), align=('left', 'middle')))
        self += MetaDataFrame(self, config=FrameConfig(scalers=(0.67, 0.8), align=('right', 'top')))
        
        spec_style = SpectrumStyle(barw_min=1, barsize_pc=3, bar_style=BarStyle(flip=False, led_gap=0, peak_h=1, radius=0, tip=False, colour_mode='horz'))
        self += SpectrumFrame(self, channel=Channel.MONO, config=FrameConfig(scalers=(0.67, 0.2), align=('right', 'bottom')), visuals=spec_style)


class BigDialsScreen2(Frame):
    @property
    def title(self): return 'Lightback with 270 speedo dial type VU dial'
    @property
    def type(self): return 'Visualiser and metadata'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='space'))
        TICK_W = 4
        ARCLEN = 0.9
        NEEDLELEN = 0.9
        TICKLEN = 0.9        
        TICK_PC = 0.20         
        SCALESLEN = 1.05
        MARKS = {
            0.0: {'text': '0', 'width': TICK_W, 'colour': 'mid'},
            0.14: {'text': '1', 'width': TICK_W, 'colour': 'mid'},
            0.28: {'text': '2', 'width': TICK_W, 'colour': 'mid'},
            0.42: {'text': '3', 'width': TICK_W, 'colour': 'mid'},
            0.56: {'text': '4', 'width': TICK_W, 'colour': 'mid'},
            0.70: {'text': '5', 'width': TICK_W, 'colour': 'mid'},
            0.84: {'text': '6', 'width': TICK_W, 'colour': 'mid'},
            1.0: {'text': '7', 'width': TICK_W, 'colour': 'mid'}
        }
        ARCS = {ARCLEN: {'width': TICK_W // 3, 'colour': 'mid'}}
        ANNOTATE = {'Valign': 'bottom', 'text': '', 'colour': 'mid'}
        NEEDLE = VUNeedleStyle(width=4, colour='foreground', length=NEEDLELEN, radius_pc=1.0)
    
        vu_style = VUMeterStyle(pivot=0, endstops=(3 * PI / 8, 13 * PI / 8), needle=NEEDLE, scale=VUMeterScale(marks=MARKS, arcs=ARCS, annotate=ANNOTATE, tick_width=TICK_W, tick_length=TICKLEN, tick_radius_pc=TICK_PC, scale_radius=SCALESLEN), show_peak=True)
        self += VUMeter(self, channel=Channel.MONO, config=FrameConfig(scalers=(0.7, 0.7), align=('centre', 'middle')), visuals=vu_style)
        
        subframe = Frame(self, config=FrameConfig(scalers=(0.32, 0.95), align=('right', 'middle')))
        subframe2 = Frame(self, config=FrameConfig(scalers=(0.31, 0.55), align=('left', 'top')))
        
        self += MetaImages(subframe, key=MetadataKey.ALBUM, config=FrameConfig(align=('centre', 'middle'), outline=OutlineStyle(colour='light', width=5, opacity=0.8, radius=20)))
        self += MetaDataFrame(subframe2, config=FrameConfig(scalers=(0.9, 0.9), align=('centre', 'middle')))
        
        spec_style = SpectrumStyle(barw_min=3, barsize_pc=1, bar_style=BarStyle(flip=False, led_gap=5, peak_h=3, radius=4, tip=True))
        self += SpectrumFrame(self, channel=Channel.MONO, config=FrameConfig(scalers=(0.68, 0.7), align=('left', 'bottom')), visuals=spec_style)
        self += PlayProgressFrame(self, config=FrameConfig(scalers=(0.68, 0.05), align=('left', 'bottom')))