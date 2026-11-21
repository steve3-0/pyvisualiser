from pyvisualiser.core.components import Bar

from pyvisualiser import *
from pyvisualiser.styles.presets import *
from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
from pyvisualiser.visualisers.oscillogramme import *


"""
Hybrid Screens - these are top level frames comprising frames of frames at full display size
"""
class MixedLEDScreen(Frame):
    """ Volume/Source on left - Stereo Spectrum overlaid """
    def __init__(self, platform):
        Frame.__init__(self, platform, padding=50, background='dark', outline={'width':2,'colour':'alert'}, theme='hifi')
        cols = ColFramer(self, col_ratios=(4,1), background={'colour':'dark','opacity':20}, padding=0, outline={'width':4,'colour':'mid'})
        cols += SpectrumFrame(cols, 'mono', spectrum_style=SpectrumStyle(barw_min=6, barsize_pc=0.2, bar_style=BarStyle(peak_h=2, led_gap=3, led_h=5)), theme='leds')
        cols += VU2chFrame(cols, orient='vert', flip=False, led_gap=3, led_h=5, background=None)



""" Horizontal VU bar meter """
class VUScreen(Frame):   
    def __init__(self, platform):
        background={'image':'stream.png','opacity':150}
        Frame.__init__(self, platform)
        self += VU2chHorzFrame(self,
            bar_style=BarStyle(effects=BarEffects(threshold=0.6, scale=3.0, blur=0.9))
        )

class VUVScreen(Frame):   
    def __init__(self, platform):
        back = {'colour':'background'}
        Frame.__init__(self, platform, background=back)

        cols = ColFramer(self)
        rows = RowFramer(cols)
        rows += VU2chFrame(rows, orient='horz', flip=True)
        rows += VU2chFrame(rows, style=BarStyle(orient='horz', flip=False))
        row1 = RowFramer(cols)
        row1 += VU2chFrame(row1, orient='vert', flip=True, style=BarStyle(segment_size=5, segment_gap=4, corner_radius=4, edge_softness=0.05))
        row1 += VU2chFrame(row1, orient='vert', flip=False,style=BarStyle(segment_size=5, segment_gap=4, corner_radius=4, edge_softness=0.05))
        row2 = RowFramer(cols)
        row2 += VUFlipFrame(row2, orient='horz', flip=True,bar_style=BarStyle(led_h=5, led_gap=5),barsize_pc=0.7,intensity_threshold=0.6, intensity_scale=2.0, intensity_blur=0.7, intensity_alpha=80)
        row2 += VUFlipFrame(row2, orient='horz', flip=False,bar_style=BarStyle(led_h=5, led_gap=5),barsize_pc=0.7,intensity_threshold=0.6, intensity_scale=2.0, intensity_blur=0.7, intensity_alpha=80)
        row3 = RowFramer(cols)
        row3 += VUFlipFrame(row3, orient='vert', flip=True,led_h=5, style=BarStyle(segment_size=10, segment_gap=1, corner_radius=0, edge_softness=0.05))
        row3 += VUFlipFrame(row3, orient='vert', flip=False,led_h=5, style=BarStyle(segment_size=10, segment_gap=1, corner_radius=0, edge_softness=0.05))        


class ArtistMetaDataFrame(Frame):
    def __init__(self, parent, scalers=None, align=None,tip=False, theme=None, justify='centre'):
        super().__init__(parent, scalers=scalers, align=align, theme=theme)
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
        rowframe    = RowFramer(self)
        rowframe   += MetaDataFrame(rowframe, scalers=(1.0, 1.0), justify=self.justify)
        rowframe   += SpectrumFrame(rowframe, 'mono', scalers=(1.0, 0.3), align=('centre','bottom'), spectrum_style=SpectrumStyle(flip=False, led_gap=0, peak_h=1, radius=0, tip=False, barw_min=1, barsize_pc=2, col_mode='horz'))


"""
Test Code
"""


class TestVisualiserScreen(Frame):   
    @property
    def title(self): return 'Test multiple configurations of Visualisers'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        back = {'colour':'background'}
        Frame.__init__(self, platform,background=back)

        self += OscilogrammeBar(self  , 'left', scalers=(1.0,0.5), align=('right','top') )
        self += OscilogrammeBar(self  , 'right', scalers=(1.0,0.5), align=('right','bottom'), bar_style=BarStyle(flip=True))






