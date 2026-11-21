'''
Analogue VU meters have image based background and scale based background.  The rendering and light effects are  cruicial to get 
a good simulation of Analogue VU meters

Mar 2026 Baloothebear4. v1.0
- refectored from frames.py and subframes.py

'''

from    pyvisualiser.core.framecore  import Frame, get_asset_path, Smoother, RowFramer, ColFramer
from    pyvisualiser.core.components import Text, Line, Image, Bar
from    pyvisualiser.core.state      import AudioSnapshot
from    pyvisualiser.core.frame_config import FrameConfig, Centred, PI
from    pyvisualiser.core.base_defs  import Channel

from    pyvisualiser.styles.styles   import *
from    pyvisualiser.styles.profiles import ProfileManager
from    pyvisualiser.styles.ballistics import MeterBallistics
from    pyvisualiser.visualisers.metadata   import TextFrame


class VU:
    """Calculates instantaneous audio level, smoothed ballistics, and floating peaks."""

    def __init__(
        self,
        platform,
        channel: str,
        decay: float = 0.3,
        smooth: int = 8,
        ballistics: Optional[MeterBallistics] = None
    ):
        self.platform = platform
        self.channel = str(channel)

        if ballistics is not None:
            self.ballistics = ballistics
        else:
            self.ballistics = MeterBallistics(
                decay_rate=decay,
                smoothing_samples=smooth
            )

        self.current = Smoother(1.0, self.ballistics.smoothing_samples)
        self.peaks = 0.0
        self.peak_hold_counter = 0

    def read(self, audio_snapshot: Optional[AudioSnapshot] = None) -> tuple[float, float]:
        """
        Calculates instantaneous ballistic deflection and peak values.
        Accepts optional AudioSnapshot; falls back to self.platform.vu if omitted.
        """
        if audio_snapshot is not None:
            target_height = audio_snapshot.get_vu(self.channel)
        else:
            target_height = self.platform.vu.get(self.channel, self.platform.vu.get('mono', 0.0))

        smoothed_val = self.current.smoothed()

        # 1. Rising or sustained signal tracking
        if target_height >= smoothed_val:
            self.current.add(target_height)
        else:
            # Falling response (exponential decay)
            decay_step = smoothed_val * (1.0 - self.ballistics.decay_rate)
            if decay_step < (self.ballistics.decay_rate / 100.0):
                self.current.add(0.0)
            else:
                self.current.add(decay_step)

        height = self.current.smoothed()

        # 2. Peak hold tracking: keep hold counter fully charged on sustained peaks
        if height >= self.peaks:
            self.peaks = height
            self.peak_hold_counter = self.ballistics.peak_hold_frames
        else:
            # Fall-off phase: count down hold window before releasing peak
            if self.peak_hold_counter > 0:
                self.peak_hold_counter -= 1
            else:
                self.peaks *= (1.0 - self.ballistics.peak_decay_rate)

        if height < (self.ballistics.decay_rate / 3.0):
            self.peaks = 0.0

        return height, self.peaks

