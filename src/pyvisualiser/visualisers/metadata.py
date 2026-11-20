#!/usr/bin/env python
"""
 Visualiser classes for MetaData
    - album/track/artist 
    - source
    - volume
    - data rate

 Part of pyvisualiser

 v1.0 Baloothebear4 Apr 2026
   - refactored from frames.py
   -added source & volume classes
   
"""

from    pyvisualiser.core.framecore  import Frame, RowFramer, ColFramer, get_asset_path, Smoother
from    pyvisualiser.core.components import Line, Box, Image, Text
from    pyvisualiser.visualisers.glvisualisers import ShaderFrame
from    pyvisualiser.styles.presets import Centred

class TextFrame(Frame):
    """
        Display a simple centred set of text
        - text is the largest imaginable width of text
        - V is the vertical alignment
        - Y is the y scaler
    """
    def __init__(self, parent, scalers=None, align=None, text='Default Text', reset=True, theme=None, wrap=False, font_size=None,\
                 colour='foreground', justify='centre', background=None, outline=None, padding=0, update_fn=None, z_order=0):
        
        self.parent         = parent
        self.theme          = theme
        self.background     = background
        self.outline        = outline
        self.padding        = padding
        self.z_order        = z_order
        self.scalers        = scalers
        self.alignment      = align
        self.colour         = colour
        self.wrap           = wrap
        self.reset          = reset
        self.text           = text
        self.justify        = justify
        self.update_fn      = update_fn
        Frame.__init__(self, self.parent, scalers=self.scalers, align=self.alignment, theme=self.theme, \
                       background=self.background, outline=self.outline,padding=self.padding, z_order=self.z_order)
        self.font_size = self.h if font_size is None else font_size

        self.configure()

    def configure(self):
        # print("TextFrame.configure>", self.text, self.background_frame.background, self.geostr())
        self.textcomp      = Text(self, text=self.text, fontmax=self.font_size, reset=self.reset, colour=self.colour, wrap=self.wrap, justify=self.justify, z_order=self.z_order)

    def update_screen(self, text=None, colour=None, fontmax=None, audio=None, media=None):
        if text is None and self.update_fn is not None:
            try:
                # Support update_fn accepting state or parameterless
                text = self.update_fn(media)
            except TypeError:
                text = self.update_fn()
        elif text is None:
            text = self.text

        self.textcomp.draw(text=text, colour=colour, fontmax=fontmax)
        
    @property
    def width(self):
        return self.w
    
    @property
    def fontsize(self):
        return self.text.fontsize


"""
MetaData Frames
- Progress
- Track, Artist & Album
"""

class PlayProgressFrame(Frame):
    """ This creates a propgress bar that moves according to play progress with time elapsd and time to go calc """
    def __init__(self, parent, scalers=None, align=None, barsize_pc=0.5, theme=None, flip=False, outline=None,\
                    led_h=1, led_gap=0, radius=0, barw_min=10, barw_max=400, tip=True, orient='horz', background=None, z_order=10, **kwargs):

        self.barsize_pc     = barsize_pc      # min widths
        self.barw_max       = barw_max      # max width
        self.orient         = orient   # Horz or vert bars
        self.theme          = theme
        Frame.__init__(self, parent, scalers=scalers, align=align, theme=theme, background=background, outline=outline, z_order=z_order)
        self.configure()


    def configure(self):
        self.barw           = self.w * self.barsize_pc if self.orient == 'vert' else self.h * self.barsize_pc   # width of the bar

        text = " 22:22 "
        self.elapsed     = Text(self, fontmax=self.barw, text=text, justify=('left', 'middle'), colour='mid', z_order=self.z_order+1)
        self.remaining   = Text(self, fontmax=self.barw, text=text, justify=('right', 'middle'), colour='mid', z_order=self.z_order+1)
        self.text_width  = self.elapsed.fontwh[0] + self.remaining.fontwh[0]

        box = (self.barw, self.h) if self.orient == 'vert' else (self.w-self.text_width, self.barw)
        self.boxbar      = Box(self, align=('centre', 'middle'), theme=self.theme, box=box, radius=10)

    def update_screen(self, audio=None, media=None):
        # 1. Resolve elapsed and remaining safely from media snapshot or fallback platform
        if media is not None:
            elapsed_str = f"  {media.format_elapsed()}"
            remaining_str = f"{media.format_remaining()}  "
            elapsed_pc = media.elapsed_pc
        else:
            dur = getattr(self.platform, "duration", 0.0) or 0.0
            elap = getattr(self.platform, "elapsed", 0.0) or 0.0
            rem = max(0.0, dur - elap)
            elapsed_str = f"  {int(elap // 60)}:{int(elap % 60):02d}"
            remaining_str = f"{int(rem // 60)}:{int(rem % 60):02d}  "
            elapsed_pc = (elap / dur) if dur > 0 else 0.0

        # 2. Resize box if needed
        box = (self.barw, self.h) if self.orient == "vert" else (self.w - self.text_width, self.barw)
        if self.boxbar.wh != box:
            self.boxbar.resize(box)

        # 3. Draw progress bar geometry
        hide_backline = -self.h / 2 if elapsed_pc * self.w > self.h / 2 else 0
        self.boxbar.drawH(elapsed_pc, flip=True, colour_index="dark", offset=(hide_backline, 0))
        self.boxbar.drawH(elapsed_pc, colour_index="light")

        # 4. Draw labels
        self.elapsed.draw(elapsed_str, colour="light")
        self.remaining.draw(remaining_str, colour="light")
        return True
 
