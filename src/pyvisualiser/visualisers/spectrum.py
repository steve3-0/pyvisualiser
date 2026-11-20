#!/usr/bin/env python
"""
 Display classes:
    - base screens
    - screen frames
    - sub-frames

 Part of mVista preDAC

 v1.0 Baloothebear4 Sept 17 - Original
 v2.0 Baloothebear4  May 20 - Re-factored to use Frame class, simplifying & cleaning up
 v3.0 Baloothebear4 Dec 23 - Refactored for MacOS & DSI Display usage

"""
# from pyparsing import Optional
from typing import Optional

from pyvisualiser.core.framecore  import Frame, Smoother, RowFramer, ColFramer
from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.components import Bar, Text, Line, Box, Image, ArcsOctaves, BarStyle, SpectrumStyle
from pyvisualiser.styles.presets  import PI, Centred
from pyvisualiser.styles.styles   import MeterBallistics
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.ballistics import FFTBallistics
from pyvisualiser.core.state import AudioSnapshot
from pyvisualiser.core.base_defs import Channel, Orientation



"""
Spectrum Analyser Frames
"""
class Spectrum:
    """Calculates octave-band frequency distribution, temporal smoothing, and peak hold."""

    def __init__(
        self,
        width,
        barsize_pc=0.5,
        barw_min=1,
        barw_max=20,
        bandwidth=None,
        decay=0.4,
        ballistics: Optional[FFTBallistics] = None,
        platform=None
    ):
        self.barsize_pc = barsize_pc
        self.barw_min = barw_min
        self.barw_max = barw_max
        if platform is not None:
            self.platform = platform

        # 1. Resolve ballistics (Bridge layer)
        if ballistics is not None:
            self.ballistics = ballistics
        else:
            self.ballistics = FFTBallistics(decay_rate=decay)

        # 2. Calculate how many bars can be drawn in the width available
        barw = self.barw_min
        for self.spacing in (48, 24, 12, 6, 3, 2, 1):
            if hasattr(self, 'platform') and self.platform is not None:
                self.bar_freqs = self.platform.createBands(self.spacing, flast=bandwidth)
            else:
                self.bar_freqs = [100.0 * (i + 1) for i in range(24)]

            self.bars = len(self.bar_freqs)
            for barw in range(self.barw_max, self.barw_min, -1):
                self.bar_gap = int(barw * self.barsize_pc)
                self.max_bars = int(width / (self.bar_gap + barw))
                if self.bars <= self.max_bars:
                    break
            if self.bars <= self.max_bars:
                break

        self.barw = barw
        spectrum_width = self.bars * (self.bar_gap + self.barw)
        if spectrum_width < width:
            gaptofill = width - spectrum_width
            self.bar_gap = self.bar_gap + gaptofill / self.bars

        # 3. Always initialize dynamics arrays
        self.peaks = [0.0] * self.bars
        self.peak_hold_counters = [0] * self.bars
        self.current = [Smoother(1.0, 5) for _ in range(self.bars)]

        # 4. Count octaves
        self.octaves = [0]
        for freq_bin in range(1, len(self.bar_freqs)):
            if self.bar_freqs[freq_bin] >= 2 * self.bar_freqs[self.octaves[-1]]:
                if freq_bin - self.octaves[-1] < 12:
                    continue
                else:
                    self.octaves.append(freq_bin)

    def read(self, channel='left', audio_snapshot: Optional[AudioSnapshot] = None):
        """
        Updates frequency bins and peaks with temporal ballistics.
        Accepts optional AudioSnapshot; falls back to self.platform.packFFT.
        """
        if audio_snapshot is not None:
            # If bins are pre-packed in snapshot or we pack them
            fft = self.platform.packFFT(self.bar_freqs, channel)
        else:
            fft = self.platform.packFFT(self.bar_freqs, channel)

        smoothed_peak = 0.0

        for i, target_height in enumerate(fft):
            smoothed_val = self.current[i].smoothed()

            # 1. Rising or sustained signal tracking
            if target_height >= smoothed_val:
                self.current[i].add(target_height)
            else:
                # 2. Falling response (exponential decay)
                decay_step = smoothed_val * (1.0 - self.ballistics.decay_rate)
                if decay_step < (self.ballistics.decay_rate / 100.0):
                    self.current[i].add(0.0)
                else:
                    self.current[i].add(decay_step)

            height = self.current[i].smoothed()
            if height > smoothed_peak:
                smoothed_peak = height

            # 3. Peak hold & release dynamics
            if height >= self.peaks[i]:
                self.peaks[i] = height
                # FFT peak hold window (e.g. 15 frames)
                self.peak_hold_counters[i] = 15
            else:
                if self.peak_hold_counters[i] > 0:
                    self.peak_hold_counters[i] -= 1
                else:
                    self.peaks[i] *= (1.0 - self.ballistics.peak_decay_rate)

            # Reset peak if signal drops near zero
            if height < (self.ballistics.decay_rate / 3.0):
                self.peaks[i] = 0.0

        return smoothed_peak

        # print("Spectrum.read> ", self.current[i].__str__())

