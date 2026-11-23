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



class ShadowTestScreen(Frame):

    @property
    def title(self):
        return 'Drop Shadow Test'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(background=BackgroundStyle(texture_path='particles.jpg', texture_opacity=0.2)))
        cols = self.add_cols(ratios=(1, 1, 1), padpc=0.2, config=FrameConfig(padding=40))

        # 1. Hard Offset Drop Shadow
        s1 = ShadowStyle(colour=(0, 0, 0), opacity=1.0, offset=(15, 15), softness=0.0)
        out1 = OutlineStyle(colour='foreground', width=2, radius=10)
        bg1 = BackgroundStyle(colour='light', colour_opacity=1.0, shadow=s1)
        cols += TextFrame(
            cols,
            text='Hard Shadow',
            config=FrameConfig(outline=out1, background=bg1),
            visuals=TextStyle(colour='dark', justify=('centre', 'middle'))
        )

        # 2. Soft Offset Drop Shadow
        s2 = ShadowStyle(colour=(0, 0, 0), opacity=0.8, offset=(20, 20), softness=0.8)
        out2 = OutlineStyle(colour='foreground', width=2, radius=20)
        bg2 = BackgroundStyle(colour='mid', colour_opacity=1.0, shadow=s2)
        cols += TextFrame(
            cols,
            text='Soft Shadow',
            config=FrameConfig(outline=out2, background=bg2),
            visuals=TextStyle(colour='foreground', justify=('centre', 'middle'))
        )

        # 3. Centered Red Glow (Offset 0, 0)
        s3 = ShadowStyle(colour=(255, 50, 50), opacity=1.0, offset=(0, 0), softness=0.9)
        out3 = OutlineStyle(colour='foreground', width=2, radius=30)
        bg3 = BackgroundStyle(colour='dark', colour_opacity=1.0, shadow=s3)
        cols += TextFrame(
            cols,
            text='Red Glow',
            config=FrameConfig(outline=out3, background=bg3),
            visuals=TextStyle(colour='light', justify=('centre', 'middle'))
        )

class ProgressScreen(Frame):

    @property
    def title(self):
        return 'Progress> checks the API for PlayProgressFrame'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        back = BackgroundStyle(colour= 'background', colour_opacity=1.0)
        super().__init__(platform, config=FrameConfig(theme='hifi', outline=OutlineStyle(width= 20, colour= 'alert'), padding=0))
        cols = ColFramer(self)
        cols += PlayProgressFrame(cols, config=FrameConfig(scalers=(1.0, 0.2), background=back))
        cols += MetaData(cols, key='track', config=FrameConfig(scalers=(1.0, 1.0), outline=OutlineStyle(width= 20, colour= 'alert')), 
                                                               visuals=TextStyle(colour='foreground'))
 
        rows = RowFramer(cols, row_ratios=(4, 1, 1), padpc=0, config=FrameConfig(background= BackgroundStyle(colour='mid'), padding=0, outline=OutlineStyle(colour= 'alert', width=1)))
        rows += MetaData(rows, key='track', config=FrameConfig(scalers=(1.0, 1.0), outline=OutlineStyle(width= 1, colour= 'alert')),
                          visuals=TextStyle(colour='foreground'))
        rows += PlayProgressFrame(rows, visuals=PlayProgressStyle(bar_style=BarStyle(led_h=3, led_gap=3)))
        rows += PlayProgressFrame(rows, visuals=PlayProgressStyle(bar_style=BarStyle(led_h=3, led_gap=3,orient='horz')))
