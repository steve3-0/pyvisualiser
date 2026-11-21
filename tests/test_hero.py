from pyvisualiser.core.frame_config import FrameConfig
'\n All top level screens.  Screens are comprised of Frames\n\n v1.0 Baloothebear4 Mar 2026\n\n\n'
from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
from pyvisualiser.visualisers.glvisualisers import *
from pyvisualiser.visualisers.oscillogramme import *
from pyvisualiser.core.base_defs import *
from pyvisualiser.styles.presets import *
from pyvisualiser.styles.styles import *
from pyvisualiser.core.framecore import Frame, RowFramer, ColFramer
' Common styles for this profile'
SimpleOutline = OutlineStyle(colour='mid', width=1, radius=10, opacity=1.0, glow_intensity=0.2, softness=1.0)
Edge = EdgeLightStyle(enabled=True, intensity=0.7, width=0.2, softness=1.2, audio_reactivity=0.0)
ArtOutline = OutlineStyle(colour='mid', width=5, radius=10, opacity=1.0, glow_intensity=0.3, softness=1.0)
Cloud = CloudStyle(opacity=0.5)
ScreenBackground = BackgroundStyle(starfield=False, cloud=Cloud, edge_light=Edge)
' A Floating frame that sits on top of a screen on the RHS same'

class VolumeSource(Frame):

    @property
    def title(self):
        return 'Volume and Source'

    @property
    def type(self):
        return 'Hi-Fi'

    def __init__(self, platform, **kwargs):
        Frame.__init__(self, platform, **kwargs)
        rows = RowFramer(self, row_ratios=(1, 1, 1), padpc=0.05, config=FrameConfig(padding=10, align=('right', 'bottom'), scalers=(0.1, 1.0)))
        rows += CircularProgress(rows, colour='mid')
        rows += MetaData(rows, key=MetadataKey.SOURCE, visuals=TextStyle(colour='mid'))
        rows += MetaData(rows, key=MetadataKey.VOLUME, visuals=TextStyle(colour='foreground'))