class TestVUScreen(Frame):   
    @property
    def title(self): return 'Tests out Bar VU meters of all types'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        back = {'colour':'background'}
        Frame.__init__(self, platform, background=back)
        self += VU2chFrame(self,  scalers=(0.25, 1.0), align=('left','top'), style=BarStyle(orient='vert', flip=False))
        self += VUFlipFrame(self,  scalers=(0.25, 1.0), align=('right','bottom'), style=BarStyle(orient='vert', flip=True))
        self += VU2chHorzFrame(self,  frameconfig=FrameConfig(scalers=(0.5, 0.5), align=('centre','top')),tip=True)
        self += VUFlipFrame(self,  scalers=(0.5, 0.5), align=('centre','bottom'), style=BarStyle(orient='horz', flip=False))

class TrackVUMeterScreen2(Frame):   
    @property
    def title(self): return 'Analogue VU Meters, Roon Album Art, Metadata and progress bar'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        back = {'image':'artist', 'opacity': 100}
        Frame.__init__(self, platform, background=back, theme= 'meter1', padding=30)
  
        NEEDLE    = VUNeedleStyle(width=4, colour='foreground', length=0.8, radius_pc=1.0)
        ENDSTOPS  = (3*PI/4, 5*PI/4)  
        PIVOT     = -0.5
        OUTLINE   = {'colour':'foreground', 'width':5, 'opacity': 255, 'radius': 10}
        BACK      = {'colour':'background', 'opacity':150}
        
        cols = ColFramer(self, background={'colour':None,'per_frame_update':True})
        cols += VUMeter(cols, 'left', square=False, style=VUMeterStyle(pivot=PIVOT, scale=VUMeterScale(arcs={}), endstops=ENDSTOPS, needle=NEEDLE), outline=OUTLINE, background=BACK)
        cols += MetaDataFrame(cols, padding=2, background=BACK)
        cols += VUMeter(cols, 'right', square=False, style=VUMeterStyle(pivot=PIVOT, scale=VUMeterScale(arcs={}), endstops=ENDSTOPS, needle=NEEDLE), outline=OUTLINE, background=BACK)


#------------ Image Test screens --------------
class ImageTestScreen(Frame):
    @property
    def title(self): return 'ArtTestScreen> aligns Album art and Artist Art'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi', outline={'width':20,'colour':'alert'}, padding=2)

        rows = RowFramer(self, row_ratios=(1,1), padding=20)
        colframe = ColFramer(rows, col_ratios =(1,1,2), background='mid', padpc=0, padding=0, outline={'colour':'alert','width':5}) 

        colframe += MetaImages(colframe,  art_type='album',  opacity=255, outline={'colour':'alert','width':1}, reflection=True)
        colframe += TextFrame(colframe  , text='Test Art', background='light', outline={'colour':'alert','width':2})
        colframe += MetaImages(colframe,  art_type='artist',  opacity=190, outline={'colour':'alert','width':1},reflection={'size': 0.4, 'opacity': 0.3})

class ReflectionTestScreen(Frame):
    @property
    def title(self): return 'Reflection Test Screen'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi', background={'image': 'particles.jpg', 'opacity': 100})
        
        cols = ColFramer(self, col_ratios=(1, 1, 1), padding=20)
        
        col1 = RowFramer(cols, row_ratios=(5, 1))
        col1 += MetaImages(col1, art_type='album', reflection=True, outline={'colour':'light', 'width':2}, z_order=1)
        col1 += TextFrame(col1, text="Default", align=('centre', 'middle'))

        col2 = RowFramer(cols, row_ratios=(5, 1))
        col2 += MetaImages(col2, art_type='artist', reflection={'size': 0.5, 'opacity': 0.7}, outline={'colour':'alert', 'width':2}, z_order=1)
        col2 += TextFrame(col2, text="Strong", align=('centre', 'middle'))

        col3 = RowFramer(cols, row_ratios=(5, 1))
        col3 += MetaImages(col3, art_type='album', reflection={'size': 0.2, 'opacity': 0.2}, outline={'colour':'mid', 'width':2}, z_order=1)
        col3 += TextFrame(col3, text="Subtle", align=('centre', 'middle'))