"""
Analogue VU Meter frames
"""
class VUMeter(Frame):
    def __init__(
        self,
        parent,
        channel: Channel | str = Channel.LEFT,
        config: Optional[FrameConfig] = None,
        visuals: Optional[VUMeterStyle] = None,
        ballistics: Optional[MeterBallistics] = None
    ):
        self.channel = Channel.from_str(str(channel))
        self.ballistics = ballistics

        profile = ProfileManager.get_profile()
        self.style = visuals if visuals is not None else profile.get_style('vu_meter')
        if self.style is None:
            self.style = VUMeterStyle()

        # resolved_config = config if config is not None else FrameConfig(theme=self.style.theme)
        super().__init__(parent, config=config)
        self.configure()

    def configure(self):
        self.shape = self.abs_wh
        
        radius = self.abs_h * (0.5 - self.style.pivot)
        self.anglescale(radius, self.style.endstops, self.style.pivot)

        if self.style.texture_path is not None:
            self.path = get_asset_path('VU Images', self.style.texture_path)
            self.bgdimage = Image(self, align=('centre', 'middle'), path=self.path, outline=self.config.outline, opacity=int(self.style.texture_opacity * 255))
        else:
            self.path = None
            current_marks = self.style.scale.marks if self.style.scale and self.style.scale.marks is not None else {}
            current_arcs = self.style.scale.arcs if self.style.scale and self.style.scale.arcs is not None else {}
            current_annotate = self.style.scale.annotate if self.style.scale and self.style.scale.annotate is not None else {}

            self.scales = {
                mark: Text(self, text=current_marks[mark]['text'], 
                               colour=current_marks[mark]['colour'],
                               fontmax=self.abs_h * self.style.scale.font_height,
                               endstops=self.style.endstops,
                               centre_offset=self.style.pivot,
                               radius=radius * self.style.scale.scale_radius,
                               reset=False)
                for mark in current_marks
            }
            
            if current_annotate and current_annotate.get('text'):
                self.dB = Text(self, fontmax=self.abs_h * self.style.scale.font_height * 2,
                               text=current_annotate.get('text', ''),
                               justify=('centre', current_annotate.get('Valign', 'middle')),
                               colour=current_annotate.get('colour', 'mid'),
                               reset=True)
            else:
                self.dB = None
            
            self.ticks = Line(self, width=self.style.scale.tick_width, endstops=self.style.endstops, colour=self.style.scale.tick_colour,
                              tick_pc=self.style.scale.tick_radius_pc, centre_offset=self.style.pivot, 
                              radius=radius * self.style.scale.tick_length)
            
            self.arclines = []
            if current_arcs:
                for rad_pc, arc in current_arcs.items():
                    self.arclines.append(
                        Line(self, width=arc['width'], colour=arc['colour'],
                             endstops=self.style.endstops, tick_pc=self.style.scale.tick_radius_pc,
                             centre_offset=self.style.pivot, radius=radius * rad_pc)
                    )

        effective_ballistics = self.ballistics if self.ballistics is not None else MeterBallistics(
            decay_rate=self.style.decay,
            smoothing_samples=self.style.smooth
        )

        self.VU = VU(
            self.platform,
            self.channel,
            ballistics=effective_ballistics
        )
        
        self.needle = Line(self, width=self.style.needle.width, tick_pc=self.style.needle.radius_pc, 
                           centre_offset=self.style.pivot, endstops=self.style.endstops, 
                           radius=radius * self.style.needle.length, 
                           colour=self.style.needle.colour)
        
        self.peak = Line(self, width=self.style.needle.width, tick_pc=self.style.needle.radius_pc, 
                         centre_offset=self.style.pivot, endstops=self.style.endstops, 
                         radius=radius * self.style.needle.length, 
                         colour='alert')

    def update_screen(self):
        # self.draw_background(True)
        if self.path is None:
            self.drawVUBackground()
        else:
            self.bgdimage.draw()
        self.drawNeedle()
        return True
        

    def drawVUBackground(self):
        # Optimization: Group draw calls to batch geometry and reduce GPU flushes
        # 1. Draw all Lines (Ticks and Arcs) first
        current_marks = self.style.scale.marks if self.style.scale and self.style.scale.marks is not None else {}
        
        for val, mark in current_marks.items():
            self.ticks.drawFrameCentredVector(val, width=mark['width'])

        for arc in self.arclines:
            arc.drawFrameCentredArc(0)

        # 2. Draw all Text (Scales and dB) second
        if self.scales:
            for val, mark in current_marks.items():
                if val in self.scales:
                    self.scales[val].drawVectoredText(val, colour=mark['colour'])

        if self.dB:
            self.dB.draw()

    def drawNeedle(self):
        # print("VUeter._drawNeedle", self.framestr(), "\n", self.needle.framestr())
        vu, peaks   = self.VU.read()

        frame_rect = self.abs_rect()
        frame_bottom = frame_rect[1] + frame_rect[3]
        
        # 0. Draw Shadow
        if self.style.needle.shadow:
            xy = self.needle.anglexy(vu, self.needle.radius)
            ab = self.needle.anglexy(vu, self.needle.radius*(1-self.needle.tick_pc))
            
            # Offset shadow by 4 pixels
            offset = 5
            shadow_xy = (xy[0] + offset, xy[1] + offset)
            shadow_ab = (ab[0] + offset, ab[1] + offset)

            # Clip shadow base to frame boundary
            margin = self.style.needle.width / 2.0
            limit_y = frame_bottom - margin
            if shadow_ab[1] > limit_y:
                dy = shadow_xy[1] - shadow_ab[1]
                if abs(dy) > 0.1:
                    t = (limit_y - shadow_ab[1]) / dy
                    if 0 <= t <= 1:
                        shadow_ab = (shadow_ab[0] + t * (shadow_xy[0] - shadow_ab[0]), limit_y)
            
            if shadow_ab[1] <= limit_y:
                self.platform.renderer.draw_line((0, 0, 0, 100), shadow_ab, shadow_xy, width=self.style.needle.width, softness=1.0)

        # 1. Draw Glow (Behind)
        if self.style.needle.glow_intensity > 0:
            # Draw a tighter, controlled glow
            glow_opacity = int(255 * self.style.needle.glow_intensity)
            self.needle.drawFrameCentredVector(vu, colour=self.style.needle.glow_colour, 
                                               width=self.style.needle.width * 3, 
                                               softness=1.0, additive=True, opacity=glow_opacity)

        # 2. Draw Main Needle
        self.needle.drawFrameCentredVector(vu, softness=0.1)
        
        # 3. Draw Peak Needle
        if self.style.show_peak and peaks > 0: self.peak.drawFrameCentredVector(peaks)

        # 4. Draw Tip Glow (High Level)
        if self.style.needle.tip_glow and vu > 0.8:
            tip_xy = self.needle.anglexy(vu, self.needle.radius)
            col = self.colours.get(self.style.needle.glow_colour)
            # Draw a small glowing dot at the tip
            self.platform.renderer.draw_rect(col, (tip_xy[0]-6, tip_xy[1]-6, 12, 12), border_radius=6, softness=1.0, additive=True)

        # 5. Draw Pivot Cover
        if self.style.pivotcoverpc > 0:
            radius = self.abs_h * (0.5 - self.style.pivot)
            pc_radius = radius * self.style.pivotcoverpc
            cx, cy = self.abs_centre()

            # 1. Calculate 3D Depth Colors
            base_rgb = self.colours.get_rgb(self.style.pivotcovercolour)
            opacity = int(self.style.pivotcoveropacity * 255)
            
            # Create highlight and shadow versions for a dome effect
            col_light = [min(255, int(c * 1.4 + 30)) for c in base_rgb] + [opacity]
            col_dark  = [int(c * 0.6) for c in base_rgb] + [opacity]

            # Clipping logic to stay within frame bounds
            rect_y_start = cy - pc_radius
            rect_height = pc_radius * 2
            
            # Calculate clipping level (0.0 to 1.0) to hide anything below the frame bottom
            level = (frame_bottom - rect_y_start) / rect_height
            if level > 0:
                rect = (cx - pc_radius, rect_y_start, pc_radius * 2, rect_height)
                
                # 1.5. Draw Drop Shadow (Beneath the cover, above the needle)
                shadow_offset = 4
                shadow_rect = (cx - pc_radius + shadow_offset, rect_y_start + shadow_offset, pc_radius * 2, rect_height)
                shadow_level = (frame_bottom - shadow_rect[1]) / shadow_rect[3]
                if shadow_level > 0:
                    shadow_col = (0, 0, 0, int(100 * self.style.pivotcoveropacity))
                    self.platform.renderer.draw_rect(shadow_col, shadow_rect, border_radius=pc_radius, 
                                                     softness=0.8, level=min(1.0, shadow_level), axis=1.0)

                # 2. Draw Base Dome (with vertical depth gradient)
                self.platform.renderer.draw_rect(col_light, rect, border_radius=pc_radius, 
                                                 level=min(1.0, level), axis=1.0, 
                                                 gradient=(col_light, col_dark))
                
                # 2.5. Draw Metallic Rim (Outer Ring highlight)
                # rim_col = [min(255, int(c * 1.8 + 40)) for c in base_rgb] + [opacity]
                # self.platform.renderer.draw_rect(rim_col, rect, border_radius=pc_radius, 
                #                                  width=1, level=min(1.0, level), axis=1.0)
                
                # 3. Draw Specular Shine (Catch-light at the top-left)
                shine_r = pc_radius * 0.4
                shine_col = (255, 255, 255, int(160 * self.style.pivotcoveropacity))
                shine_rect = (cx - shine_r * 1.5, cy - pc_radius * 0.8, shine_r * 2, shine_r * 2)

                # Calculate clipping level for the shine specifically to respect frame boundaries
                shine_level = (frame_bottom - shine_rect[1]) / shine_rect[3]
                if shine_level > 0:
                    self.platform.renderer.draw_rect(shine_col, shine_rect, border_radius=shine_r, 
                                                     softness=0.4, additive=True, 
                                                     level=min(1.0, shine_level), axis=1.0)




