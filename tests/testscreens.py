from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.components import Bar
from pyvisualiser import *
from pyvisualiser.styles.presets import *
from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
from pyvisualiser.visualisers.oscillogramme import *
'\nHybrid Screens - these are top level frames comprising frames of frames at full display size\n'

class MixedLEDScreen(Frame):
    """ Volume/Source on left - Stereo Spectrum overlaid """

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(padding=50, background='dark', outline={'width': 2, 'colour': 'alert'}, theme='hifi'))
        cols = ColFramer(self, col_ratios=(4, 1), config=FrameConfig(background={'colour': 'dark', 'opacity': 20}, padding=0, outline={'width': 4, 'colour': 'mid'}))
        cols += SpectrumFrame(cols, 'mono', visuals=SpectrumStyle(barw_min=6, barsize_pc=0.2, bar_visuals=BarStyle(peak_h=2, led_gap=3, led_h=5)), theme='leds')
        cols += VU2chFrame(cols, orient='vert', flip=False, led_gap=3, led_h=5, background=None)
' Horizontal VU bar meter '


class ArtistMetaDataFrame(Frame):

    def __init__(self, parent, scalers=None, align=None, tip=False, theme=None, justify='centre'):
        super().__init__(parent, config=FrameConfig(scalers=scalers, align=align, theme=theme))
        self.justify = justify
        self.create()

    def create(self):
        rows = RowFramer(self)
        rows += MetaImages(rows)
        rows += MetaDataFrame(rows)

class MetaMiniSpectrumFrame(Frame):

    def __init__(self, parent, justify='centre', **kwargs):
        super().__init__(parent, **kwargs)
        self.justify = justify
        self.create()

    def create(self):
        rowframe = RowFramer(self)
        rowframe += MetaDataFrame(rowframe)
        rowframe += SpectrumFrame(rowframe, 'mono', config=FrameConfig(scalers=(1.0, 0.3), align=('centre', 'bottom')), visuals=SpectrumStyle(flip=False, led_gap=0, peak_h=1, radius=0, tip=False, barw_min=1, barsize_pc=2, col_mode='horz'))
'\nTest Code\n'

class TestVisualiserScreen(Frame):

    @property
    def title(self):
        return 'Test multiple configurations of Visualisers'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        back = {'colour': 'background'}
        Frame.__init__(self, platform, config=FrameConfig(background=back))
        self += OscilogrammeBar(self, 'left', config=FrameConfig(scalers=(1.0, 0.5), align=('right', 'top')))
        self += OscilogrammeBar(self, 'right', config=FrameConfig(scalers=(1.0, 0.5), align=('right', 'bottom'), bar_visuals=BarStyle(flip=True)))


class TrackVUMeterScreen2(Frame):

    @property
    def title(self):
        return 'Analogue VU Meters, Roon Album Art, Metadata and progress bar'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        back = {'image': 'artist', 'opacity': 100}
        Frame.__init__(self, platform, config=FrameConfig(background=back, theme='meter1', padding=30))
        NEEDLE = VUNeedleStyle(width=4, colour='foreground', length=0.8, radius_pc=1.0)
        ENDSTOPS = (3 * PI / 4, 5 * PI / 4)
        PIVOT = -0.5
        OUTLINE = {'colour': 'foreground', 'width': 5, 'opacity': 255, 'radius': 10}
        BACK = {'colour': 'background', 'opacity': 150}
        cols = ColFramer(self, config=FrameConfig(background={'colour': None, 'per_frame_update': True}))
        cols += VUMeter(cols, Channel.LEFT, visuals=VUMeterStyle(pivot=PIVOT, scale=VUMeterScale(arcs={}), endstops=ENDSTOPS, needle=NEEDLE), config=FrameConfig(square=False, outline=OUTLINE, background=BACK))
        cols += MetaDataFrame(cols, padding=2, background=BACK)
        cols += VUMeter(cols, Channel.RIGHT, visuals=VUMeterStyle(pivot=PIVOT, scale=VUMeterScale(arcs={}), endstops=ENDSTOPS, needle=NEEDLE), config=FrameConfig(square=False, outline=OUTLINE, background=BACK))