class CircularProgress(Frame):
    @property
    def title(self): return 'GLSL Shader Test - Circular Progress'

    @property
    def type(self): return 'Test'

    def __init__(self, platform,colour='mid'):
        # Use the new 'meter2' theme which has the cream background
        super().__init__(platform, theme='hifi', padding=0, square=True)

        start_text = self.update_text()
        self += ShaderFrame(self, shader='progressdial',colour=colour)
        self += TextFrame(self, text=start_text, colour='mid', align=Centred, update_fn=self.update_text, scalers=(0.7,0.7))

    def update_text(self, media=None):
        if media is not None:
            duration = media.duration
        else:
            duration = getattr(self.platform, "duration", 0.0) or 0.0

        minutes = int(duration // 60)
        seconds = int(duration % 60)
        return f"{minutes:d}:{seconds:02d}"

    def update_screen(self, audio=None, media=None):
        self.update_text(media)

'''
Control, Source & Quality metadata
- Volume
- Source
- Quality
'''

class MetaData(TextFrame):
    def __init__(self, parent, metadata_type="artist", justify=("centre", "middle"), **kwargs):
        self.metadata_key = str(metadata_type)

        def _resolver(media=None):
            if media is not None:
                return str(getattr(media, self.metadata_key, ""))
            # Fallback to platform
            return str(getattr(parent.platform, self.metadata_key, ""))

        super().__init__(
            parent,
            update_fn=_resolver,
            justify=justify,
            **kwargs
        )
class MetaDataFrame(Frame):
    SHOW = { 'track' : {'colour' : 'foreground', 'align': ('left','middle'), 'scalers': (1.0, 1.0)}, \
             'album' : {'colour' : 'mid',        'align': ('left','middle'), 'scalers': (1.0, 0.8)},  \
             'artist': {'colour' : 'mid',        'align': ('left','middle'), 'scalers': (1.0, 0.8) } }
             

    OUTLINE = { 'width' : 1, 'radius' : 0, 'colour' : 'dark'}

    def __init__(self, parent, tip=False, justify=('centre','middle'), **kwargs):
        super().__init__(parent, **kwargs)
        self.justify = justify

        OUT = None
        rows  = RowFramer(self, padding=0.00, row_ratios=(1.5,1,1,0.5),padpc=0.3     )
        rows += MetaData(rows, 'track', justify=self.justify,  colour  = 'foreground')
        rows += MetaData(rows, 'album', justify=self.justify,  colour  = 'light')
        rows += MetaData(rows, 'artist', justify=self.justify, colour  = 'light') 
        rows += PlayProgressFrame(rows,background=None, outline=OUT)

    def update_screen(self, audio=None, media=None):
        self.draw_outline()
        self.draw_background()

        draw_list = sorted(self.frames, key=lambda x: getattr(x, "z_order", 0))
        for f in draw_list:
            f.draw_outline()
            f.draw_background()
            f.update_screen(audio=audio, media=media)
        return True
'''
Image based meta data frames
'''

class ArtFrame(Frame):
    # OUTLINE = { 'width' : 3, 'radius' : 0, 'colour_index' : 'foreground'}
    # def __init__(self, parent, update_fn=None, square=False, scalers=None, align=None, opacity=None, outline=None, padding=0, background=None):
    def __init__(self, parent, update_fn=None, opacity=150, reflection=None, **kwargs):

        # Frame.__init__(self, parent, scalers=scalers, align=align, outline=outline, padding=padding, background=background, square=square)
        self.kwargs    = kwargs
        self.parent    = parent
        self.update_fn = update_fn
        self.opacity   = opacity 
        self.reflection = reflection
        Frame.__init__(self, parent, **kwargs)
        # print("ArtFrame", square, opacity)
        self.configure()

    def configure(self):    
        self.image_container = Image(self, opacity=self.opacity, reflection=self.reflection)  

    def update_screen(self, audio=None, media=None):
        art_ref = None
        if media is not None:
            if self.is_album:
                art_ref = media.album_art
            else:
                art_ref = media.artist_art
        
        if art_ref is None and self.update_fn is not None:
            art_ref = self.update_fn()

        self.image_container.draw(art_ref)
        return True
 

class MetaImages(ArtFrame):
    def __init__(self, parent, art_type='album', opacity=1.0, reflection=None, **kwargs):

        VALID_ART_TYPES = {'album', 'artist'}

        if art_type in VALID_ART_TYPES: 
            # Dynamically construct the property name: 'album_art' or 'artist_art'
            attr_name = f"{art_type}_art"
            
            # Determine if it should be square based on the art_type
            is_square = (art_type == 'album')

            # The lambda fetches the *current* image/art at the time it is called
            ArtFrame.__init__(
                self, 
                parent, 
                update_fn=lambda *args: getattr(parent.platform, attr_name), 
                opacity=opacity * 255, 
                reflection=reflection, 
                square=is_square,  
                **kwargs
            ) 
        else:
            raise ValueError(f"MetaImages.__init__> Meta art type not known: {art_type}")
