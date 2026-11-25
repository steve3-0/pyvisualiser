from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.components import Bar
from pyvisualiser import *
from pyvisualiser.styles.presets import *
from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
from pyvisualiser.visualisers.oscillogramme import *


class VUScreen(Frame):

    def __init__(self, platform):
        Frame.__init__(self, platform)
        cols=ColFramer(self,padpc=0.1)
        vubar_style=VUBarStyle(barsize_pc=0.2,  bar_style= BarStyle(colour_mode='vert', effects=BarEffects(threshold=0.6, scale=3.0, blur=0.9)))
        cols += VUFrame(cols, 'left', config=FrameConfig(align=('centre','middle')),
                        visuals=vubar_style)
        cols += VUFrame(cols, 'right', config=FrameConfig(align=('centre','middle')),
                        visuals=None)

class VU2Screen(Frame):

    def __init__(self, platform):
        background = BackgroundStyle(texture_path= 'particles.jpg', texture_opacity= 0.7)
        Frame.__init__(self, platform, config=FrameConfig(background=background))
        self += VU2chHorzFrame(self, visuals=VUBarStyle(barsize_pc=0.7, 
                                                        bar_style=BarStyle(effects=BarEffects(threshold=0.6, scale=1.0, blur=0.9))))

class VUVScreen(Frame):

    def __init__(self, platform):
        back = BackgroundStyle(colour= 'background')
        Frame.__init__(self, platform, config=FrameConfig(background=back))
        cols = ColFramer(self)
        rows = RowFramer(cols)
        rows += VU2chFrame(rows, visuals=VUBarStyle(bar_style=BarStyle(orient='horz', flip=True)))
        rows += VU2chFrame(rows, visuals=VUBarStyle(barsize_pc=0.3, 
                                                        bar_style=BarStyle(orient='horz', flip=False)))
        row1 = RowFramer(cols)
        row1 += VU2chFrame(row1, visuals=VUBarStyle(barsize_pc=0.3, 
                                                        bar_style=BarStyle(orient='vert', flip=True, segment_size=5, segment_gap=4, corner_radius=4, edge_softness=0.05)))
        row1 += VU2chFrame(row1,  visuals=VUBarStyle(barsize_pc=0.3, 
                                                        bar_style=BarStyle(orient='vert', flip=False,segment_size=5, segment_gap=4, corner_radius=4, edge_softness=0.05)))
        row2 = RowFramer(cols)
        row2 += VUFlipFrame(row2, visuals=VUBarStyle(barsize_pc=0.7, 
                                                        bar_style=BarStyle(orient='horz', flip=True, led_h=5, led_gap=5,  
                                                   effects=BarEffects(threshold=0.6, scale=2.0, blur=0.7, alpha=80))))
        row2 += VUFlipFrame(row2,  visuals=VUBarStyle(barsize_pc=0.7, 
                                                        bar_style=BarStyle(orient='horz', flip=False,led_h=5, led_gap=5, 
                                                    effects=BarEffects(threshold=0.6, scale=2.0, blur=0.7, alpha=80))))
        row3 = RowFramer(cols)
        row3 += VUFlipFrame(row3, visuals=VUBarStyle(barsize_pc=0.3, 
                                                        bar_style=BarStyle(orient='vert', flip=True, led_h=5, segment_size=10, segment_gap=1, corner_radius=0, edge_softness=0.05)))
        row3 += VUFlipFrame(row3, visuals=VUBarStyle(barsize_pc=0.3, 
                                                        bar_style=BarStyle(orient='vert', flip=False, led_h=5, segment_size=10, segment_gap=1, corner_radius=0, edge_softness=0.05)))


