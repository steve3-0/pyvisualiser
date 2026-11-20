#!/usr/bin/env python
"""
 All top level screens.  Screens are comprised of Frames

 v1.0 Baloothebear4 Mar 2026


"""


# from pyvisualiser import *
from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
from pyvisualiser.visualisers.glvisualisers import *
from pyvisualiser.visualisers.oscillogramme import *

from pyvisualiser.styles.presets import *
from pyvisualiser.styles.styles  import *
from pyvisualiser.core.framecore  import Frame, RowFramer, ColFramer

""" Common styles for this profile"""
SimpleOutline     = OutlineStyle(colour='mid', width=1, radius=10, opacity=1.0, glow_intensity=0.2, softness=1.0)
Edge              = EdgeLightStyle(enabled=True, intensity=0.7, width=0.2, softness=1.2,audio_reactivity=0.0)
ArtOutline        = OutlineStyle(colour='mid', width=5, radius=10, opacity=1.0, glow_intensity=0.3, softness=1.0)
Cloud             = CloudStyle(opacity=0.5)
ScreenBackground  = BackgroundStyle(starfield=False,cloud=Cloud, edge_light=Edge )

""" A Floating frame that sits on top of a screen on the RHS same"""
class VolumeSource(Frame):
    @property
    def title(self): return 'Volume and Source' 

    @property
    def type(self): return 'Hi-Fi'

    def __init__(self, platform, **kwargs):
        Frame.__init__(self, platform, **kwargs)
        rows = RowFramer(self, row_ratios=(1,1,1), padding=10, padpc=0.05, align=('right','bottom'), scalers=(0.1,1.0))
        rows += CircularProgress(rows, colour='mid')
        rows += MetaData(rows, metadata_type='source', colour='mid')
        rows += MetaData(rows, metadata_type='volume', colour='foreground')


