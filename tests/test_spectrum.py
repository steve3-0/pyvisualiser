"""
Test Screens for Spectrum Analyser Frames

"""
# from pyvisualiser import *
from pyvisualiser.styles.presets import *
# from pyvisualiser.visualisers.vumeters import *
# from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
# from pyvisualiser.visualisers.oscillogramme import *



"""
Spectrum Analyser Frames - variants on
    1. Full frame - mono
    2. Horz Split screen
    3. Horz Split screen - right flipped
    4. Vert split - L/R
    5. Full frame, right channel offset

    SpectrumFrame API:
    # def __init__(self, parent, channel, scale, align=('left','bottom'), right_offset=0, theme='std', flip=False, \
    #                 led_h=5, led_gap=1, peak_h=1, radius=0, barsize_pc=0.5, barw_min=12, barw_max=20, tip=False, decay=DECAY):
"""


        

class SpectrumStereoFrame(Frame): #""" Horz Split screen - right flipped 'Apple Style' """
    # THis is vertically aligned, with one flipped
    def __init__(self, parent, scalers=None, align=None, config=None) :
        Frame.__init__(self, parent, scalers=scalers, align=align, config=config)

        bar = BarStyle(flip=False, led_gap=2, peak_h=0, radius=2,colour_mode='vert')
        col = ColFramer(self)

        col += SpectrumFrame(col, 'left',  config=FrameConfig(theme='rainbow', background=None),
                              visuals=SpectrumStyle(barw_min=10, barsize_pc=0.4,flip=True, bar_style=bar) )
        col += SpectrumFrame(col, 'right', config=FrameConfig(theme='rainbow', background=None),
                               visuals=SpectrumStyle(barw_min=10, barsize_pc=0.4, bar_style=bar)  )        

class SpectrumStereoLRFrame(Frame): #""" Horz Split screen - LED Style right flipped  """
    # THis is vertically aligned, with one flipped
    def __init__(self, parent, scalers, align) :
        Frame.__init__(self, parent, scalers=scalers, align=align)
        bar=BarStyle(flip=True, led_gap=1, peak_h=1, radius=2)
        self += SpectrumFrame(self, 'right', config=FrameConfig(scalers=(1.0, 0.5), align=('left','top')    ), visuals=SpectrumStyle(barw_min=12, bar_style=bar), theme='white' )
        self += SpectrumFrame(self, 'left', config=FrameConfig(scalers=(1.0, 0.5), align=('left','bottom')) , visuals=SpectrumStyle(barw_min=12, bar_style=bar), theme='red' )
        

class SpectrumStereoSplitFrame(Frame): #""" Horz Split screen - right flipped """
    # This is vertically aligned
    def __init__(self, parent, scalers=None, align=None, config=None) :
        Frame.__init__(self, parent, config=config,scalers=scalers, align=align)
        rows = RowFramer(self)
        bar_style=BarStyle(led_gap=0, flip=False, tip=True)
        rows += SpectrumFrame(rows, 'right', config=FrameConfig(scalers=(1.0, 0.5), align=('left','top')    ), visuals=SpectrumStyle(barw_min=5, barsize_pc=0.5, bar_style=bar_style) )
        bar_style=BarStyle(led_gap=0, flip=True, tip=True)
        rows += SpectrumFrame(self, 'left', config=FrameConfig(scalers=(1.0, 0.5), align=('left','bottom')) ,  visuals=SpectrumStyle(barw_min=5, barsize_pc=0.5, bar_style=bar_style) )
        

class SpectrumStereoOffsetFrame(Frame):
    def __init__(self, parent, config=None,scalers=None, align=None) :
        Frame.__init__(self, parent, config=config, scalers=scalers, align=align)
        self += SpectrumFrame(self, 'right', config=FrameConfig(scalers=(1.0, 1.0), align=('left','top'), theme='red', background=None),   
                              visuals=SpectrumStyle(barw_min=8, barsize_pc=1.5, 
                                    bar_style=BarStyle(led_gap=0, tip=True,right_offset=2,),))
        self += SpectrumFrame(self, 'left', config=FrameConfig(scalers=(1.0, 1.0), align=('left','bottom'),theme='blue',background=None), 
                              visuals=SpectrumStyle(barw_min=8, barsize_pc=1.5, bar_style=BarStyle(led_gap=0, tip=True) )  )


