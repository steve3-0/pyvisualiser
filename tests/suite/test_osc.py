from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.components import Bar
from pyvisualiser import *
from pyvisualiser.styles.presets import *
from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
from pyvisualiser.visualisers.oscillogramme import *
'\nHybrid Screens - these are top level frames comprising frames of frames at full display size\n'



class TestOscBarScreen(Frame):

    @property
    def title(self):
        return 'Test multiple configurations of Visualisers'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        back = BackgroundStyle(colour='dark')
        Frame.__init__(self, platform, config=FrameConfig(background=back))
        self += OscilogrammeBar(self, 'left', config=FrameConfig(scalers=(1.0, 0.5), align=('right', 'top')))
        self += OscilogrammeBar(self, 'right', config=FrameConfig(scalers=(1.0, 0.5), align=('right', 'bottom')), 
                                visuals=OscillogrammeStyle(bar_style=BarStyle(flip=True)))

class TestOscScreen(Frame):

    @property
    def title(self):
        return 'Test multiple configurations of Visualisers'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        back = BackgroundStyle(colour='background')
        Frame.__init__(self, platform, config=FrameConfig(background=back))
        self += Oscilogramme(self, 'left', config=FrameConfig(scalers=(1.0, 0.5), align=('right', 'top')))
        self += Oscilogramme(self, 'right', config=FrameConfig(scalers=(1.0, 0.5), align=('right', 'bottom')), 
                                                               visuals=OscillogrammeStyle(bar_style=BarStyle(flip=True)))


class TrackVisScreen3(Frame):
    @property
    def title(self): return 'Oscillograme Bar, Complex Visualiser, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='std'))

        subframe = self.add_rows(config=FrameConfig(scalers=(1.0, 1.0)))
        subframe += SamplesFrame(subframe, config=FrameConfig(scalers=(1.0, 1.0)))
        subframe += MetaData(subframe, key=MetadataKey.TRACK, config=FrameConfig(scalers=(1.0, 0.7)), visuals=TextStyle(colour='foreground'))
        subframe += MetaData(subframe, key=MetadataKey.ARTIST, config=FrameConfig(scalers=(1.0, 0.5)), visuals=TextStyle(colour='mid'))
        subframe += PlayProgressFrame(subframe, config=FrameConfig(scalers=(1.0, 0.3)))

class TrackOscScreen(Frame):
    @property
    def title(self): return 'Oscillogram, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='red'))
        self.create()

    def create(self):
        subframe = self.add_cols(config=FrameConfig(scalers=(1.0, 0.7), align=('right', 'top')))
        subframe += MetaDataFrame(subframe, config=FrameConfig(scalers=(1.0, 1.0)))
        subframe += MetaImages(subframe, key=MetadataKey.ALBUM, config=FrameConfig(scalers=(1.0, 1.0)), visuals=ImageStyle(opacity=100))
        subframe += VU2chFrame(subframe, config=FrameConfig(scalers=(0.1, 1.0), align=('right', 'middle'), outline=OutlineStyle(colour='foreground', width=1)), 
                               visuals=VUBarStyle(bar_style=BarStyle(led_h=7, led_gap=2, ),barsize_pc=0.1))
        self += Oscilogramme(self, channel=Channel.MONO, config=FrameConfig(scalers=(1.0, 0.3), align=('left', 'bottom')))