""" Digital Bar VU"""
class VUFrame(Frame):
    def __init__(
        self,
        parent,
        channel: Channel | str = Channel.LEFT,
        config: Optional[FrameConfig] = None,
        visuals: Optional[BarStyle] = None,
        ballistics: Optional[MeterBallistics] = None
    ):
        self.channel = Channel.from_str(str(channel))
        self.ballistics = ballistics
        self.bar_style = visuals if visuals is not None else BarStyle()

        # resolved_config = config if config is not None else FrameConfig()
        super().__init__(parent, config=config)
        self.configure()

    def configure(self):
        box = (self.abs_w * self.bar_style.barsize_pc, self.abs_h) if self.bar_style.orient == 'vert' else (self.abs_w, self.abs_h * self.bar_style.barsize_pc)
        # self.bar = Bar(self, align=('centre', 'middle'), box_size=box, bar_style=self.bar_style)
        self.bar = Bar(self, config=FrameConfig(align=('centre', 'middle')), box_size=box, bar_style=self.bar_style)
        effective_ballistics = self.ballistics if self.ballistics is not None else MeterBallistics()
        self.VU = VU(self.platform, self.channel, ballistics=effective_ballistics)

    def update_screen(self, audio=None, media=None):
        height, peaks = self.VU.read(audio_snapshot=audio)
        self.bar.draw(0, height, self.barw if hasattr(self, 'barw') else self.w, peaks)
        return True
    