class SpectrumFrame(Frame, Spectrum):
    def __init__(
        self,
        parent,
        channel=Channel.MONO,
        # bar_style=None,
        spectrum_style=None,
        ballistics: Optional[FFTBallistics] = None,
        config: Optional[FrameConfig] = None,
        **kwargs
    ):
        self.channel = str(channel)
        self.ballistics = ballistics
        self.bar_style = spectrum_style.bar_style if spectrum_style and hasattr(spectrum_style, 'bar_style') else BarStyle()
        self.spectrum_style = spectrum_style if spectrum_style is not None else SpectrumStyle()

        Frame.__init__(
            self,
            parent,
            config=config

        )
        self.configure()

    def configure(self):
        spectrum_w, spectrum_h = self.abs_wh

        # Initialize Spectrum ballistics and band spacing
        Spectrum.__init__(
            self,
            spectrum_w,
            barsize_pc=getattr(self.bar_style, 'barsize_pc', self.spectrum_style.barsize_pc),
            barw_min=self.spectrum_style.barw_min,
            barw_max=self.spectrum_style.barw_max,
            decay=self.spectrum_style.decay,
            ballistics=self.ballistics,
            platform=self.platform
        )

        # Create the Bar component using newly calculated dimensions
        self.bar = Bar(
            self,
            box_size=(self.width, spectrum_h),
            bar_style=self.bar_style
        )

    def update_screen(self, audio=None, media=None):
        self.read(self.channel, audio_snapshot=audio)

        is_flipped = getattr(self.spectrum_style, 'flip', False)
        col_mode = getattr(self.bar_style, 'colour_mode', 'horz')
        right_offset = getattr(self.bar_style, 'right_offset', 0)

        if is_flipped:
            for i, item in enumerate(reversed(self.current)):
                x = i * (self.barw + self.bar_gap)
                colour_index = x if col_mode == 'horz' else None
                peak_val = self.peaks[len(self.current) - 1 - i]
                self.bar.draw(
                    x + right_offset,
                    item.smoothed(),
                    self.barw,
                    peak_val,
                    colour_index=colour_index
                )
        else:
            for i in range(len(self.current)):
                x = i * (self.barw + self.bar_gap)
                colour_index = x if col_mode == 'horz' else None
                self.bar.draw(
                    x + right_offset,
                    self.current[i].smoothed(),
                    self.barw,
                    self.peaks[i],
                    colour_index=colour_index
                )
        return True
        

    @property
    def width(self):
        return self.bars * (self.bar_gap+self.barw)



""" A visualiser based on a circle display of spectrum lines """
class Diamondiser(Frame, Spectrum):
    BARSPACE = 1
    def __init__(self, parent, channel, scalers=None, theme=None, align=None, barsize_pc=BARSPACE,background=None, z_order=0, **kwargs):
        Frame.__init__(self, parent, scalers=scalers, align=align, square=True, theme=theme,background=background, z_order=z_order)
        self.channel     = channel
        self.barsize_pc   = barsize_pc
        self.configure()

    def configure(self):
        Spectrum.__init__(self, self.w, barsize_pc=self.barsize_pc, bandwidth=8000, decay=0.5)
        # self.VU          = VU(self.platform, channel, decay=0.2)
        self.max_radius  = self.h/2
        self.ray_angle   = 1/self.bars
        self.centre_pc   = 0.8

        self.rays        = [Line(self, endstops=(PI/2, 5*PI/2), width=self.barsize_pc*2, tick_pc=self.centre_pc, centre_offset=0, \
                            radius=self.max_radius, colour='mid') \
                             for _ in range(self.bars)]

    def update_screen(self):
        self.read(self.channel)
        radius  = self.centre_pc

        for ray_index, ray in enumerate(self.rays):
            col = self.max_radius*(ray_index/self.bars)
            amp = radius*self.current[ray_index].smoothed() if self.current[ray_index].smoothed() > 0 else 0
            ray.drawFrameCentredVector(ray_index*self.ray_angle, amplitude=amp, gain=1-radius, colour=col)