class H1(Frame):

    @property
    def title(self):
        return 'Hero 1: Analogue VU Meters, Roon Album Art, Metadata and progress bar'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        EDGE = EdgeLightStyle(enabled=True, intensity=0.9, width=0.2, softness=1.2, audio_reactivity=0.0)
        BACKGROUND = BackgroundStyle(colour='background', ambient_glow=None, texture_path='particles.jpg', texture_opacity=0.4, reactive_glow=None, starfield=False, edge_light=EDGE)
        Frame.__init__(self, platform, config=FrameConfig(background=BACKGROUND, theme='hifi', padding=0, outline=None))
        NEEDLE = VUNeedleStyle(colour='foreground', width=2, length=0.8, radius_pc=1.0, glow_intensity=0.2, glow_colour='foreground', tip_glow=True, shadow=True)
        ENDSTOPS = (3 * PI / 4, 5 * PI / 4)
        PIVOT = -0.5
        ANNOTATE = {'Valign': 'middle', 'text': 'dB', 'colour': 'foreground'}
        FONTH = 0.06
        PIVOT = -0.5
        NEEDLELEN = 0.8
        TICKLEN = 0.75
        SCALESLEN = 0.8
        ARCLEN = TICKLEN
        TICK_PC = 0.1
        TICK_W = 3
        TICKCOLOUR = 'light'
        MARKCOLOUR = 'foreground'
        MARKS = {0.0: {'text': '-20', 'width': TICK_W, 'colour': MARKCOLOUR}, 0.3: {'text': '-10', 'width': TICK_W, 'colour': MARKCOLOUR}, 0.5: {'text': '-3', 'width': TICK_W, 'colour': MARKCOLOUR}, 0.6: {'text': '-1', 'width': TICK_W, 'colour': MARKCOLOUR}, 0.7: {'text': '+0', 'width': TICK_W, 'colour': MARKCOLOUR}, 0.8: {'text': '+1', 'width': TICK_W, 'colour': MARKCOLOUR}, 0.9: {'text': '+2', 'width': TICK_W, 'colour': MARKCOLOUR}, 1.0: {'text': '+3', 'width': TICK_W, 'colour': MARKCOLOUR}}
        ARCS = {ARCLEN * 0.9: {'width': TICK_W - 1, 'colour': TICKCOLOUR}}
        VIS_OPACITY = 0.8
        VUGlow = AmbientGlowStyle(colour='foreground', radius=0.3, softness=0.4, opacity=0.7)
        VUOutline = OutlineStyle(colour='mid', width=4, opacity=1.0, radius=25, glow_intensity=0.1, softness=0.05)
        VUBackground = BackgroundStyle(colour='background', colour_opacity=VIS_OPACITY, ambient_glow=VUGlow)
        VUscale = VUMeterScale(marks=MARKS, arcs=ARCS, annotate=ANNOTATE, tick_width=TICK_W, scale_radius=SCALESLEN, tick_colour=TICKCOLOUR, font_height=FONTH, tick_length=TICKLEN, tick_radius_pc=TICK_PC)
        meter = VUMeterStyle(pivot=PIVOT, endstops=ENDSTOPS, needle=NEEDLE, scale=VUscale)
        BAR_STYLE = BarStyle(led_gap=2, peak_h=2, radius=0, led_h=4, colour_mode='vert')
        SPECTRUM_STYLE = SpectrumStyle(barsize_pc=0.3, barw_min=10, decay=0.23, bar_style=BAR_STYLE)
        SPECTRUM_STYLE_FLIP = SpectrumStyle(barsize_pc=0.3, barw_min=10, decay=0.23, bar_style=BAR_STYLE, flip=True)
        SPECTRUM_BACKGROUND = BackgroundStyle(colour='background', colour_opacity=VIS_OPACITY, ambient_glow=None)
        METERPAD = 0
        METAPAD = 0
        cols = ColFramer(self, col_ratios=(1, 2, 1), padpc=0.1)
        row_l = RowFramer(cols, row_ratios=(2, 1), padpc=0.15)
        row_l += VUMeter(row_l, Channel.LEFT, visuals=meter, config=FrameConfig(square=False, background=VUBackground, outline=SimpleOutline, padding=METERPAD))
        source = RowFramer(row_l, row_ratios=(2, 1, 1))
        source += MetaData(source, key=MetadataKey.SOURCE, visuals=TextStyle(colour='light'))
        source += MetaData(source, key=MetadataKey.FORMAT, visuals=TextStyle(colour='light'))
        source += MetaData(source, key=MetadataKey.SAMPLE_RATE, visuals=TextStyle(colour='light'))
        centre = RowFramer(cols, row_ratios=(3, 1, 0.4), padpc=0.15)
        stereo = ColFramer(centre, col_ratios=(1, 1), config=FrameConfig(outline=SimpleOutline, padding=10), padpc=0.0)
        stereo += SpectrumFrame(centre, 'left', visuals=SPECTRUM_STYLE_FLIP)
        stereo += SpectrumFrame(centre, 'right', visuals=SPECTRUM_STYLE)
        metadata = RowFramer(centre, padpc=0.0, config=FrameConfig(padding=10, outline=SimpleOutline, background=BackgroundStyle(colour_opacity=0.2, reactive_glow=ReactiveGlowStyle(colour='mid'))))
        metadata += MetaData(metadata, key=MetadataKey.TRACK, visuals=TextStyle(justify='left', colour='foreground'))
        metadata += MetaData(metadata, key=MetadataKey.ARTIST, visuals=TextStyle(justify='left', colour='light'))
        centre += PlayProgressFrame(centre)
        rows_r = RowFramer(cols, row_ratios=(2, 1), padpc=0.15)
        rows_r += VUMeter(rows_r, Channel.RIGHT, visuals=meter, config=FrameConfig(square=False, background=VUBackground, outline=SimpleOutline, padding=METERPAD))
        rows_r += MetaData(rows_r, key=MetadataKey.VOLUME, visuals=TextStyle(colour='foreground'), config=FrameConfig(padding=METAPAD))