""" Complex VU Meters""" 


class VUMeterImageFrame(Frame):
    """ Image background based class - the """
    def __init__(self, parent, type=None, config:Optional[FrameConfig]=None):

        Frame.__init__(self, parent, config=config)

        NEEDLE      = VUNeedleStyle(colour='dark', width=4, length=0.7, radius_pc = 0.7)
                                    # { 'width':3, 'colour': 'dark', 'length': 0.7, 'radius_pc': 0.7 }
        NEEDLE2     = VUNeedleStyle(colour='mid', width=3, length=0.8, radius_pc = 0.55)
                            # { 'width':3, 'colour': 'mid', 'length': 0.8, 'radius_pc': 0.55 }
        NEEDLE3     = VUNeedleStyle(colour='foreground', width=3, length=0.7, radius_pc = 0.5)
                        # { 'width':3, 'colour': 'foreground', 'length': 0.7, 'radius_pc': 0.5 }
        NEEDLE4     = VUNeedleStyle(colour='alert', width=4, length=0.85, radius_pc = 0.75)
                        # { 'width':4, 'colour': 'alert', 'length': 0.85, 'radius_pc': 0.75 }

        ENDSTOPS    = (3*PI/4, 5*PI/4)
        METERS      = { 'blueVU' : VUMeterStyle(texture_path='blue-bgr.png', needle=NEEDLE, endstops=ENDSTOPS, pivot=-0.49),
                        'goldVU' : VUMeterStyle(texture_path='gold-bgr.png', needle=NEEDLE2, endstops=ENDSTOPS, pivot=-0.35),
                        'blackVU': VUMeterStyle(texture_path='black-white-bgr.png', needle=NEEDLE3, endstops=ENDSTOPS, pivot=-0.65),
                        'rainVU' : VUMeterStyle(texture_path='rainbow-bgr.png', needle=NEEDLE4, endstops=ENDSTOPS, pivot=-0.75),
                        'redVU'  : VUMeterStyle(texture_path='red-bgr.jpeg', needle=VUNeedleStyle(width=3, colour='dark', length=0.8, radius_pc=0.65), endstops=ENDSTOPS, pivot=-0.76),
                        'vintVU' : VUMeterStyle(texture_path='vintage-bgr.jpeg', needle=VUNeedleStyle(width=3, colour='alert', length=0.7, radius_pc=0.8), endstops=ENDSTOPS, pivot=-0.6),
                        'whiteVU': VUMeterStyle(texture_path='white-red-bgr.png', needle=VUNeedleStyle(width=2, colour='foreground', length=0.75, radius_pc=0.65), endstops=ENDSTOPS, pivot=-0.75),
                        'OldVU': VUMeterStyle(texture_path='vintage-VU.png', needle=VUNeedleStyle(width=3, colour='foreground', length=0.75, radius_pc=0.65), endstops=ENDSTOPS, pivot =-0.75),
                        'ModVU': VUMeterStyle(texture_path='modern-VU.png', needle=VUNeedleStyle(width=2, colour='foreground', length=0.75, radius_pc=0.65), endstops=ENDSTOPS, pivot=-0.75),
                        'greenVU': VUMeterStyle(texture_path='emerald-bgr.jpeg', needle=VUNeedleStyle(width=2, colour='foreground', length=0.63, radius_pc=0.60), endstops=ENDSTOPS, pivot=-0.6) }

        METERS_THEME = { 'blueVU' :  'blue',
                        'goldVU' :  'white',
                        'blackVU': 'meter1',
                        'rainVU' : 'meter1',
                        'redVU'  : 'meter1',
                        'vintVU' : 'meter1',
                        'whiteVU': 'meter1',
                        'OldVU': 'meter2',
                        'ModVU': 'meter1',
                        'greenVU': 'meter1'}

        # if the meter type does not exist then there will be a run time error
        # meter colour themes assume meter1
        style = METERS[type]
        theme = METERS_THEME[type]
        outline = OutlineStyle(width=4, radius=10, colour='light', glow_intensity=0.1, softness=0.2)
        cols = ColFramer(self, config=FrameConfig(padding=30), padpc=0.05)
        cols += VUMeter(cols, 'left', visuals=style, config=FrameConfig(outline=outline, theme=theme))
        cols += VUMeter(cols, 'right', visuals=style, config=FrameConfig(outline=outline, theme=theme)   ) 