class ImageTestScreen(Frame):

    @property
    def title(self):
        return 'ArtTestScreen> aligns Album art and Artist Art'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', outline={'width': 20, 'colour': 'alert'}, padding=2))
        rows = RowFramer(self, row_ratios=(1, 1), config=FrameConfig(padding=20))
        colframe = ColFramer(rows, col_ratios=(1, 1, 2), padpc=0, config=FrameConfig(background='mid', padding=0, outline={'colour': 'alert', 'width': 5}))
        colframe += MetaImages(colframe, art_type='album', visuals=ImageStyle(opacity=255, reflection=True), config=FrameConfig(outline={'colour': 'alert', 'width': 1}))
        colframe += TextFrame(colframe, text='Test Art', background='light', outline={'colour': 'alert', 'width': 2})
        colframe += MetaImages(colframe, art_type='artist', visuals=ImageStyle(opacity=190, reflection={'size': 0.4, 'opacity': 0.3}), config=FrameConfig(outline={'colour': 'alert', 'width': 1}))

class ReflectionTestScreen(Frame):

    @property
    def title(self):
        return 'Reflection Test Screen'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', background={'image': 'particles.jpg', 'opacity': 100}))
        cols = ColFramer(self, col_ratios=(1, 1, 1), config=FrameConfig(padding=20))
        col1 = RowFramer(cols, row_ratios=(5, 1))
        col1 += MetaImages(col1, art_type='album', visuals=ImageStyle(reflection=True), config=FrameConfig(outline={'colour': 'light', 'width': 2}, z_order=1))
        col1 += TextFrame(col1, text='Default', align=('centre', 'middle'))
        col2 = RowFramer(cols, row_ratios=(5, 1))
        col2 += MetaImages(col2, art_type='artist', visuals=ImageStyle(reflection={'size': 0.5, 'opacity': 0.7}), config=FrameConfig(outline={'colour': 'alert', 'width': 2}, z_order=1))
        col2 += TextFrame(col2, text='Strong', align=('centre', 'middle'))
        col3 = RowFramer(cols, row_ratios=(5, 1))
        col3 += MetaImages(col3, art_type='album', visuals=ImageStyle(reflection={'size': 0.2, 'opacity': 0.2}), config=FrameConfig(outline={'colour': 'mid', 'width': 2}, z_order=1))
        col3 += TextFrame(col3, text='Subtle', align=('centre', 'middle'))


class ArtistScreen(Frame):

    @property
    def title(self):
        return 'Artist art front and centre'

    @property
    def type(self):
        return 'Visualiser and metadata'

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(theme='zomp'))
        cols = ColFramer(self, config=FrameConfig(background='dark'))
        cols += MetaImages(cols, art_type='album', config=FrameConfig(outline=None))
        cols += MetaDataFrame(cols, background='dark')
        cols += VUFlipFrame(cols, background='dark', orient='vert', outline=None)

class BloomImageTestScreen(Frame):

    @property
    def title(self):
        return 'Bloom Effect over Image Background'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(background={'image': 'particles.jpg', 'opacity': 255}))
        cols = ColFramer(self, col_ratios=(1, 2), config=FrameConfig(padding=20))
        cols += MetaImages(cols, art_type='album', visuals=ImageStyle(opacity=200), config=FrameConfig(outline={'colour': 'light', 'width': 2}))
        vu_bg = {'colour': 'dark', 'opacity': 100}
        cols += VU2chHorzFrame(cols, background=vu_bg, effects=Effects(threshold=0.5, scale=2.0, blur=0.8, alpha=80))

class ShadowTestScreen(Frame):

    @property
    def title(self):
        return 'Drop Shadow Test'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(background={'image': 'particles.jpg', 'opacity': 50}))
        cols = ColFramer(self, col_ratios=(1, 1, 1), config=FrameConfig(padding=40))
        shadow1 = {'color': (0, 0, 0), 'opacity': 255, 'offset': (15, 15), 'softness': 0.0}
        cols += TextFrame(cols, text='Hard Shadow', background={'colour': 'light', 'shadow': shadow1, 'opacity': 255}, outline={'colour': 'foreground', 'width': 2, 'radius': 10})
        shadow2 = {'color': (0, 0, 0), 'opacity': 200, 'offset': (20, 20), 'softness': 0.8}
        cols += TextFrame(cols, text='Soft Shadow', background={'colour': 'mid', 'shadow': shadow2, 'opacity': 255}, outline={'colour': 'foreground', 'width': 2, 'radius': 20})
        shadow3 = {'color': (255, 50, 50), 'opacity': 255, 'offset': (0, 0), 'softness': 0.9}
        cols += TextFrame(cols, text='Red Glow', background={'colour': 'dark', 'shadow': shadow3, 'opacity': 255}, outline={'colour': 'foreground', 'width': 2, 'radius': 30})