class IntensityTestScreen(Frame):
    @property
    def title(self): return 'Intensity Test Screen'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi', background={'image': 'particles.jpg', 'opacity': 100})
        
        rows = RowFramer(self, padding=20, padpc=0.3)
        
        # 1. Default
        r1 = ColFramer(rows, col_ratios=(1, 3))
        r1 += TextFrame(r1, text="Default", align=('right', 'middle'))
        r1 += VU2chHorzFrame(r1)

        # 2. High Sensitivity (Threshold 0.1)
        r2 = ColFramer(rows, col_ratios=(1, 3))
        r2 += TextFrame(r2, text="High Sensitivity", align=('right', 'middle'))
        r2 += VU2chHorzFrame(r2, style=BarStyle(effects=BarEffects(threshold=0.1)))

        # 3. High Intensity (Scale 4.0, Alpha 100, Blur 100.0, Threshold 0.5)
        r3 = ColFramer(rows, col_ratios=(1, 3))
        r3 += TextFrame(r3, text="High Intensity", align=('right', 'middle'))
        r3 += VU2chHorzFrame(r3, style=BarStyle(effects=BarEffects(
            threshold=0.5, 
            scale=4.0, 
            alpha=100, 
            blur=100.0
        )))

        # 4. Sharp Glow (Threshold 0.5, Blur 10.0, Alpha 130)
        r4 = ColFramer(rows, col_ratios=(1, 3))
        r4 += TextFrame(r4, text="Sharp Glow", align=('right', 'middle'))
        r4 += VU2chHorzFrame(r4, style=BarStyle(effects=BarEffects(
            threshold=0.5, 
            blur=10.0, 
            alpha=130
        )))

class BarParametersTestScreen(Frame):
    @property
    def title(self): return 'Bar Parameters Test Screen'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi', background={'image': 'particles.jpg', 'opacity': 100})
        
        rows = RowFramer(self, row_ratios=(1, 1, 1, 1), padding=20)
        
        r1 = ColFramer(rows, col_ratios=(1, 3))
        r1 += TextFrame(r1, text="Default", align=('right', 'middle'))
        r1 += VU2chHorzFrame(r1)

        r2 = ColFramer(rows, col_ratios=(1, 3))
        r2 += TextFrame(r2, text="Blocky (Retro)", align=('right', 'middle'))
        r2 += VU2chHorzFrame(r2, style=BarStyle(segment_size=15, segment_gap=2, corner_radius=0, edge_softness=0.0))

        r3 = ColFramer(rows, col_ratios=(1, 3))
        r3 += TextFrame(r3, text="Round & Soft", align=('right', 'middle'))
        r3 += VU2chHorzFrame(r3, style=BarStyle(segment_size=8, segment_gap=4, corner_radius=4, edge_softness=0.1))

        r4 = ColFramer(rows, col_ratios=(1, 3))
        r4 += TextFrame(r4, text="Solid (Analog)", align=('right', 'middle'))
        r4 += VU2chHorzFrame(r4, style=BarStyle(segment_size=10, segment_gap=0, corner_radius=5, edge_softness=0.02))

class ArtistScreen(Frame):   
    @property
    def title(self): return 'Artist art front and centre'
    @property
    def type(self): return 'Visualiser and metadata'

    def __init__(self, platform):
        Frame.__init__(self, platform, theme= 'zomp')
        cols = ColFramer(self, background='dark')
        cols += MetaImages(cols, art_type='album', outline=None)
        cols += MetaDataFrame(cols, background='dark')
        cols += VUFlipFrame(cols, background='dark',orient='vert',outline=None)

class BloomImageTestScreen(Frame):
    @property
    def title(self): return 'Bloom Effect over Image Background'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, background={'image': 'particles.jpg', 'opacity': 255})
        cols = ColFramer(self, col_ratios=(1, 2), padding=20)
        cols += MetaImages(cols, art_type='album', opacity=200, outline={'colour':'light', 'width':2})
        vu_bg = {'colour': 'dark', 'opacity': 100} 
        cols += VU2chHorzFrame(cols, 
            background=vu_bg,
            effects=Effects(threshold=0.5, scale=2.0, blur=0.8, alpha=80)
        )