class H1(Frame):   # comprises volume on the left, spectrum on the right
    @property
    def title(self): return 'Hero 1: Analogue VU Meters, Roon Album Art, Metadata and progress bar'

    @property
    def type(self): return 'Test'

    def __init__(self, platform):


        edge = EdgeLightStyle(enabled=True, intensity=0.7, width=0.2, softness=1.2,audio_reactivity=0.0)
        BACKGROUND    = BackgroundStyle(colour='background', ambient_glow=None, \
                                        texture_path='particles.jpg', texture_opacity=0.6, \
                                        reactive_glow=None, starfield=False, edge_light=Edge   )
        

        Frame.__init__(self, platform, background=BACKGROUND, theme= 'ocean', padding=0, outline=None)


        NEEDLE    = VUNeedleStyle( colour='foreground', width=2, length=0.8, radius_pc=1.0, 
                                  glow_intensity=0.2, glow_colour='foreground', tip_glow=True, shadow=True )     
        ENDSTOPS  = (3*PI/4, 5*PI/4)  
        PIVOT     = -0.5
        ANNOTATE  = { 'Valign':'middle', 'text':'dB', 'colour':'foreground' }
        FONTH     = 0.06
        PIVOT     = -0.5
        NEEDLELEN = 0.8
        TICKLEN   = 0.75
        SCALESLEN = 0.80
        ARCLEN    = TICKLEN
        TICK_PC   = 0.1
        TICK_W    = 3
        TICKCOLOUR = 'light'
        MARKCOLOUR = 'foreground'
        MARKS     = {   0.0: {'text':'-20', 'width': TICK_W, 'colour': MARKCOLOUR},
                        0.3: {'text':'-10', 'width': TICK_W, 'colour': MARKCOLOUR},
                        0.5: {'text':'-3', 'width': TICK_W, 'colour': MARKCOLOUR},
                        0.6: {'text':'-1', 'width': TICK_W, 'colour': MARKCOLOUR},
                        0.7: {'text':'+0', 'width': TICK_W, 'colour': MARKCOLOUR},
                        0.8: {'text':'+1', 'width': TICK_W, 'colour': MARKCOLOUR},
                        0.9: {'text':'+2', 'width': TICK_W, 'colour': MARKCOLOUR},
                        1.0: {'text':'+3', 'width': TICK_W, 'colour': MARKCOLOUR}}

        ARCS      = { ARCLEN*0.9: {'width': TICK_W-1, 'colour': TICKCOLOUR} }

        VIS_OPACITY     = 0.8
        VUGlow          = AmbientGlowStyle(colour='foreground', radius=0.3, softness=0.4, opacity=0.7)
        VUOutline       = OutlineStyle(colour='mid', width=4, opacity=1.0, radius=25, glow_intensity=0.1, softness=0.05)  
        VUBackground    = BackgroundStyle(colour='background', colour_opacity=VIS_OPACITY, ambient_glow=VUGlow)
        VUscale         = VUMeterScale(marks=MARKS, arcs=ARCS, annotate=ANNOTATE, tick_width=TICK_W, scale_radius=SCALESLEN, 
                                        tick_colour=TICKCOLOUR ,font_height=FONTH, tick_length=TICKLEN, tick_radius_pc=TICK_PC)

        meter           = VUMeterStyle(pivot=PIVOT, endstops=ENDSTOPS, needle=NEEDLE, scale=VUscale)
  
        # Migrated bar_style parameters into SpectrumStyle
        BAR_STYLE       = BarStyle(led_gap=2, peak_h=2, radius=0, led_h=4, colour_mode='vert')
        SPECTRUM_STYLE  = SpectrumStyle(barsize_pc=0.3, barw_min=10, decay=0.23, bar_style=BAR_STYLE)
        SPECTRUM_STYLE_FLIP = SpectrumStyle(barsize_pc=0.3, barw_min=10, decay=0.23, bar_style=BAR_STYLE, flip=True)
        
        SPECTRUM_BACKGROUND    = BackgroundStyle(colour='background', colour_opacity=VIS_OPACITY, ambient_glow=None)

        METERPAD  = 0
        METAPAD = 0

        cols = ColFramer(self, col_ratios=(1,2,1),padpc=0.1)

        row_l     = RowFramer(cols, row_ratios=(2,1),padpc=0.15)
        row_l    += VUMeter(row_l, 'left', square=False, style=meter, background=VUBackground, outline=SimpleOutline,padding=METERPAD)

        source    = RowFramer(row_l, row_ratios=(2,1,1),padding=METAPAD)
        source    += MetaData(source, metadata_type='source', colour='light')
        source    += MetaData(source, metadata_type='format', colour='light')
        source    += MetaData(source, metadata_type='sample_rate', colour='light')
 
        centre    = RowFramer(cols, row_ratios=(3,1,0.4),outline=None,padding=0,padpc=0.1)

        stereo    = ColFramer(centre, col_ratios=(1,1),outline=SimpleOutline,padding=1,padpc=0.0)
        stereo    += SpectrumFrame(centre, 'left', spectrum_style=SPECTRUM_STYLE_FLIP) 
        stereo    += SpectrumFrame(centre, 'right', spectrum_style=SPECTRUM_STYLE) 
  
        # centre   += SpectrumFrame(centre, 'mono', spectrum_style=SPECTRUM_STYLE, background=SPECTRUM_BACKGROUND, outline=SimpleOutline,padding=1) 
        # centre += SpectrumStereoFrame(centre)

        metadata  = RowFramer(centre,padpc=0.0,padding=10, outline=SimpleOutline, background=BackgroundStyle(colour_opacity=0.2, reactive_glow=ReactiveGlowStyle(colour='mid')))
        metadata  += MetaData(metadata, metadata_type='track',justify=('left'), colour='foreground')
        metadata  += MetaData(metadata, metadata_type='artist',justify=('left'), colour='light')
        centre    += PlayProgressFrame(centre)

        rows_r   = RowFramer(cols, row_ratios=(2,1),padpc=0.15)
        rows_r   += VUMeter(rows_r,'right', square=False, style=meter, background=VUBackground, outline=SimpleOutline,padding=METERPAD)
        rows_r   += MetaData(rows_r, metadata_type='volume', colour='foreground',padding=METAPAD)