class ProgressScreen(Frame):

    @property
    def title(self):
        return 'Progress> checks the API for PlayProgressFrame'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        back = {'colour': 'background', 'opacity': 255}
        super().__init__(platform, config=FrameConfig(theme='hifi', outline={'width': 20, 'colour': 'alert'}, padding=0))
        cols = ColFramer(self)
        cols += PlayProgressFrame(cols, scalers=(1.0, 0.2), background=back)
        cols += MetaData(cols, key='track', scalers=(1.0, 1.0), outline={'colour': 'alert', 'width': 0}, visuals=TextStyle(colour='foreground'))
        rows = RowFramer(cols, row_ratios=(4, 1, 1), padpc=0, config=FrameConfig(background='mid', padding=0, outline={'colour': 'alert', 'width': 0}))
        rows += MetaData(rows, key='track', scalers=(1.0, 1.0), outline={'colour': 'alert', 'width': 0}, visuals=TextStyle(colour='foreground'))
        rows += PlayProgressFrame(rows, bar_visuals=BarStyle(led_h=3, led_gap=3))
        rows += PlayProgressFrame(rows, orient='horz')

class TestScreen(Frame):

    @property
    def title(self):
        return 'Tests out Frames, nesting and components'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform)
        subframe = Frame(self, scalers=(1.0, 0.5), align=('centre', 'top'))
        self += SubFrame(self, scalers=(0.5, 0.3), align=('left', 'top'))
        self += SubFrame(self, scalers=(0.5, 0.3), align=('right', 'bottom'))
        self += TestFrame(self, scalers=(1.0, 0.25), align=('centre', 'middle'))
        self += TestFrame(self, scalers=(0.5, 0.3), align=('left', 'bottom'), run=True)

class ColAlignedScreen(Frame):

    @property
    def title(self):
        return 'ColAlignedScreen> Creates 3 box frames and aligns them horizontally, evenly'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', outline={'width': 20, 'colour': 'alert'}, padding=0))
        self.create()

    def create(self):
        self += Frame(self, scalers=(0.5, 0.5), align=('left', 'middle'), background='light', outline={'colour': 'alert', 'width': 5})
        self += Frame(self, scalers=(0.5, 0.5), align=('right', 'bottom'), background='mid', outline={'colour': 'alert', 'width': 5})

class RowAlignedScreen(Frame):

    @property
    def title(self):
        return 'ColAlignedScreen> Creates 3 box frames and aligns them horizontally, evenly'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi'))
        out = OutlineStyle(width=10, colour='alert')
        rowframe = RowFramer(self, config=FrameConfig(scalers=(1.0, 1.0), padding=10, background=BackgroundStyle(colour='dark'), outline=out))
        rowframe += TextFrame(rowframe, text='left', scalers=(1.0, 1.0), background=BackgroundStyle(colour='light'), outline=out)
        rowframe += TextFrame(rowframe, text='mid on a very long string that needs to be even longer askjdhfkjahsdlfkjhalskjdhflkajshdflkjashdflkj', wrap=True, background=BackgroundStyle(colour='mid'), outline=out)
        rowframe += MetaData(rowframe, key='track', outline=out, visuals=TextStyle(colour='foreground'))

class F1(Frame):

    @property
    def title(self):
        return 'F1> Creates 3 box frames and aligns them horizontally, evenly'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', outline={'width': 10, 'colour': 'alert'}, padding=10, background={'image': 'stream.png', 'opacity': 255}))
        self.create()

    def create(self):
        self += Frame(self, scalers=(0.5, 0.5), align=('left', 'bottom'), background=BackgroundDefault, outline={'colour': 'foreground', 'width': 10})
        self += Frame(self, scalers=(0.5, 0.5), align=('right', 'bottom'), background=None, outline={'colour': 'foreground', 'width': 10})
        self += Frame(self, scalers=(0.5, 0.5), align=('left', 'top'), background=None, outline={'colour': 'foreground', 'width': 10})
        self += Frame(self, scalers=(0.5, 0.5), align=('right', 'top'), background=None, outline={'colour': 'foreground', 'width': 10})
        print(self)