class TestVUScreen(Frame):

    @property
    def title(self):
        return 'Tests out Bar VU meters of all types'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        back = BackgroundStyle(colour= 'background')
        Frame.__init__(self, platform, config=FrameConfig(background=back))
        self += VU2chFrame(self, config=FrameConfig(scalers=(0.25, 1.0), align=('left', 'top')), visuals=VUBarStyle(bar_style=BarStyle(orient='vert', flip=False)))
        self += VUFlipFrame(self, config=FrameConfig(scalers=(0.25, 1.0), align=('right', 'bottom')), visuals=VUBarStyle(bar_style=BarStyle(orient='vert', flip=True)))
        self += VU2chHorzFrame(self, config=FrameConfig(scalers=(0.5, 0.5), align=('centre', 'top')), tip=True)
        self += VUFlipFrame(self, config=FrameConfig(scalers=(0.5, 0.5), align=('centre', 'bottom')), visuals=VUBarStyle(bar_style=BarStyle(orient='horz', flip=False)))

class IntensityTestScreen(Frame):

    @property
    def title(self):
        return 'Intensity Test Screen'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', background=BackgroundStyle(texture_path='particles.jpg', texture_opacity= 0.3)))
        rows = RowFramer(self, padpc=0.3, config=FrameConfig(padding=20))
        r1 = ColFramer(rows, col_ratios=(1, 3))
        r1 += TextFrame(r1, text='Default', config=FrameConfig(align=('right', 'middle')))
        r1 += VU2chHorzFrame(r1)
        r2 = ColFramer(rows, col_ratios=(1, 3))
        r2 += TextFrame(r2, text='High Sensitivity', config=FrameConfig(align=('right', 'middle')))
        r2 += VU2chHorzFrame(r2, visuals=VUBarStyle(bar_style=BarStyle(effects=BarEffects(threshold=0.1))))
        r3 = ColFramer(rows, col_ratios=(1, 3))
        r3 += TextFrame(r3, text='High Intensity', config=FrameConfig(align=('right', 'middle')))
        r3 += VU2chHorzFrame(r3, visuals=VUBarStyle(bar_style=BarStyle(effects=BarEffects(threshold=0.5, scale=4.0, alpha=100, blur=100.0))))
        r4 = ColFramer(rows, col_ratios=(1, 3))
        r4 += TextFrame(r4, text='Sharp Glow', config=FrameConfig(align=('right', 'middle')))
        r4 += VU2chHorzFrame(r4, visuals=VUBarStyle(bar_style=BarStyle(effects=BarEffects(threshold=0.5, blur=10.0, alpha=130))))

class BarParametersTestScreen(Frame):

    @property
    def title(self):
        return 'Bar Parameters Test Screen'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        
        super().__init__(platform, config=FrameConfig(theme='hifi', background=BackgroundStyle(texture_path='particles.jpg', texture_opacity= 0.3)))
        rows = RowFramer(self, row_ratios=(1, 1, 1, 1), config=FrameConfig(padding=20))
        r1 = ColFramer(rows, col_ratios=(1, 3))
        r1 += TextFrame(r1, text='Default', config=FrameConfig(align=('right', 'middle')))
        r1 += VU2chHorzFrame(r1)
        r2 = ColFramer(rows, col_ratios=(1, 3))
        r2 += TextFrame(r2, text='Blocky (Retro)', config=FrameConfig(align=('right', 'middle')))
        r2 += VU2chHorzFrame(r2, visuals=VUBarStyle(bar_style=BarStyle(segment_size=15, segment_gap=2, corner_radius=0, edge_softness=0.0)))
        r3 = ColFramer(rows, col_ratios=(1, 3))
        r3 += TextFrame(r3, text='Round & Soft', config=FrameConfig(align=('right', 'middle')))
        r3 += VU2chHorzFrame(r3, visuals=VUBarStyle(bar_style=BarStyle(segment_size=8, segment_gap=4, corner_radius=4, edge_softness=0.1)))
        r4 = ColFramer(rows, col_ratios=(1, 3))
        r4 += TextFrame(r4, text='Solid (Analog)', config=FrameConfig(align=('right', 'middle')))
        r4 += VU2chHorzFrame(r4, visuals=VUBarStyle(bar_style=BarStyle(segment_size=10, segment_gap=0, corner_radius=5, edge_softness=0.02)))