class StereoSpectrumFrame(Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self += SpectrumFrame(self,  'right', config=FrameConfig(scalers=(1.0, 0.5), align=('left','top')), 
                              visuals=SpectrumStyle(barw_min=15, barsize_pc=0.5, 
                              bar_style=BarStyle(led_gap=5, peak_h=3, radius=0 )))
        self += SpectrumFrame(self,  'left', config=FrameConfig(scalers=(1.0, 0.5), align=('left','bottom')) , 
                              visuals=SpectrumStyle(barw_min=15, barsize_pc=0.5, 
                              bar_style=BarStyle(led_gap=5, peak_h=3, radius=0, flip=True)) )


""" Spectrum Analyser based Screens """

class Spectrum2chFrame(Frame): #""" Vert split - L/R """
    def __init__(self, parent, **kwargs) :
        Frame.__init__(self, parent, outline={'width':4,'colour':'light'}, **kwargs)

        rows = ColFramer(self, scalers=(0.7, 0.7), padding=10, outline={'width':4,'colour':'light'})
        rows += SpectrumFrame(rows, 'left'  )
        rows += SpectrumFrame(rows, 'right' )
class StereoSpectrumLRScreen(Frame):
    """ Volume/Source on left - Spectrum on left - one channel """
    def __init__(self, platform):
        Frame.__init__(self, platform, theme='hifi')
        self += Spectrum2chFrame(self, padding=30)


class FullSpectrumOffsetScreen(Frame):
    """ Volume/Source on left - Spectrum on left - one channel """
    def __init__(self, platform):
        Frame.__init__(self, platform, background=None)
        self += SpectrumStereoOffsetFrame(self  , scalers=(1.0,1.0), align=('centre','middle'))


class StereoSpectrumScreen(Frame):
    """ Volume/Source on left - Stereo Spectrum overlaid """
    def __init__(self, platform):
        Frame.__init__(self, platform)
        self += SpectrumStereoFrame(self  , scalers=(1.0,1.0), align=('centre','middle'))


class StereoSpectrumSplitScreen(Frame):
    """ Volume/Source on left - Stereo Spectrum overlaid """
    @property
    def title(self): return 'Full Spectrum Analyser, Roon Album Art, Metadata and progress bar'

    @property
    def type(self): return 'Test'
    
    def __init__(self, platform):
        Frame.__init__(self, platform)
        self += SpectrumStereoSplitFrame(self  , scalers=(1.0,1.0), align=('centre','middle'))


class MonoSpectrumScreen(Frame):
    """ Volume/Source on left - Stereo Spectrum overlaid """
    def __init__(self, platform):
        Frame.__init__(self, platform)
        self += SpectrumFrame(self  , 'left', scalers=(1.0, 1.0),  visuals=SpectrumStyle(barw_min=2, bar_style=BarStyle(led_gap=0, tip=True)))


class MonoSpectrumLEDScreen(Frame):
    """ Volume/Source on left - Stereo Spectrum overlaid """
    def __init__(self, platform):
        Frame.__init__(self, platform, outline={'width':5,'colour':'alert'}, theme='hifi', padding=30, background='background')
        col = ColFramer(self)
        col += SpectrumFrame(col, 'mono', 
                             visuals=SpectrumStyle(barw_min=6, barsize_pc=0.2, bar_style=BarStyle(peak_h=2, led_gap=3, led_h=4)), 
                             ballistics=FFTBallistics(attack_rate=0.9, decay_rate=0.05, peak_decay_rate=0.005, smoothing_factor=0.5) )



class TestSpectrumScreen(Frame):   
    @property
    def title(self): return 'Tests out multiple configurations of spectrum analysers'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, theme='leds')
        # 2 x 2 Cols, Rows
        cols = ColFramer(self, col_ratios=(1, 1), padding=10)
        row1 = RowFramer(cols, row_ratios=(1, 1), padding=10)
        row2 = RowFramer(cols, row_ratios=(1, 1), padding=10)

        row1 += SpectrumStereoSplitFrame(row1)
        row1 += SpectrumStereoOffsetFrame(row1)
        
        # Migrated bar_style parameters into SpectrumStyle
        row2 += MonoSpectrumScreen(row2)
        row2 += SpectrumStereoFrame(row2)