class ShadowTestScreen(Frame):
    @property
    def title(self): return 'Drop Shadow Test'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, background={'image': 'particles.jpg', 'opacity': 50})
        cols = ColFramer(self, col_ratios=(1, 1, 1), padding=40)
        
        shadow1 = {'color': (0, 0, 0), 'opacity': 255, 'offset': (15, 15), 'softness': 0.0}
        cols += TextFrame(cols, text="Hard Shadow", 
                          background={'colour': 'light', 'shadow': shadow1, 'opacity': 255},
                          outline={'colour': 'foreground', 'width': 2, 'radius': 10})

        shadow2 = {'color': (0, 0, 0), 'opacity': 200, 'offset': (20, 20), 'softness': 0.8}
        cols += TextFrame(cols, text="Soft Shadow", 
                          background={'colour': 'mid', 'shadow': shadow2, 'opacity': 255},
                          outline={'colour': 'foreground', 'width': 2, 'radius': 20})

        shadow3 = {'color': (255, 50, 50), 'opacity': 255, 'offset': (0, 0), 'softness': 0.9}
        cols += TextFrame(cols, text="Red Glow", 
                          background={'colour': 'dark', 'shadow': shadow3, 'opacity': 255},
                          outline={'colour': 'foreground', 'width': 2, 'radius': 30})

class ProgressScreen(Frame):
    @property
    def title(self): return 'Progress> checks the API for PlayProgressFrame'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        back = {'colour':'background', 'opacity':255}
        super().__init__(platform, theme='hifi', outline={'width':20,'colour':'alert'}, padding=0)

        cols = ColFramer(self)
        cols += PlayProgressFrame(cols, scalers=(1.0,0.2), background=back)
        cols += MetaData(cols,  'track', colour='foreground', scalers=(1.0,1.0), outline={'colour':'alert','width':0})
        rows = RowFramer(cols, row_ratios=(4,1,1),background='mid', padpc=0, padding=0, outline={'colour':'alert','width':0})

        rows += MetaData(rows,  'track', colour='foreground', scalers=(1.0,1.0), outline={'colour':'alert','width':0})
        rows += PlayProgressFrame(rows, bar_style=BarStyle(led_h=3, led_gap=3))
        rows += PlayProgressFrame(rows, orient='horz')


class TestScreen(Frame):
    @property
    def title(self): return 'Tests out Frames, nesting and components'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform)
        subframe = Frame(self, scalers=(1.0,0.5), align=('centre','top'))
        self += SubFrame(self  , scalers=(0.5,0.3), align=('left','top'))
        self += SubFrame(self  , scalers=(0.5,0.3), align=('right','bottom'))
        self += TestFrame(self, scalers=(1.0, 0.25), align=('centre','middle'))
        self += TestFrame(self, scalers=(0.5, 0.3), align=('left','bottom'), run=True)


class ColAlignedScreen(Frame):
    @property
    def title(self): return 'ColAlignedScreen> Creates 3 box frames and aligns them horizontally, evenly'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi', outline={'width':20,'colour':'alert'}, padding=0)
        self.create()

    def create(self):
        self += Frame(self, scalers=(0.5,0.5), align=('left','middle'), background='light', outline={'colour':'alert','width':5})
        self += Frame(self, scalers=(0.5,0.5), align=('right','bottom'), background='mid', outline={'colour':'alert','width':5})


class RowAlignedScreen(Frame):
    @property
    def title(self): return 'ColAlignedScreen> Creates 3 box frames and aligns them horizontally, evenly'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi' )
        out = OutlineStyle(width=10,colour='alert')
        rowframe = RowFramer(self, scalers=(1.0,1.0), padding=10, background=BackgroundStyle(colour='dark'),outline=out  )
        rowframe += TextFrame(rowframe  , text='left', scalers=(1.0, 1.0), background=BackgroundStyle(colour='light'), outline=out)
        rowframe += TextFrame(rowframe  , text='mid on a very long string that needs to be even longer askjdhfkjahsdlfkjhalskjdhflkajshdflkjashdflkj', wrap=True, background=BackgroundStyle(colour='mid'), outline=out)
        rowframe += MetaData(rowframe,  'track', colour='foreground', outline=out)