class VU2chFrame(Frame):
    """Stereo dual-channel level bar meter."""
    def __init__(
        self,
        parent,
        config: Optional[FrameConfig] = None,
        visuals: Optional[BarStyle] = None,
        ballistics: Optional[MeterBallistics] = None
    ):
        resolved_config = config if config is not None else FrameConfig()
        super().__init__(parent, config=resolved_config)
        self.bar_style = visuals if visuals is not None else BarStyle()
        self.ballistics = ballistics
        self.configure()

    def configure(self):
        if self.bar_style.orient == 'horz':
            self += VUFrame(
                self,
                channel=Channel.LEFT,
                config=FrameConfig(scalers=(1.0, 0.5), align=('centre', 'top')),
                visuals=self.bar_style,
                ballistics=self.ballistics
            )
            self += VUFrame(
                self,
                channel=Channel.RIGHT,
                config=FrameConfig(scalers=(1.0, 0.5), align=('left', 'bottom')),
                visuals=self.bar_style,
                ballistics=self.ballistics
            )
        else:
            self += VUFrame(
                self,
                channel=Channel.LEFT,
                config=FrameConfig(scalers=(0.5, 1.0), align=('left', 'middle')),
                visuals=self.bar_style,
                ballistics=self.ballistics
            )
            self += VUFrame(
                self,
                channel=Channel.RIGHT,
                config=FrameConfig(scalers=(0.5, 1.0), align=('right', 'bottom')),
                visuals=self.bar_style,
                ballistics=self.ballistics
            )



