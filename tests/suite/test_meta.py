from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.components import Bar
from pyvisualiser import *
from pyvisualiser.styles.presets import *
from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
from pyvisualiser.visualisers.oscillogramme import *

"""Text Based Frames """


class ArtistMetaDataFrame(Frame):

    def __init__(self, parent, config=None):
        super().__init__(parent, config=config)

        rows = RowFramer(self)
        rows += MetaImages(rows)
        rows += MetaDataFrame(rows)


class MetaMiniSpectrumFrame(Frame):

    def __init__(self, parent, config=None):
        super().__init__(parent, config=config)

        rowframe = RowFramer(self)
        rowframe += MetaDataFrame(rowframe)
        rowframe += SpectrumFrame(rowframe, 'mono', config=FrameConfig(scalers=(1.0, 0.3), align=('centre', 'bottom')), 
                                  visuals=SpectrumStyle( barsize_pc=2, barw_min=1, 
                                                        bar_style=BarStyle(flip=False, led_gap=0, peak_h=1, radius=0, tip=False, colour_mode='horz')))





class ProgressScreen(Frame):

    @property
    def title(self):
        return 'Progress> checks the API for PlayProgressFrame'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        back = BackgroundStyle(colour= 'mid', colour_opacity=1.0)
        super().__init__(platform, config=FrameConfig(theme='hifi',  outline=OutlineStyle(width= 2, colour= 'alert'), padding=10))

        rows = RowFramer(self, row_ratios=(1, 1), padpc=0.1, config=FrameConfig(background= BackgroundStyle(colour='mid'), padding=0, outline=OutlineStyle(colour= 'alert', width=1)))
        
        cols = ColFramer(rows, padpc=0.1,)
        cols += PlayProgressFrame(cols, config=FrameConfig(scalers=(1.0, 0.2), background=back), 
                                  visuals=PlayProgressStyle(bar_style=BarStyle(led_h=6, led_gap=3)))
        cols += PlayProgressFrame(cols, visuals=PlayProgressStyle(bar_style=BarStyle(radius=10, led_h=3, led_gap=3)))

        rows += PlayProgressFrame(rows, visuals=PlayProgressStyle(bar_style=BarStyle(radius=30, led_h=3, led_gap=3,orient='horz')))

class CircProgressScreen(Frame):
    @property
    def title(self): return 'Circular Playprogress bar'

    @property
    def type(self): return 'Test'


    def __init__(self, platform):
        # Use the new 'meter2' theme which has the cream background
        super().__init__(platform, config=FrameConfig(theme='ocean', padding=0))

        cols = ColFramer(self, padpc=0.1)
        cols += CircularProgress(cols,colour='foreground')
        cols += CircularProgress(cols,colour='mid')
        cols += CircularProgress(cols,colour='alert')