class F2(Frame):

    @property
    def title(self):
        return 'F2> Creates 3 box frames and aligns them horizontally, evenly'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', outline={'width': 20, 'colour': 'alert'}, padding=20))
        self += Frame(self, scalers=(0.3, 0.3), align=('centre', 'bottom'), background='light', outline={'colour': 'foreground', 'width': 5})
        self += Frame(self, scalers=(0.3, 0.3), align=('right', 'bottom'), background='mid', outline={'colour': 'foreground', 'width': 5})
        self += Frame(self, scalers=(0.3, 0.3), align=('left', 'top'), background='light', outline={'colour': 'foreground', 'width': 5})
        self += Frame(self, scalers=(0.3, 0.3), align=('right', 'top'), background='mid', outline={'colour': 'foreground', 'width': 5})
        self += Frame(self, scalers=(0.3, 0.3), align=('left', 'middle'), background='light', outline={'colour': 'foreground', 'width': 5})
        self += Frame(self, scalers=(0.3, 0.3), align=('right', 'middle'), background='mid', outline={'colour': 'foreground', 'width': 5})

class F3(Frame):

    @property
    def title(self):
        return 'F3> Checks out Text Frames'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', outline={'width': 20, 'colour': 'foreground'}, padding=30))
        self += TextFrame(self, text='one', scalers=(0.33, 1.0), background='mid', align=('left', 'middle'), outline={'colour': 'alert', 'width': 10}, padding=10)
        self += TextFrame(self, text='two', scalers=(0.33, 1.0), background='mid', align=('centre', 'middle'), outline={'colour': 'alert', 'width': 10}, padding=10)
        self += TextFrame(self, text='three', scalers=(0.33, 1.0), background='mid', align=('right', 'middle'), outline={'colour': 'alert', 'width': 10}, padding=10)
        print(self)

class F4(Frame):

    @property
    def title(self):
        return 'F4> Checks out Col Framer'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', outline={'width': 5, 'colour': 'alert'}, background={'image': 'particles.jpg', 'opacity': 100}, padding=30))
        back = {'colour': 'dark', 'opacity': 100, 'glow': True}
        colframe = ColFramer(self, col_ratios=(1.0, 1.0, 1, 1), padpc=0.1, config=FrameConfig(align=('centre', 'middle'), background=None, padding=0, outline={'colour': 'alert', 'width': 0}))
        colframe += TextFrame(colframe, text='oneRT', background=back, justify=('right', 'top'), outline={'colour': 'foreground', 'width': 1}, padding=0)
        colframe += TextFrame(colframe, text='wideC', background='light', justify=('centre', 'middle'), outline={'colour': 'alert', 'width': 1})
        colframe += TextFrame(colframe, text='threeLB', background=back, justify=('left', 'bottom'), outline={'colour': 'mid', 'width': 1})
        rowframe = RowFramer(colframe, padpc=0.0, config=FrameConfig(align=('right', 'middle'), background=back, padding=0.0, outline={'colour': 'foreground', 'width': 1}))
        rowframe += TextFrame(rowframe, text='top', scalers=(1.0, 1.0), background='mid', outline={'colour': 'foreground', 'width': 0})
        rowframe += TextFrame(rowframe, text='rhs', background='dark', justify=('left', 'top'), outline={'colour': 'mid', 'width': 0})
        rowframe += TextFrame(rowframe, text='next', background='dark', justify=('centre', 'middle'), outline={'colour': 'mid', 'width': 0})
        rowframe += TextFrame(rowframe, text='b', scalers=(1.0, 1.0), justify=('right', 'bottom'), background='light')
        print(self)

