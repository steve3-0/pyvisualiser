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

from collections.abc import Callable
from typing import Optional, Union, Tuple, Dict, Any
from dataclasses import replace

from    pyvisualiser.core.framecore  import Frame, RowFramer, ColFramer, get_asset_path, Smoother
from    pyvisualiser.core.components import Line, Box, Image, Text
from    pyvisualiser.visualisers.text import TextFrame
from    pyvisualiser.visualisers.playprogress import PlayProgressFrame
from    pyvisualiser.core.frame_config import FrameConfig, Centred, FullScale, PI   
from    pyvisualiser.styles.styles import TextStyle, PlayProgressStyle, ImageStyle, BarStyle, ShaderStyle
from    pyvisualiser.styles.profiles import ProfileManager
from    pyvisualiser.core.base_defs  import *
from    pyvisualiser.core.state import MediaSnapshot


""" Text based frames for displaying metadata such as track title, album, artist, and play progress."""
class TextFrame(Frame):
    def __init__(
        self,
        parent,
        text: str = "Default Text",
        config: Optional[FrameConfig] = None,
        visuals: Optional[TextStyle] = None,
        update_fn: Optional[Callable[..., str]] = None
    ):
        self.text = text
        self.update_fn = update_fn
        self.style = visuals if visuals is not None else TextStyle()

        resolved_config = config if config is not None else FrameConfig()
        super().__init__(parent, config=resolved_config)
        self.configure()

    def configure(self):
        self.textcomp = Text(
            self,
            text=self.text,
            fontmax=self.style.font_size or self.h,
            reset=True,
            colour=self.style.colour,
            wrap=self.style.wrap,
            justify=self.style.justify,
            z_order=self.z_order
        )

    def update_screen(self, text=None, colour=None, fontmax=None, audio=None, media=None):
        if text is None and self.update_fn is not None:
            try:
                text = self.update_fn(media)
            except TypeError:
                text = self.update_fn()
        elif text is None:
            text = self.text

        self.textcomp.draw(text=text, colour=colour or self.style.colour, fontmax=fontmax)
        return True


class MetaData(TextFrame):
    def __init__(
        self,
        parent,
        key: MetadataKey | str = MetadataKey.TRACK,
        config: Optional[FrameConfig] = None,
        visuals: Optional[TextStyle] = None
    ):
        self.metadata_key = str(key).lower()
        align = config.align if config is not None else Centred
        colour= visuals.colour if visuals is not None else 'mid'
        style = visuals if visuals is not None else TextStyle()
        style = TextStyle(justify=align, colour=colour)

        def _resolver(media=None):
            if media is not None:
                return str(getattr(media, self.metadata_key, ""))
            return str(getattr(parent.platform, self.metadata_key, ""))

        super().__init__(
            parent,
            text="",
            config=config,
            visuals=style,
            update_fn=_resolver
        )

class MetaDataFrame(Frame):
    """
    Structured multi-row container displaying Track Title, Album, Artist,
    and a PlayProgress bar in a clean vertical hierarchy.
    """
    def __init__(
        self,
        parent,
        justify='centre',
        config: Optional[FrameConfig] = None
    ):
        resolved_config = config if config is not None else parent.config
        super().__init__(parent, config=resolved_config)
        self.justify = justify

        self.configure()

    def configure(self):
        # Build 4-row stack: Track, Album, Artist, Progress Bar
        rows = RowFramer(self, row_ratios=(1.5, 1, 1, 1), padpc=0.3, config=FrameConfig(padding=0.0))
        rows += MetaData(rows, MetadataKey.TRACK,  visuals=TextStyle(colour='foreground', justify=self.justify))
        rows += MetaData(rows, MetadataKey.ALBUM,  visuals=TextStyle(colour='light', justify=self.justify))
        rows += MetaData(rows, MetadataKey.ARTIST, visuals=TextStyle(colour='light', justify=self.justify))

        rows += PlayProgressFrame(rows)


""" Play progress indicators frame for displaying elapsed and remaining time with a visual progress bar."""
# class PlayProgressFrame(Frame):
#     def __init__(
#         self,
#         parent,
#         config: Optional[FrameConfig] = None,
#         visuals: Optional[PlayProgressStyle] = None
#     ):
#         self.progress_style = visuals if visuals is not None else PlayProgressStyle()
#         self.bar_style = self.progress_style.bar_style
#         self.text_style = self.progress_style.text_style