class VUFlipFrame(Frame):
    """Stereo level bar meter where channels grow away from or towards each other."""
    def __init__(
        self,
        parent,
        config: Optional[FrameConfig] = None,
        visuals: Optional[BarStyle] = None,
        ballistics: Optional[MeterBallistics] = None,
        flip_order: tuple[bool, bool] = (True, False)
    ):
        resolved_config = config if config is not None else FrameConfig()
        super().__init__(parent, config=resolved_config)
        self.bar_style = visuals if visuals is not None else BarStyle()
        self.ballistics = ballistics
        self.flip_order = flip_order
        self.configure()

    def configure(self):
        import dataclasses
        from pyvisualiser.core.framecore import ColFramer, RowFramer

        flip_l, flip_r = self.flip_order
        style_l = dataclasses.replace(self.bar_style, flip=flip_l)
        style_r = dataclasses.replace(self.bar_style, flip=flip_r)

        if self.bar_style.orient == 'horz':
            cols = ColFramer(self, col_ratios=(1, 1), config=FrameConfig.default())
            cols += VUFrame(cols, channel=Channel.LEFT, visuals=style_l, ballistics=self.ballistics)
            cols += VUFrame(cols, channel=Channel.RIGHT, visuals=style_r, ballistics=self.ballistics)
        else:
            rows = RowFramer(self, row_ratios=(1, 1), config=FrameConfig.default())
            rows += VUFrame(rows, channel=Channel.LEFT, visuals=style_l, ballistics=self.ballistics)
            rows += VUFrame(rows, channel=Channel.RIGHT, visuals=style_r, ballistics=self.ballistics)

# from dataclasses import dataclass, replace
# class VUHorzFrame(Frame):
#     def __init__(self, parent, channel, visuals=None):


#         Frame.__init__(self, parent)
#         cols = ColFramer(self, col_ratios=(1,3))
#         # cols = self
#         channel_text = ' L' if channel=='left' else ' R'
#         cols += TextFrame(cols, text=channel_text)
  
#         style=visuals replace(orient='horz')
#         cols += VUFrame(cols, channel=channel, visuals=style)

from typing import Optional
from dataclasses import replace
from pyvisualiser.core.base_defs import Channel, HorizontalAlign, VerticalAlign
class VUHorzFrame(Frame):
    """Horizontal stereo/mono channel meter row with a channel label prefix."""
    def __init__(
        self,
        parent,
        channel: Channel | str = Channel.LEFT,
        config: Optional[FrameConfig] = None,
        visuals: Optional[BarStyle] = None
    ):
        super().__init__(parent, config=config or FrameConfig())
        self.channel = Channel.from_str(str(channel))
        
        # Ensure the passed BarStyle is configured for horizontal orientation
        base_bar_style = visuals if visuals is not None else BarStyle()
        self.bar_style = replace(base_bar_style, orient='horz')
        
        self.configure()

    def configure(self):
        # Use fluent add_cols helper (ColFramer with ratios 1:3 for label vs bar)
        cols = self.add_cols(ratios=(1, 3), padpc=0.0, config=FrameConfig(padding=0))

        channel_text = ' L' if self.channel == Channel.LEFT else ' R'
        
        # Add channel text label
        cols += TextFrame(
            cols,
            text=channel_text,
            config=FrameConfig(align=(HorizontalAlign.CENTRE, VerticalAlign.MIDDLE)),
            visuals=TextStyle(colour='light')
        )
        cols += VUFrame(cols, channel=self.channel, visuals=self.bar_style)

class VU2chHorzFrame(Frame):
    def __init__(self, parent, tip=False, config=None, visuals=None):
        # Pass the FrameConfig object directly to the parent Frame constructor 
        # using your existing bridge layer (config=frameconfig)
        super().__init__(parent, config=config)

        # Pass style, tip, and component-specific arguments down to the subframes
        rows = RowFramer(self)
        rows += VUHorzFrame(rows, 'left', visuals=visuals)
        rows += VUHorzFrame(rows, 'right', visuals=visuals)
        # self += VUFrame(self, channel='left', visuals=visuals)