class F5(Frame):

    @property
    def title(self):
        return 'F5 Checks background images'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', outline={'width': 0, 'colour': 'alert'}, padding=30, background={'image': 'particles.jpg', 'opacity': 100}))
        colframe = ColFramer(self, col_ratios=(1, 1, 2), config=FrameConfig(scalers=(1.0, 1.0), background=None, outline={'colour': 'foreground', 'width': 1}, padding=0))
        colframe += TextFrame(colframe, text='twoCM', scalers=(1.0, 1.0), align=('right', 'top'), justify=('centre', 'middle'), background='light', outline={'colour': 'alert', 'width': 1})
        colframe += VUFrame(colframe, 'left', align=('right', 'middle'), scalers=(1.0, 1.0), barsize_pc=1.0, bar_visuals=BarStyle(orient='horz', led_gap=0, tip=True), background='dark')
        rowframe = RowFramer(colframe, row_ratios=(1, 3, 1), config=FrameConfig(scalers=(1.0, 1.0), align=('right', 'middle'), background='dark', padding=0.0))
        rowframe += TextFrame(rowframe, text='row sub', scalers=(1.0, 1.0), background='light')
        colframe2 = ColFramer(rowframe, padpc=0, config=FrameConfig(scalers=(1.0, 1.0), align=('centre', 'middle'), background='mid', padding=0, outline={'colour': 'alert', 'width': 0}))
        colframe2 += TextFrame(colframe2, text='a', scalers=(1.0, 1.0), background='light')
        colframe2 += TextFrame(colframe2, text='two', scalers=(1.0, 1.0), background='dark', outline={'colour': 'mid', 'width': 30})
        colframe2 += TextFrame(colframe2, text='mleftj', wrap=True, background='mid', outline={'colour': 'alert', 'width': 1})
        rowframe += TextFrame(rowframe, text='five', scalers=(1.0, 0.5), align=('left', 'bottom'), background='dark', outline={'colour': 'mid', 'width': 2})
        print(self)

class F6(Frame):

    @property
    def title(self):
        return 'F5 Checks background images'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', outline={'width': 0, 'colour': 'alert'}, padding=10, background={'image': 'stream.png', 'opacity': 255}))
        self.create()

    def create(self):
        colframe = ColFramer(self, col_ratios=(1, 1, 1), config=FrameConfig(scalers=(1.0, 1.0), background=None, outline={'colour': 'foreground', 'width': 1}, padding=10))
        colframe += MetaDataFrame(colframe)
        colframe += VUFrame(colframe, 'left', align=('right', 'middle'), scalers=(1.0, 1.0), barsize_pc=1.0, bar_visuals=BarStyle(orient='vert', led_gap=0, tip=True), background='dark')
        print(self)

class F7(Frame):

    @property
    def title(self):
        return 'F7> Checks out Bars'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='std', outline={'width': 20, 'colour': 'foreground'}, padding=30, background={'image': 'stream.png', 'opacity': 255}))
        self.create()

    def create(self):
        col = ColFramer(self, col_ratios=(2, 1, 1), config=FrameConfig(background='dark'))
        col += VUFrame(col, 'left', align=('right', 'middle'), scalers=(1.0, 1.0), barsize_pc=1.0, bar_visuals=BarStyle(orient='horz', led_gap=0, tip=True), background='dark')
        print(self)

class F8(Frame):

    @property
    def title(self):
        return 'F8 > Check out Spectrum Analyser'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(theme='white', background='background'))
        cols = ColFramer(self, config=FrameConfig(background='background'))
        cols += SpectrumFrame(cols, 'mono', visuals=SpectrumStyle(barw_min=3, barsize_pc=2, bar_visuals=BarStyle(led_gap=0, peak_h=1, radius=0, tip=True)), background='background')
        artoutline = {'colour': 'background', 'width': 5}
        cols += MetaImages(cols, art_type='artist', visuals=ImageStyle(opacity=100), config=FrameConfig(outline=artoutline))
        cols += MetaDataFrame(cols)

class F9(Frame):

    @property
    def title(self):
        return 'Background layers test'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(theme='blue', background={'image': 'stream.png', 'opacity': 200}, padding=30))
        subframe = ColFramer(self, col_ratios=(1, 1, 1), padpc=0.1, config=FrameConfig(padding=40, background={'image': 'particles.jpg'}))
        subframe += VU2chFrame(subframe, bar_visuals=BarStyle(led_h=7, led_gap=2), barsize_pc=1.0, outline={'colour': 'foreground', 'width': 5}, background={'colour': 'mid', 'opacity': 100})
        subframe += MetaImages(subframe, art_type='album', visuals=ImageStyle(opacity=255))
        subframe += TextFrame(subframe, text='Volume', background={'colour': 'dark', 'opacity': 200}, justify=('right', 'middle'), outline={'colour': 'foreground', 'width': 1}, padding=0)