class H2(Frame):

    @property
    def title(self):
        return 'Spectrum, Metadata and progress bar'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        SpectrumGlow = None
        SpectrumReact = None
        edge = EdgeLightStyle(enabled=True, intensity=0.7, width=0.2, softness=1.2, audio_reactivity=0.0)
        SpectrumBackground = BackgroundStyle(colour='background', ambient_glow=SpectrumGlow, edge_light=Edge, texture_path='particles.jpg', texture_opacity=0.6)
        SimpleOutline = OutlineStyle(colour='mid', width=1, radius=10, opacity=1.0, glow_intensity=0.0, softness=0.0)
        Frame.__init__(self, platform, config=FrameConfig(theme='hifi', background=SpectrumBackground))
        cols = ColFramer(self, col_ratios=(1, 2), padpc=0.0, config=FrameConfig(padding=10))
        cols += MetaImages(cols, key=MetadataKey.ALBUM, visuals=ImageStyle(opacity=1.0), config=FrameConfig(padding=10, background=None, outline=ArtOutline))
        centre = RowFramer(cols, row_ratios=(1.5, 3, 1), padpc=0.0, config=FrameConfig(padding=0))
        metadata = RowFramer(centre, padpc=0.0)
        metadata += MetaData(metadata, key=MetadataKey.TRACK, visuals=TextStyle(justify='left', colour='foreground'))
        metadata += MetaData(metadata, key=MetadataKey.ARTIST, visuals=TextStyle(justify='left', colour='light'))
        reflection_style = ReflectionStyle(size=0.5, opacity=0.05)
        effects_style = BarEffects(reflection=reflection_style, threshold=0.6, scale=2.0, alpha=200, blur=1.5)
        bar_style = BarStyle(led_gap=0, peak_h=2, radius=3, tip=True, flip=False, effects=effects_style)
        spectrum_style = SpectrumStyle(barw_min=3, barsize_pc=1, barw_max=10, decay=0.2, bar_style=bar_style)
        centre += SpectrumFrame(centre, 'mono', config=FrameConfig(padding=0), visuals=spectrum_style)
        centre += Frame(centre)
        self += VolumeSource(self)

class H3(Frame):

    @property
    def title(self):
        return 'Art, Visualiser, Metadata and progress bar'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(theme='hifi', padding=0, background=ScreenBackground))
        colframe = ColFramer(self, padpc=0.0, col_ratios=(2, 8, 0.8), config=FrameConfig(padding=10, background=None))
        vu_style = BarStyle(orient='vert', flip=False, tip=True, led_h=10)
        vu_frame = RowFramer(colframe)
        vu_frame += VUFrame(vu_frame, 'left', visuals=BarStyle(orient='vert', flip=False, tip=True, led_h=10))
        vu_frame += VUFrame(vu_frame, 'right', visuals=BarStyle(orient='vert', flip=True, tip=True, led_h=10))
        colframe += ShaderFrame(colframe, shader='liquidorb', colour='mid')
        colframe += Frame(colframe)
        self += VolumeSource(self)

class H4(Frame):

    @property
    def title(self):
        return 'Artist, Visualiser, Metadata, Bar VU and progress bar, spectrum along bottom'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(theme='hifi', padding=0, background=ScreenBackground))
        colframe = ColFramer(self, padpc=0.0, col_ratios=(3, 4, 0.8), config=FrameConfig(padding=10, background=None))
        image = RowFramer(colframe, row_ratios=(4, 1), config=FrameConfig(outline=ArtOutline))
        image += MetaImages(image, key=MetadataKey.ARTIST, config=FrameConfig(background=BackgroundStyle(colour='background', colour_opacity=1.0)), visuals=ImageStyle(reflection=True))
        image += MetaData(image, key=MetadataKey.ARTIST, visuals=TextStyle(colour='mid', justify='centre'))
        metadata_col = RowFramer(colframe, row_ratios=(1, 3, 3), padpc=0.0, config=FrameConfig(padding=0))
        metadata_col += MetaData(metadata_col, key=MetadataKey.TRACK, visuals=TextStyle(colour='foreground'))
        metadata_col += OscilogrammeBar(metadata_col, 'left', visuals=OscillogrammeStyle(barsize_pc=0.5, barw_min=2, bar_style=BarStyle(led_gap=0)))
        metadata_col += OscilogrammeBar(metadata_col, 'right', visuals=OscillogrammeStyle(barsize_pc=0.5, barw_min=2, bar_style=BarStyle(led_gap=0, flip=True)))
        colframe += Frame(colframe)
        self += VolumeSource(self)