class H2(Frame):   # comprises volume on the left, spectrum on the right
    @property
    def title(self): return 'Spectrum, Metadata and progress bar'

    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        SpectrumGlow          = None
        SpectrumReact         = None
        edge = EdgeLightStyle(enabled=True, intensity=0.7, width=0.2, softness=1.2,audio_reactivity=0.0)
        SpectrumBackground    = BackgroundStyle(colour='background', ambient_glow=SpectrumGlow, edge_light=Edge,\
                                                texture_path='particles.jpg', texture_opacity=0.6 )
        SimpleOutline         = OutlineStyle(colour='mid', width=1, radius=10, opacity=1.0, glow_intensity=0.0, softness=0.0)
        Frame.__init__(self, platform, theme= 'hifi', background=SpectrumBackground)

        cols              = ColFramer(self,col_ratios=(1,2), padding=10, padpc=0.00)

        cols            += MetaImages(cols, padding=10, art_type='album', background=None, outline=ArtOutline, opacity=1.0)
 
        centre           = RowFramer(cols, row_ratios=(1.5,3,1), padding=0, padpc=0.0)

        metadata         = RowFramer(centre,padpc=0.0)
        metadata        += MetaData(metadata, metadata_type='track',justify=('left'), colour='foreground')
        metadata        += MetaData(metadata, metadata_type='artist',justify=('left'), colour='light')

        reflection_style = ReflectionStyle(size=0.5, opacity=0.05)
        effects_style    = BarEffects(reflection=reflection_style, threshold=0.6, scale=2.0, alpha=200, blur=1.5)
        bar_style        = BarStyle(led_gap=0, peak_h=2, radius=3, tip=True,flip=False,effects=effects_style)
        
        # Migrated bar_style inside SpectrumStyle
        spectrum_style   = SpectrumStyle(barw_min=3, barsize_pc=1, barw_max=10, decay=0.2, bar_style=bar_style)

        centre           += SpectrumFrame(centre, 'mono', padding=0, spectrum_style=spectrum_style) 
        centre           += Frame(centre)

        self += VolumeSource(self)


class H3(Frame):   # comprises volume on the left, spectrum on the right    
    @property
    def title(self): return 'Art, Visualiser, Metadata and progress bar'

    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, theme= 'hifi', padding=0, background=ScreenBackground)

        colframe = ColFramer(self, padpc=0.0, col_ratios=(2,8,0.8), padding=10,background=None)

        vu_style = BarStyle(orient='vert', flip=False, tip=True, led_h=10)
        vu_frame = RowFramer(colframe)
        vu_frame += VUFrame(vu_frame, 'left', bar_style=BarStyle(orient='vert', flip=False, tip=True, led_h=10))
        vu_frame += VUFrame(vu_frame, 'right', bar_style=BarStyle(orient='vert', flip=True, tip=True, led_h=10))

        colframe += ShaderFrame(colframe, shader='liquidorb', colour='mid')
        colframe += Frame(colframe) 
        self += VolumeSource(self)
        


class H4(Frame):   # comprises volume on the left, spectrum on the right    
    @property
    def title(self): return 'Artist, Visualiser, Metadata, Bar VU and progress bar, spectrum along bottom'

    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, theme= 'hifi', padding=0, background=ScreenBackground)

        colframe    = ColFramer(self, padpc=0.0, col_ratios=(3,4,0.8), padding=10,background=None)

        image = RowFramer(colframe, row_ratios=(4,1),outline=ArtOutline)
        image += MetaImages(image, padding=10, art_type='artist', background=BackgroundStyle(colour='background', colour_opacity=1.0),  reflection=True)  
        image += MetaData(image, metadata_type='artist', colour='mid',justify=('centre'))

        metadata_col  = RowFramer(colframe, row_ratios=(1,3,3), padding=0,padpc=0.0)
        metadata_col += MetaData(metadata_col, metadata_type='track', colour='foreground')
        metadata_col += OscilogrammeBar(metadata_col, 'left', oscillograme=OscillogrammeStyle(barsize_pc=0.5, barw_min=2), bar_style=BarStyle(led_gap=0))
        metadata_col += OscilogrammeBar(metadata_col, 'right', oscillograme=OscillogrammeStyle(barsize_pc=0.5, barw_min=2), bar_style=BarStyle(led_gap=0,flip=True))

        colframe += Frame(colframe) 
        self += VolumeSource(self)
        