#         resolved_config = config if config is not None else parent.config.change(z_order=10)
#         super().__init__(parent, config=resolved_config)
#         self.configure()

#     def configure(self):
#         self.barw = self.abs_w * self.progress_style.barsize_pc if self.bar_style.orient == 'vert' else self.abs_h * self.progress_style.barsize_pc

#         text_sample = " 22:22 "
#         self.elapsed = Text(self, fontmax=self.barw, text=text_sample, justify=('left', 'middle'), style=self.text_style, z_order=self.z_order + 1)
#         self.remaining = Text(self, fontmax=self.barw, text=text_sample, justify=('right', 'middle'), style=self.text_style, z_order=self.z_order + 1)
#         self.text_width = self.elapsed.fontwh[0] + self.remaining.fontwh[0]

#         box = (self.barw, self.h) if self.bar_style.orient == 'vert' else (self.w - self.text_width, self.barw)
#         config = self.config.change(align=('centre', 'middle'))
#         self.boxbar = Box(self, config=config , box=box, radius=self.bar_style.radius)

#     def update_screen(self, audio=None, media=None):
#         if media is not None:
#             elapsed_str = f"  {media.format_elapsed()}"
#             remaining_str = f"{media.format_remaining()}  "
#             elapsed_pc = media.elapsed_pc
#         else:
#             dur = getattr(self.platform, 'duration', 0.0) or 0.0
#             elap = getattr(self.platform, 'elapsed', 0.0) or 0.0
#             elapsed_str = f"  {int(elap // 60)}:{int(elap % 60):02d}"
#             remaining_str = f"{int(max(0.0, dur - elap) // 60)}:{int(max(0.0, dur - elap) % 60):02d}  "
#             elapsed_pc = (elap / dur) if dur > 0 else 0.0

#         box = (self.barw, self.h) if self.bar_style.orient == 'vert' else (self.w - self.text_width, self.barw)
#         if self.boxbar.wh != box:
#             self.boxbar.resize(box)

#         hide_backline = -self.h / 2 if elapsed_pc * self.w > self.h / 2 else 0
#         self.boxbar.drawH(elapsed_pc, flip=True, colour_index='dark', offset=(hide_backline, 0))
#         self.boxbar.drawH(elapsed_pc, colour_index='light')

#         self.elapsed.draw(elapsed_str, colour=self.text_style.colour)
#         self.remaining.draw(remaining_str, colour=self.text_style.colour)
#         return True


# class CircularProgress(Frame):
#     """Circular progress dial with centered timecode readout."""
#     @property
#     def title(self):
#         return 'GLSL Shader Test - Circular Progress'

#     @property
#     def type(self):
#         return 'Test'

#     def __init__(
#         self,
#         parent,
#         config: Optional[FrameConfig] = None,
#         colour: str = 'mid',
#         visuals: Optional[TextStyle] = None
#     ):
#         resolved_config = config if config is not None else FrameConfig(
#             theme='hifi',
#             padding=0,
#             square=True
#         )
#         super().__init__(parent, config=resolved_config)
#         self.colour = colour
#         self.text_style = visuals if visuals is not None else TextStyle(
#             colour='mid',
#             justify=('centre', 'middle')
#         )
#         self.configure()

#     def configure(self):
#         start_text = self.update_text()

#         self += ShaderFrame(
#             self,
#             shader='progressdial',
#             config=FrameConfig.default(),
#             visuals=ShaderStyle(shader_name='progressdial', colour=self.colour)
#         )
#         self += TextFrame(
#             self,
#             text=start_text,
#             config=FrameConfig(scalers=(0.7, 0.7), align=('centre', 'middle')),
#             visuals=self.text_style,
#             update_fn=self.update_text
#         )

#     def update_text(self, media=None):
#         if media is not None:
#             duration = media.duration
#         else:
#             duration = getattr(self.platform, 'duration', 0.0) or 0.0
#         minutes = int(duration // 60)
#         seconds = int(duration % 60)
#         return f"{minutes:d}:{seconds:02d}"