class H5(Frame):

    @property
    def title(self):
        return 'Analogue VU Meters, Roon Album Art, Metadata and progress bar'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        Frame.__init__(self, platform, config=FrameConfig(background=ScreenBackground, theme='hifi', padding=0))
        TICK_W = 3
        TICK_PC = 0.1
        ARCLEN = 0.8
        SCALESLEN = 0.87
        FONTHEIGHT = 0.06
        TICKLEN = 0.8
        VUTEXT = 'foreground'
        MARKCOLOUR = 'light'
        MARKS = {0.0: {'text': '-40', 'width': TICK_W, 'colour': VUTEXT}, 0.2: {'text': '-20', 'width': TICK_W, 'colour': VUTEXT}, 0.3: {'text': '-10', 'width': TICK_W, 'colour': VUTEXT}, 0.4: {'text': '-5', 'width': TICK_W, 'colour': VUTEXT}, 0.5: {'text': '-3', 'width': TICK_W, 'colour': VUTEXT}, 0.6: {'text': '-1', 'width': TICK_W, 'colour': VUTEXT}, 0.7: {'text': '0', 'width': TICK_W * 2, 'colour': VUTEXT}, 0.8: {'text': '+1', 'width': TICK_W * 2, 'colour': VUTEXT}, 0.9: {'text': '+2', 'width': TICK_W * 2, 'colour': VUTEXT}, 1.0: {'text': '+3', 'width': TICK_W * 2, 'colour': VUTEXT}}
        ARCS = {ARCLEN * (1 - TICK_PC): {'width': TICK_W - 1, 'colour': MARKCOLOUR}}
        ANNOTATE = {'Valign': 'middle', 'text': 'dB', 'colour': VUTEXT}
        vuglow = AmbientGlowStyle(colour='foreground', radius=0.4, softness=0.3, opacity=0.5)
        vuoutline = OutlineStyle(colour='light', width=1.0, opacity=1.0, radius=25, glow_intensity=0.4, softness=1.5)
        vubackground = BackgroundStyle(colour='background', colour_opacity=0.3, ambient_glow=vuglow, texture_opacity=0.0, texture_path='particles.jpg')
        style = VUMeterStyle(pivot=-0.7, endstops=(3 * PI / 4, 5 * PI / 4), pivotcoverpc=0.25, pivotcovercolour='dark', needle=VUNeedleStyle(width=3, colour='foreground', length=0.8, radius_pc=0.75, glow_intensity=0.0, glow_colour='foreground', tip_glow=True, shadow=True), scale=VUMeterScale(marks=MARKS, arcs=ARCS, annotate=ANNOTATE, scale_radius=SCALESLEN, font_height=FONTHEIGHT, tick_length=TICKLEN, tick_width=TICK_W, tick_radius_pc=TICK_PC, tick_colour=MARKCOLOUR))
        cols_all = ColFramer(self, col_ratios=(10, 1))
        rows = RowFramer(cols_all, row_ratios=(4, 1), padpc=0.0, config=FrameConfig(padding=10))
        cols = ColFramer(rows, padpc=0.22, config=FrameConfig(padding=20))
        cols += VUMeter(cols, Channel.LEFT, visuals=style, config=FrameConfig(background=vubackground, outline=vuoutline))
        cols += VUMeter(cols, Channel.RIGHT, visuals=style, config=FrameConfig(background=vubackground, outline=vuoutline))
        metadata = RowFramer(rows, padpc=0.05, config=FrameConfig(outline=None))
        metadata += MetaData(metadata, key=MetadataKey.TRACK, visuals=TextStyle(justify='centre', colour='foreground'))
        metadata += MetaData(metadata, key=MetadataKey.ARTIST, visuals=TextStyle(justify='centre', colour='light'))
        cols_all += Frame(cols_all)
        self += VolumeSource(self)

class H6(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent, config=FrameConfig(theme='hifi', background=ScreenBackground))
        cols = ColFramer(self, col_ratios=(4, 7, 1), padpc=0.0, config=FrameConfig(padding=10))
        image = RowFramer(cols, row_ratios=(4, 1), config=FrameConfig(outline=None))
        image += MetaImages(image, key=MetadataKey.ALBUM, visuals=ImageStyle(reflection=True), config=FrameConfig(padding=0, background=BackgroundStyle(colour='background', colour_opacity=1.0), outline=OutlineStyle(width=0, softness=1.8, glow_intensity=0.2, glow_colour='foreground')))
        image += Frame(image)
        rows = RowFramer(cols, row_ratios=(3, 1), padpc=0.05, config=FrameConfig(padding=5))
        rows += MetaDataFrame(rows)
        rows += SpectrumFrame(rows, channel='mono', visuals=SpectrumStyle(barsize_pc=4, bar_style=BarStyle(led_gap=0)))
        cols += Frame(cols)
        self += VolumeSource(self)

