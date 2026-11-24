# from pyvisualiser import Channel, ImageStyle, MetadataKey, ProgressStyle, TextStyle
from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.components import Bar
from pyvisualiser import *
from pyvisualiser.styles.presets import *
from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
from pyvisualiser.visualisers.oscillogramme import *

class ImageTestScreen(Frame):

    @property
    def title(self):
        return 'ArtTestScreen> aligns Album art and Artist Art'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', outline=OutlineStyle(colour='alert', width= 20), padding=2))
        rows = RowFramer(self, row_ratios=(1, 1), config=FrameConfig(padding=20))
        colframe = ColFramer(rows, col_ratios=(1, 1, 2), padpc=0, config=FrameConfig(background=BackgroundStyle(colour='mid',colour_opacity=0.5), padding=0, outline=OutlineStyle(colour= 'alert', width= 5)))
        colframe += MetaImages(colframe, key='album', visuals=ImageStyle(opacity=1.0, reflection=True), config=FrameConfig(outline=OutlineStyle(colour= 'alert', width= 1)))
        colframe += TextFrame(colframe, text='Test Art', 
                              config=FrameConfig(background=BackgroundStyle(colour='light'), outline=OutlineStyle(colour='alert', width= 2)))
        colframe += MetaImages(colframe, key='artist', visuals=ImageStyle(opacity=0.7, reflection=ReflectionStyle(size= 0.4, opacity= 0.3)), 
                               config=FrameConfig(outline=OutlineStyle(colour='alert', width= 1),background=None))#BackgroundStyle(colour='dark')))

class ReflectionTestScreen(Frame):

    @property
    def title(self):
        return 'Reflection Test Screen'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', background= BackgroundStyle(texture_path= 'particles.jpg', texture_opacity= 0.4)))
        cols = ColFramer(self, col_ratios=(1, 1, 1), config=FrameConfig(padding=20))
        col1 = RowFramer(cols, row_ratios=(5, 1))
        col1 += MetaImages(col1, key='album', visuals=ImageStyle(reflection=True), 
                           config=FrameConfig(outline=OutlineStyle(colour='light', width= 2), z_order=1))
        col1 += TextFrame(col1, text='Default', config=FrameConfig(background=BackgroundStyle('dark'), padding=10,align=('centre', 'middle')))
       
        col2 = RowFramer(cols, row_ratios=(5, 1))
        col2 += MetaImages(col2, key='artist', visuals=ImageStyle(reflection=ReflectionStyle(size= 0.5, opacity= 0.7)), 
                           config=FrameConfig(outline=OutlineStyle(colour='alert', width= 2), z_order=1))
        col2 += TextFrame(col2, text='Strong', config=FrameConfig(align=('centre', 'middle')))
        col3 = RowFramer(cols, row_ratios=(5, 1))
        col3 += MetaImages(col3, key='album', visuals=ImageStyle(reflection=ReflectionStyle(size= 0.2, opacity= 0.2)), 
                           config=FrameConfig(outline=OutlineStyle(colour='mid', width= 2), z_order=1))

class ArtistScreen(Frame):

    @property
    def title(self):
        return 'Artist art front and centre'

    @property
    def type(self):
        return 'Visualiser and metadata'

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(theme='zomp'))
        cols = ColFramer(self, config=FrameConfig(        background = BackgroundStyle(colour='background')))
        cols += MetaImages(cols, key='artist', config=FrameConfig(outline=None))
        cols += MetaDataFrame(cols)
        cols += VUFlipFrame(cols, visuals=VUBarStyle(bar_style=BarStyle(orient='vert')))

class ImageTestScreen2(Frame):

    @property
    def title(self):
        return 'Artist art front and centre'

    @property
    def type(self):
        return 'Visualiser and metadata'

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(theme='zomp'))
        cols = ColFramer(self, ratios=(4,3,2,2), padpc=0.1, config=FrameConfig(padding=10))
        cols += MetaImages(cols, key='album', config=FrameConfig(outline=OutlineStyle(width=2)))
        cols += MetaImages(cols, key='album', config=FrameConfig(outline=OutlineStyle(width=2)))
        cols += MetaImages(cols, key='album', config=FrameConfig(outline=OutlineStyle(width=2)))
        cols += MetaImages(cols, key='particles.jpg', config=FrameConfig(outline=OutlineStyle(width=2)))
     