class Octaviser(Frame, Spectrum):
    def __init__(self, parent, channel, scalers=None, align=('left', 'bottom'), theme=None):
        self.channel = channel
        Frame.__init__(self, parent, scalers=scalers, align=align)
        self.configure()

    def configure(self):
        Spectrum.__init__(self, self.w, barsize_pc=5)
        self.num_octaves=len(self.octaves)
        self.arcs = ArcsOctaves(self.parent, theme='rainbow', NumOcts=self.num_octaves)

    def update_screen(self):
        fft = self.read(self.channel)

        for octave in range(1, self.num_octaves):
            self.arcs.draw(octave, fft[self.octaves[octave-1]:self.octaves[octave]])
            # print(bin, self.octaves[octave]) #, fft[bin:self.octaves[octave]])

        


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
                              spectrum_style=SpectrumStyle(barw_min=10, barsize_pc=0.4,flip=True, bar_style=bar) )
        col += SpectrumFrame(col, 'right', config=FrameConfig(theme='rainbow', background=None),
                               spectrum_style=SpectrumStyle(barw_min=10, barsize_pc=0.4, bar_style=bar)  )        

class SpectrumStereoLRFrame(Frame): #""" Horz Split screen - LED Style right flipped  """
    # THis is vertically aligned, with one flipped
    def __init__(self, parent, scalers, align) :
        Frame.__init__(self, parent, scalers=scalers, align=align)
        bar=BarStyle(flip=True, led_gap=1, peak_h=1, radius=2)
        self += SpectrumFrame(self, 'right', config=FrameConfig(scalers=(1.0, 0.5), align=('left','top')    ), spectrum_style=SpectrumStyle(barw_min=12, bar_style=bar), theme='white' )
        self += SpectrumFrame(self, 'left', config=FrameConfig(scalers=(1.0, 0.5), align=('left','bottom')) , spectrum_style=SpectrumStyle(barw_min=12, bar_style=bar), theme='red' )
        

class SpectrumStereoSplitFrame(Frame): #""" Horz Split screen - right flipped """
    # This is vertically aligned
    def __init__(self, parent, scalers=None, align=None, config=None) :
        Frame.__init__(self, parent, config=config,scalers=scalers, align=align)
        rows = RowFramer(self)
        bar_style=BarStyle(led_gap=0, flip=False, tip=True)
        rows += SpectrumFrame(rows, 'right', config=FrameConfig(scalers=(1.0, 0.5), align=('left','top')    ), spectrum_style=SpectrumStyle(barw_min=5, barsize_pc=0.5, bar_style=bar_style) )
        bar_style=BarStyle(led_gap=0, flip=True, tip=True)
        rows += SpectrumFrame(self, 'left', config=FrameConfig(scalers=(1.0, 0.5), align=('left','bottom')) ,  spectrum_style=SpectrumStyle(barw_min=5, barsize_pc=0.5, bar_style=bar_style) )
        

class SpectrumStereoOffsetFrame(Frame):
    def __init__(self, parent, config=None,scalers=None, align=None) :
        Frame.__init__(self, parent, config=config, scalers=scalers, align=align)
        self += SpectrumFrame(self, 'right', config=FrameConfig(scalers=(1.0, 1.0), align=('left','top'), theme='red', background=None),   
                              spectrum_style=SpectrumStyle(barw_min=8, barsize_pc=1.5, 
                                    bar_style=BarStyle(led_gap=0, tip=True,right_offset=2,),))
        self += SpectrumFrame(self, 'left', config=FrameConfig(scalers=(1.0, 1.0), align=('left','bottom'),theme='blue',background=None), 
                              spectrum_style=SpectrumStyle(barw_min=8, barsize_pc=1.5, bar_style=BarStyle(led_gap=0, tip=True) )  )


class StereoSpectrumFrame(Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self += SpectrumFrame(self,  'right', config=FrameConfig(scalers=(1.0, 0.5), align=('left','top')), 
                              spectrum_style=SpectrumStyle(barw_min=15, barsize_pc=0.5, 
                              bar_style=BarStyle(led_gap=5, peak_h=3, radius=0 )), **kwargs)
        self += SpectrumFrame(self,  'left', config=FrameConfig(scalers=(1.0, 0.5), align=('left','bottom')) , 
                              spectrum_style=SpectrumStyle(barw_min=15, barsize_pc=0.5, 
                              bar_style=BarStyle(led_gap=5, peak_h=3, radius=0)), **kwargs )