class H7(Frame):

    @property
    def title(self):
        return 'GLSL Shader Test - as a background'

    @property
    def type(self):
        return 'Test'

    def __init__(self, platform):
        super().__init__(platform, config=FrameConfig(theme='hifi', background=BackgroundStyle(colour='background', shader='milkdrop', edge_light=Edge)))
        SpectrumGlow = None
        SpectrumReact = None
        edge = EdgeLightStyle(enabled=True, intensity=0.7, width=0.2, softness=1.2, audio_reactivity=0.0)
        SpectrumBackground = BackgroundStyle(colour='background', ambient_glow=SpectrumGlow, edge_light=edge, texture_path='particles.jpg', texture_opacity=0.6)
        SimpleOutline = OutlineStyle(colour='mid', width=1, radius=10, opacity=1.0, glow_intensity=0.0, softness=0.0)
        cols = ColFramer(self, col_ratios=(4, 1), padpc=0.05, config=FrameConfig(padding=0))
        centre = RowFramer(cols, row_ratios=(1.5, 3, 1), padpc=0.0, config=FrameConfig(padding=0))
        metadata = RowFramer(centre, padpc=0.0)
        metadata += MetaData(metadata, key=MetadataKey.TRACK, visuals=TextStyle(justify='left', colour='foreground'))
        metadata += MetaData(metadata, key=MetadataKey.ARTIST, visuals=TextStyle(justify='left', colour='light'))
        reflection_style = ReflectionStyle(size=0.5, opacity=0.05)
        effects_style = BarEffects(reflection=reflection_style, threshold=0.6, scale=2.0, alpha=200, blur=1.5)
        bar_style = BarStyle(led_gap=0, peak_h=2, radius=3, tip=True, flip=False, effects=effects_style)
        spectrum_style = SpectrumStyle(barw_min=3, barsize_pc=1, barw_max=10, decay=0.2, bar_style=bar_style)
        centre += SpectrumFrame(centre, 'mono', config=FrameConfig(padding=0), visuals=spectrum_style)
        centre += Frame(centre)
        cols += Frame(cols)
        self += VolumeSource(self)

class H8(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent, config=FrameConfig(theme='hifi', background=ScreenBackground))
        basepanel = BackgroundStyle(colour='background', colour_opacity=0.2, ambient_glow=None, texture_opacity=0.0, texture_path='particles.jpg')
        baseoutline = OutlineStyle(colour='mid', width=0, radius=10, opacity=1.0, glow_intensity=0.2, softness=0.7)
        effects_style = BarEffects(reflection=None, threshold=0.6, scale=2.0, alpha=200, blur=1.5)
        left_bar_style = BarStyle(led_gap=2, peak_h=2, radius=3, tip=True, flip=False, effects=effects_style)
        right_bar_style = BarStyle(led_gap=2, peak_h=2, radius=3, tip=True, flip=True, effects=effects_style)
        spectrum_style_left = SpectrumStyle(barsize_pc=1.0, barw_min=3, barw_max=10, decay=0.25, bar_style=left_bar_style)
        spectrum_style_right = SpectrumStyle(barsize_pc=1.0, barw_min=3, barw_max=10, decay=0.25, bar_style=right_bar_style)
        cols = ColFramer(self, col_ratios=(1, 10, 1), padpc=0.1, config=FrameConfig(padding=10))
        vu_style = BarStyle(orient='vert', flip=False, tip=True, led_h=10)
        vu_frame = ColFramer(cols, config=FrameConfig(padding=10, background=basepanel, outline=baseoutline))
        vu_frame += VUFrame(vu_frame, 'left', visuals=vu_style)
        vu_frame += VUFrame(vu_frame, 'right', visuals=vu_style)
        col2 = RowFramer(cols, row_ratios=(3, 0.3, 1), padpc=0.0, config=FrameConfig(padding=0))
        spectrum = RowFramer(col2, row_ratios=(1, 1), padpc=0.0, config=FrameConfig(padding=0, background=basepanel, outline=baseoutline))
        spectrum += SpectrumFrame(spectrum, channel='left', visuals=spectrum_style_left)
        spectrum += SpectrumFrame(spectrum, channel='right', visuals=spectrum_style_right)
        col2 += Frame(col2)
        col2 += MetaData(col2, key=MetadataKey.TRACK, config=FrameConfig(background=basepanel, outline=baseoutline), visuals=TextStyle(justify='centre', colour='foreground'))
        cols += Frame(cols)
        self += VolumeSource(self)

class H9(Frame):

    def __init__(self, parent):
        background = BackgroundStyle(colour='background', shader='balatro', edge_light=Edge)
        Frame.__init__(self, parent, config=FrameConfig(theme='hifi', background=ScreenBackground))
        cols = ColFramer(self, col_ratios=(4, 7, 1), padpc=0.0, config=FrameConfig(padding=10))
        metadata = RowFramer(cols, row_ratios=(4, 2, 7), padpc=0.0)
        metadata += MetaData(metadata, key=MetadataKey.TRACK, visuals=TextStyle(justify='left', colour='foreground'))
        metadata += MetaData(metadata, key=MetadataKey.ARTIST, visuals=TextStyle(justify='left', colour='light'))
        metadata += Frame(metadata)
        cols += ShaderFrame(cols, shader='pinkball', colour='light')
        cols += Frame(cols)
        self += VolumeSource(self)