class F1(Frame):
    @property
    def title(self): return 'F1> Creates 3 box frames and aligns them horizontally, evenly'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi', outline={'width':10,'colour':'alert'}, padding=10, background={'image': 'stream.png', 'opacity': 255})
        self.create()

    def create(self):
        self += Frame(self, scalers=(0.5,0.5), align=('left','bottom'), background=BackgroundDefault, outline={'colour':'foreground','width':10})
        self += Frame(self, scalers=(0.5,0.5), align=('right','bottom'), background=None, outline={'colour':'foreground','width':10})
        self += Frame(self, scalers=(0.5,0.5), align=('left','top'), background=None, outline={'colour':'foreground','width':10})
        self += Frame(self, scalers=(0.5,0.5), align=('right','top'), background=None, outline={'colour':'foreground','width':10})
        print(self)


class F2(Frame):
    @property
    def title(self): return 'F2> Creates 3 box frames and aligns them horizontally, evenly'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi', outline={'width':20,'colour':'alert'}, padding=20)
        self += Frame(self, scalers=(0.3,0.3), align=('centre','bottom'), background='light', outline={'colour':'foreground','width':5})
        self += Frame(self, scalers=(0.3,0.3), align=('right','bottom'), background='mid', outline={'colour':'foreground','width':5})
        self += Frame(self, scalers=(0.3,0.3), align=('left','top'), background='light', outline={'colour':'foreground','width':5})
        self += Frame(self, scalers=(0.3,0.3), align=('right','top'), background='mid', outline={'colour':'foreground','width':5})
        self += Frame(self, scalers=(0.3,0.3), align=('left','middle'), background='light', outline={'colour':'foreground','width':5})
        self += Frame(self, scalers=(0.3,0.3), align=('right','middle'), background='mid', outline={'colour':'foreground','width':5})


class F3(Frame):
    @property
    def title(self): return 'F3> Checks out Text Frames'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi', outline={'width':20,'colour':'foreground'}, padding=30)
        self += TextFrame(self  , text='one', scalers=(0.33,1.0 ), background='mid', align=('left','middle'), outline={'colour':'alert','width':10}, padding =10)
        self += TextFrame(self  , text='two', scalers=(0.33, 1.0), background='mid', align=('centre','middle'), outline={'colour':'alert','width':10}, padding =10)
        self += TextFrame(self  , text='three', scalers=(0.33, 1.0), background='mid', align=('right','middle'), outline={'colour':'alert','width':10}, padding =10)
        print(self)


class F4(Frame):
    @property
    def title(self): return 'F4> Checks out Col Framer'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi', outline={'width':5,'colour':'alert'}, background={'image': 'particles.jpg', 'opacity': 100}, padding=30)
        
        back = {'colour':'dark', 'opacity':100, 'glow':True}
        colframe = ColFramer(self,col_ratios=(1.0,1.0,1,1), align=('centre','middle'), background=None, padpc=0.1, padding=0, outline={'colour':'alert','width':0}) 
        colframe += TextFrame(colframe  , text='oneRT',  background=back, justify=('right','top'), outline={'colour':'foreground','width':1}, padding =0)
        colframe += TextFrame(colframe  , text='wideC',  background='light', justify=('centre','middle'), outline={'colour':'alert','width':1})
        colframe += TextFrame(colframe  , text='threeLB',  background=back, justify=('left','bottom'), outline={'colour':'mid','width':1})

        rowframe = RowFramer(colframe  , padpc=0.0, align=('right','middle'), background=back, padding=0.0, outline={'colour':'foreground','width':1})
        rowframe += TextFrame(rowframe  , text="top",  scalers=(1.0,1.0), background='mid', outline={'colour':'foreground','width':0})
        rowframe += TextFrame(rowframe  , text='rhs', background='dark', justify=('left','top'),outline={'colour':'mid', 'width':0})
        rowframe += TextFrame(rowframe  , text='next', background='dark', justify=('centre','middle'),outline={'colour':'mid', 'width':0})
        rowframe += TextFrame(rowframe  ,  text='b', scalers=(1.0, 1.0), justify=('right','bottom'),background='light')
        print(self)