# class LinearProgress(Frame):
#     """Linear progress dial with timecode readout."""
#     @property
#     def title(self):
#         return ' Linear Progress pay bar'

#     @property
#     def type(self):
#         return 'Test'

#     def __init__(
#         self,
#         parent,
#         config: Optional[FrameConfig] = None,
#         colour: str = 'mid',
#         visuals: Optional[TextStyle] = None  # Need a ProgressStyle
#     ):
#         resolved_config = config if config is not None else FrameConfig(
#             theme='hifi',
#             padding=0,
#             square=True
#         )
#         super().__init__(parent, config=config)
#         self.colour = colour
#         self.text_style = visuals if visuals is not None else TextStyle(
#             colour='mid',
#             justify=('centre', 'middle')
#         )
#         self.configure()

#     def configure(self):
#         elapsed_str = "22:22"
#         remaining_str = "22:22"

#         cols = ColFramer(self, ratios=(1,5,1))
#         cols += TextFrame(cols,
#             text=elapsed_str,
#             config=FrameConfig(scalers=(0.7, 0.7), align=('right', 'middle')),visuals=self.text_style,
#             update_fn=self.update_elapsed
#         )
#         cols += ShaderFrame(cols, shader='linprogress', visuals=ShaderStyle(shader_name='linprogress', colour=self.colour))
#         cols += TextFrame(cols,
#             text=remaining_str,
#             config=FrameConfig(scalers=(0.7, 0.7), align=('right', 'middle')),visuals=self.text_style,
#             update_fn=self.update_remaining
#         )

#     # def update_screen(self, audio=None, media=None):
#     #     elapsed_str, remaining_str = self.update_text(media)

#     def update_elapsed(self):
#         elap = getattr(self.platform, 'elapsed', 0.0) or 0.0
#         elapsed_str = f"  {int(elap // 60)}:{int(elap % 60):02d}"
#         return elapsed_str

#     def update_remaining(self):
#         dur = getattr(self.platform, 'duration', 0.0) or 0.0
#         elap = getattr(self.platform, 'elapsed', 0.0) or 0.0
#         remaining_str = f"{int(max(0.0, dur - elap) // 60)}:{int(max(0.0, dur - elap) % 60):02d}  "
#         return remaining_str
'''
Image based meta data frames
'''

class ArtFrame(Frame):
    """
    Base container for rendering album art or artist photography
    with optional floor reflections and rounded corners.
    """
    def __init__(
        self,
        parent,
        update_fn: Optional[Callable[..., str]] = None,
        config: Optional[FrameConfig] = None,
        visuals: Optional[ImageStyle] = None
    ):
        self.update_fn = update_fn
        self.image_style = visuals if visuals is not None else ImageStyle()

        super().__init__(parent, config=config)
        self.configure()

    def configure(self):
        self.image_container = Image(
            self,
            opacity=self.image_style.opacity,
            reflection=self.image_style.reflection,
            default_image=self.image_style.default_texture
        )

    def update_screen(self, audio=None, media=None):
        art_ref = None
        if self.update_fn is not None:
            try:
                art_ref = self.update_fn(media)
            except TypeError:
                art_ref = self.update_fn()
        
        self.image_container.draw(art_ref)
        return True

class MetaImages(ArtFrame):
    def __init__(
        self,
        parent,
        key: MetadataKey | str = MetadataKey.ALBUM,
        config: Optional[FrameConfig] = None,
        visuals: Optional[ImageStyle] = None
    ):
        art_key = str(key).lower()
        attr_name = f"{'album' if 'album' in art_key else 'artist'}_art"
        is_square = 'album' in art_key

        self.image_style = visuals if visuals is not None else ImageStyle()
        resolved_config = config if config is not None else FrameConfig(square=is_square)
        resolved_config = resolved_config.change(square=is_square)

        ArtFrame.__init__(
            self,
            parent,
            update_fn=lambda *args: getattr(parent.platform, attr_name, None),
            visuals = self.image_style,
            config=resolved_config
        )


'''
Control, Source & Quality metadata
- Volume
- Source
- Quality
'''

# Not implemented yet - will be a set of icons for source, volume, and quality
 