class H5(Frame):   # comprises volume on the left, spectrum on the right
    @property
    def title(self): return 'Analogue VU Meters, Roon Album Art, Metadata and progress bar'

    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, background=ScreenBackground, theme= 'hifi', padding=0)

        TICK_W    = 3
        TICK_PC   = 0.1
        ARCLEN    = 0.8
        SCALESLEN = 0.87
        FONTHEIGHT = 0.06
        TICKLEN   = 0.8
        VUTEXT    = 'foreground'
        MARKCOLOUR = 'light'
        MARKS     = {0.0: {'text':'-40', 'width': TICK_W, 'colour': VUTEXT},
                     0.2: {'text':'-20', 'width': TICK_W, 'colour': VUTEXT},
                     0.3: {'text':'-10', 'width': TICK_W, 'colour': VUTEXT},
                     0.4: {'text':'-5', 'width': TICK_W, 'colour': VUTEXT},
                     0.5: {'text':'-3', 'width': TICK_W, 'colour': VUTEXT},
                     0.6: {'text':'-1', 'width': TICK_W, 'colour': VUTEXT},
                     0.7: {'text':'0', 'width': TICK_W*2, 'colour': VUTEXT},
                     0.8: {'text':'+1', 'width': TICK_W*2, 'colour': VUTEXT},
                     0.9: {'text':'+2', 'width': TICK_W*2, 'colour': VUTEXT},
                     1.0: {'text':'+3', 'width': TICK_W*2, 'colour': VUTEXT}
                     }
        ARCS      = {ARCLEN*(1-TICK_PC): {'width': TICK_W-1, 'colour': MARKCOLOUR} }
        ANNOTATE  = { 'Valign':'middle', 'text':'dB', 'colour':VUTEXT }
        
        vuglow          = AmbientGlowStyle(colour='foreground', radius=0.4, softness=0.3, opacity=0.5)
        vuoutline       = OutlineStyle(colour='light', width=1.0, opacity=1.0, radius=25, glow_intensity=0.4, softness=1.5)  
        vubackground    = BackgroundStyle(colour='background', colour_opacity=0.3, ambient_glow=vuglow, texture_opacity=0.0, texture_path='particles.jpg')

        style = VUMeterStyle(pivot=-0.7, endstops=(3*PI/4, 5*PI/4), pivotcoverpc=0.25, pivotcovercolour='dark',
                             needle=VUNeedleStyle(width=3, colour='foreground', length=0.8, radius_pc=0.75, glow_intensity=0.0, glow_colour='foreground',tip_glow=True, shadow=True),
                             scale=VUMeterScale(marks=MARKS, arcs=ARCS, annotate=ANNOTATE, scale_radius=SCALESLEN, font_height=FONTHEIGHT, tick_length=TICKLEN,
                                                tick_width=TICK_W, tick_radius_pc=TICK_PC, tick_colour=MARKCOLOUR))

        cols_all   = ColFramer(self, col_ratios=(10,1))
        rows = RowFramer(cols_all, row_ratios=(4,1),padding=10, padpc=0.0)

        cols = ColFramer(rows, padpc=0.22,padding=20)
        cols += VUMeter(cols, 'left', style=style, background=vubackground, outline=vuoutline)
        cols += VUMeter(cols, 'right', style=style, background=vubackground, outline=vuoutline)

        metadata  = RowFramer(rows,padpc=0.05,outline=None)
        metadata  += MetaData(metadata, metadata_type='track',justify=('centre'), colour='foreground')
        metadata  += MetaData(metadata, metadata_type='artist',justify=('centre'), colour='light')

        cols_all += Frame(cols_all)  
        self += VolumeSource(self)

class H6(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent, theme='hifi', background=ScreenBackground)

        cols  = ColFramer(self, col_ratios=(4,7,1), padding=10, padpc=0.0)

        image = RowFramer(cols,row_ratios=(4,1), outline=None)
        image += MetaImages(image,  'album',padding=0, reflection=True, background=BackgroundStyle(colour='background', colour_opacity=1.0),
                            outline=OutlineStyle(width=0, softness=1.8, glow_intensity=0.2, glow_colour='foreground'))
        image += Frame(image) 

        rows  = RowFramer(cols, row_ratios=(3,1), padpc=0.05,padding=5)
        rows += MetaDataFrame(rows, justify='left')

        # Migrated bar_style inside SpectrumStyle
        rows  += SpectrumFrame(rows, channel='mono', spectrum_style=SpectrumStyle(barsize_pc=4, bar_style=BarStyle(led_gap=0)))

        cols += Frame(cols) 
        self += VolumeSource(self)