class F5(Frame):
    @property
    def title(self): return 'F5 Checks background images'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi', outline={'width':0,'colour':'alert'}, padding=30, background={'image': 'particles.jpg', 'opacity': 100} )
        
        colframe = ColFramer(self, col_ratios=(1,1,2), scalers=(1.0,1.0), background=None, outline={'colour':'foreground','width':1}, padding=0)
        colframe += TextFrame(colframe  , text='twoCM', scalers=(1.0,1.0), align=('right','top'), justify=('centre', 'middle'), background='light', outline={'colour':'alert','width':1})
        colframe += VUFrame(colframe, 'left', align=('right','middle'), scalers=(1.0,1.0), barsize_pc=1.0, bar_style=BarStyle(orient='horz', led_gap=0, tip=True), background='dark')
        
        rowframe = RowFramer(colframe  , row_ratios=(1,3, 1),  scalers=(1.0,1.0), align=('right','middle'), background='dark', padding=0.0)
        rowframe += TextFrame(rowframe  , text='row sub', scalers=(1.0, 1.0), background='light') 
        colframe2 = ColFramer(rowframe, scalers=(1.0,1.0), align=('centre','middle'), background='mid', padpc=0, padding=0, outline={'colour':'alert','width':0}) 
        colframe2 += TextFrame(colframe2  , text='a', scalers=(1.0, 1.0), background='light') 
        colframe2 += TextFrame(colframe2  , text='two', scalers=(1.0, 1.0), background='dark', outline={'colour':'mid','width':30})
        colframe2 += TextFrame(colframe2  , text='mleftj', wrap=True, background='mid', outline={'colour':'alert','width':1})
        rowframe += TextFrame(rowframe  , text='five', scalers=(1.0, 0.5), align=('left','bottom'), background='dark', outline={'colour':'mid','width':2})
        print(self)        


class F6(Frame):
    @property
    def title(self): return 'F5 Checks background images'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi', outline={'width':0,'colour':'alert'}, padding=10, background={'image': 'stream.png', 'opacity': 255} )
        self.create()

    def create(self):
        colframe = ColFramer(self, col_ratios=(1,1,1), scalers=(1.0,1.0), background=None, outline={'colour':'foreground','width':1}, padding=10)
        colframe += MetaDataFrame(colframe)
        colframe += VUFrame(colframe, 'left', align=('right','middle'), scalers=(1.0,1.0), barsize_pc=1.0, bar_style=BarStyle(orient='vert', led_gap=0, tip=True), background='dark')
        print(self)  


class F7(Frame):
    @property
    def title(self): return 'F7> Checks out Bars'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='std', outline={'width':20,'colour':'foreground'}, padding=30, background={'image': 'stream.png', 'opacity': 255})
        self.create()

    def create(self):
        col = ColFramer(self,col_ratios=(2,1,1), background='dark')
        col += VUFrame(col, 'left', align=('right','middle'), scalers=(1.0,1.0), barsize_pc=1.0, bar_style=BarStyle(orient='horz', led_gap=0, tip=True), background='dark')
        print(self)  


class F8(Frame):   
    @property
    def title(self): return 'F8 > Check out Spectrum Analyser'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, theme= 'white', background='background')

        cols = ColFramer(self, background='background')
        
        # Migrated bar properties inside SpectrumStyle here as well
        cols += SpectrumFrame(cols, 'mono', spectrum_style=SpectrumStyle(barw_min=3, barsize_pc=2, bar_style=BarStyle(led_gap=0, peak_h=1, radius=0, tip=True)), background='background')
        
        artoutline = {'colour':'background', 'width':5}
        cols += MetaImages(cols  , art_type='artist', opacity=100, outline=artoutline)
        cols += MetaDataFrame(cols )


class F9(Frame):   
    @property
    def title(self): return 'Background layers test'
    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, theme= 'blue', background={'image':'stream.png', 'opacity':200},padding=30)

        subframe = ColFramer(self, col_ratios=(1,1,1), padpc=0.1,padding=40, background={'image':'particles.jpg'})
        subframe += VU2chFrame(subframe, bar_style=BarStyle(led_h=7, led_gap=2),barsize_pc=1.0, outline={'colour':'foreground', 'width':5},\
                               background={'colour':'mid','opacity':100})
        subframe += MetaImages(subframe, art_type='album', opacity=255)
        subframe += TextFrame(subframe  , text='Volume',  background={'colour':'dark','opacity':200}, \
                              justify=('right','middle'), outline={'colour':'foreground','width':1}, padding =0)