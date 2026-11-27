from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.components import Bar
from pyvisualiser import *
from pyvisualiser.styles.presets import *
from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.playprogress import *
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



class CircProgressScreen(Frame):
    @property
    def title(self): return 'Circular Playprogress bar'

    @property
    def type(self): return 'Test'


    def __init__(self, platform):
        # Use the new 'meter2' theme which has the cream background
        super().__init__(platform, config=FrameConfig(theme='ocean', padding=0))

        cols = ColFramer(self, ratios=(6,3,1), padpc=0.1)
        cols += PlayProgressFrame(cols, visuals=PlayProgressStyle(radius=30, format="auto", colour='foreground'))
        row = RowFramer(cols, ratios=(5,1))
        row += PlayProgressFrame(row, visuals=PlayProgressStyle(radius=30, format="auto", colour='mid'))
        row += PlayProgressFrame(row, visuals=PlayProgressStyle(radius=30, format="auto", colour='mid'))

        cols += PlayProgressFrame(cols, visuals=PlayProgressStyle(radius=30, format="auto", colour='alert'))


class ProgressScreenTest(Frame):

    @property
    def title(self):
        return 'Progress> checks the API for PlayProgressFrame'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        back = BackgroundStyle(colour= 'dark', colour_opacity=1.0)
        super().__init__(platform, config=FrameConfig(theme='std',  outline=OutlineStyle(width= 2, colour= 'alert'), padding=1))

        config=FrameConfig(outline=OutlineStyle(width= 1, colour= 'alert'), padding=1)

        rows = RowFramer(self, row_ratios=(1, 3), padpc=0.1 )
        rows += PlayProgressFrame(rows, visuals=PlayProgressStyle(radius=0, format="linear_ends"),config=config )

        cols = ColFramer(rows, ratios=(3,1), padpc=0.1)

        col1 = RowFramer(cols, ratios=(3,2,1))
        col1 += PlayProgressFrame(col1, visuals=PlayProgressStyle(radius=30, format="auto"),config=config)
        col1 += PlayProgressFrame(col1, visuals=PlayProgressStyle(radius=30, format="auto"),config=config)
        col1 += PlayProgressFrame(col1, visuals=PlayProgressStyle(radius=30, format="auto"),config=config)



        cols += PlayProgressFrame(cols, visuals=PlayProgressStyle(radius=30, format="circular"),config=config)