class H7(Frame):
    @property
    def title(self): return 'GLSL Shader Test - as a background'

    @property
    def type(self): return 'Test'

    def __init__(self, platform):
        super().__init__(platform, theme='hifi', background=BackgroundStyle(colour='background', shader='milkdrop',edge_light=Edge))       

        SpectrumGlow          = None
        SpectrumReact         = None
        edge = EdgeLightStyle(enabled=True, intensity=0.7, width=0.2, softness=1.2,audio_reactivity=0.0)
        SpectrumBackground    = BackgroundStyle(colour='background', ambient_glow=SpectrumGlow, edge_light=edge,\
                                                texture_path='particles.jpg', texture_opacity=0.6 )
        SimpleOutline         = OutlineStyle(colour='mid', width=1, radius=10, opacity=1.0, glow_intensity=0.0, softness=0.0)

        cols = ColFramer(self,col_ratios=(4,1), padding=0, padpc=0.05)
        
        centre            = RowFramer(cols, row_ratios=(1.5,3,1), padding=0, padpc=0.0)

        metadata         = RowFramer(centre,padpc=0.0)
        metadata        += MetaData(metadata, metadata_type='track',justify=('left'), colour='foreground')
        metadata        += MetaData(metadata, metadata_type='artist',justify=('left'), colour='light')

        reflection_style = ReflectionStyle(size=0.5, opacity=0.05)
        effects_style    = BarEffects(reflection=reflection_style, threshold=0.6, scale=2.0, alpha=200, blur=1.5)
        bar_style        = BarStyle(led_gap=0, peak_h=2, radius=3, tip=True,flip=False,effects=effects_style)
        
        # Migrated bar_style inside SpectrumStyle
        spectrum_style   = SpectrumStyle(barw_min=3, barsize_pc=1, barw_max=10, decay=0.2, bar_style=bar_style)

        centre           += SpectrumFrame(centre, 'mono', padding=0, spectrum_style=spectrum_style) 
        centre           += Frame(centre)

        cols += Frame(cols) 
        self += VolumeSource(self) 


class H8(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent, theme='hifi', background=ScreenBackground)

        basepanel   = BackgroundStyle(colour='background', colour_opacity=0.2, ambient_glow=None, texture_opacity=0.0, texture_path='particles.jpg')
        baseoutline = OutlineStyle(colour='mid', width=0, radius=10, opacity=1.0, glow_intensity=0.2, softness=0.7)

        effects_style    = BarEffects(reflection=None, threshold=0.6, scale=2.0, alpha=200, blur=1.5)
        
        # Migrated individual channel bar styles inside SpectrumStyle configurations
        left_bar_style  = BarStyle(led_gap=2, peak_h=2, radius=3, tip=True, flip=False, effects=effects_style)
        right_bar_style = BarStyle(led_gap=2, peak_h=2, radius=3, tip=True, flip=True, effects=effects_style)
        
        spectrum_style_left  = SpectrumStyle(barsize_pc=1.0, barw_min=3, barw_max=10, decay=0.25, bar_style=left_bar_style)
        spectrum_style_right = SpectrumStyle(barsize_pc=1.0, barw_min=3, barw_max=10, decay=0.25, bar_style=right_bar_style)

        cols  = ColFramer(self, col_ratios=(1,10,1), padding=10, padpc=0.1)

        vu_style = BarStyle(orient='vert', flip=False, tip=True, led_h=10)
        vu_frame = ColFramer(cols,padding=10, background=basepanel, outline=baseoutline)
        vu_frame += VUFrame(vu_frame, 'left', bar_style=vu_style)
        vu_frame += VUFrame(vu_frame, 'right', bar_style=vu_style)

        col2     = RowFramer(cols, row_ratios=(3,0.3,1), padpc=0.0,padding=0)

        spectrum = RowFramer(col2, row_ratios=(1,1), padding=0, padpc=0.0, background=basepanel, outline=baseoutline)
        spectrum    += SpectrumFrame(spectrum, channel='left', spectrum_style=spectrum_style_left)
        spectrum    += SpectrumFrame(spectrum, channel='right', spectrum_style=spectrum_style_right)
        
        col2    += Frame(col2) 
        col2    += MetaData(col2, metadata_type='track',justify=('centre'), colour='foreground',background=basepanel, outline=baseoutline)

        cols += Frame(cols) 
        self += VolumeSource(self)


class H9(Frame):

    def __init__(self, parent):

        background=BackgroundStyle(colour='background', shader='balatro',edge_light=Edge)
        Frame.__init__(self, parent, theme='hifi', background=ScreenBackground)

        cols  = ColFramer(self, col_ratios=(4,7,1), padding=10, padpc=0.0)

        metadata   = RowFramer(cols,row_ratios=(4,2,7),padpc=0.0)
        metadata  += MetaData(metadata, metadata_type='track',justify=('left'), colour='foreground')
        metadata  += MetaData(metadata, metadata_type='artist',justify=('left'), colour='light')
        metadata  += Frame(metadata) 

        cols += ShaderFrame(cols, shader='pinkball', colour='light')

        cols += Frame(cols) 
        self += VolumeSource(self)