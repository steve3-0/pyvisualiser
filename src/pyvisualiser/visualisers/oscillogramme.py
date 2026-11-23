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



"""
Visualiser Frames create complex responses to the audio:
- concentric octaves
- oscilogrammes
- modulated lines and circles
- dots that move in accordance with bass and treble
- blended lines and circles moving in sympathy with music

"""

from    pyvisualiser.core.framecore  import Frame, Smoother
from    pyvisualiser.core.components import Bar, Text, Line, Box, Image, ArcsOctaves, BarEffects, BarStyle, SpectrumStyle
from    pyvisualiser.core.frame_config  import FrameConfig, PI, Centred
from    pyvisualiser.styles.styles   import OscillogrammeStyle, BarStyle
import numpy as np

"""
Visualiser classes for time-domain waveforms and oscillogrammes.
Part of pyvisualiser.
"""

from typing import Optional, Callable
from pyvisualiser.core.base_defs import Channel
from pyvisualiser.core.frame_config import FrameConfig
from pyvisualiser.core.framecore import Frame, Smoother
from pyvisualiser.core.components import Bar, Line
from pyvisualiser.styles.styles import OscillogrammeStyle, BarStyle


class OscilogrammeBar(Frame):
    """
    Displays vertical time-domain sample bars with decay dynamics,
    configured via OscillogrammeStyle (encapsulating BarStyle).
    """
    def __init__(
        self,
        parent,
        channel: Channel | str = Channel.MONO,
        config: Optional[FrameConfig] = None,
        visuals: Optional[OscillogrammeStyle] = None
    ):
        self.channel = Channel.from_str(str(channel))
        self.oscillograme = visuals if visuals is not None else OscillogrammeStyle()
        self.bar_style = self.oscillograme.bar_style

        resolved_config = config if config is not None else FrameConfig()
        super().__init__(parent, config=resolved_config)
        self.configure()

    def configure(self):
        for barw in range(self.oscillograme.barw_min, self.oscillograme.barw_max):
            self.bar_gap = int(barw * self.oscillograme.barsize_pc)
            self.bars = int(self.w / max(1, (self.bar_gap + barw)))
            if self.bars <= self.oscillograme.samplesperframe:
                break

        self.barw = barw
        self.reduce_by = max(1, 2 * self.oscillograme.samplesperframe // max(1, self.bars))

        oscillograme_width = self.bars * (self.bar_gap + self.barw)
        if oscillograme_width < self.w and self.bars > 0:
            gaptofill = self.w - oscillograme_width
            self.bar_gap = self.bar_gap + gaptofill / self.bars

        self.current = [Smoother(1.0) for _ in range(self.bars)]
        self.bar = Bar(self, box_size=(self.width, self.h), bar_style=self.bar_style)
        self.decay = self.oscillograme.decay

    @property
    def width(self):
        return self.bars * (self.bar_gap + self.barw)

    def update_screen(self, audio=None, media=None):
        if audio is not None and self.channel in audio.samples:
            raw = audio.samples[self.channel]
            normalised = raw / 32768.0
            end = self.reduce_by * (len(normalised) // self.reduce_by)
            if end > 0:
                reshaped = normalised[:end].reshape(-1, self.reduce_by)
                samples = (np.sqrt(np.mean(np.square(reshaped), axis=1)) / 0.2).tolist()
            else:
                samples = [0.0] * self.bars
        else:
            samples = self.platform.reduceSamples(self.channel, self.reduce_by)

        for i in range(min(self.bars, len(samples))):
            target_height = min(1.0, samples[i])
            smoothed_val = self.current[i].smoothed()

            if target_height >= smoothed_val:
                self.current[i].add(target_height)

            if smoothed_val < self.decay / 100.0:
                self.current[i].add(0.0)
            else:
                self.current[i].add(smoothed_val * (1.0 - self.decay))

            x = i * (self.barw + self.bar_gap)
            self.bar.draw(x, self.current[i].smoothed(), self.barw, colour_index=x)
        return True


class Oscilogramme(Frame):
    """
    Renders the continuous live modulated audio waveform line.
    """
    def __init__(
        self,
        parent,
        channel: Channel | str = Channel.MONO,
        config: Optional[FrameConfig] = None,
        visuals: Optional[OscillogrammeStyle] = None
    ):
        self.channel = Channel.from_str(str(channel))
        self.oscillograme = visuals if visuals is not None else OscillogrammeStyle()

        resolved_config = config if config is not None else FrameConfig(
            align=('left', 'bottom')
        )
        super().__init__(parent, config=resolved_config)
        self.configure()

    def configure(self):
        self.lines = Line(self, circle=False, amp_scale=0.6)
        self.resolution = 256

    def update_screen(self, audio=None, media=None):
        reduceby = max(1, self.platform.framesize // self.resolution)
        if audio is not None and self.channel in audio.samples:
            raw = audio.samples[self.channel]
            normalised = raw / 32768.0
            end = reduceby * (len(normalised) // reduceby)
            if end > 0:
                samples = (np.mean(normalised[:end].reshape(-1, reduceby), axis=1) / 0.2).tolist()
            else:
                samples = [0.0] * self.resolution
        else:
            samples = self.platform.reduceSamples(self.channel, reduceby, rms=False)

        self.lines.draw_mod_line(samples, colour='foreground')
        return True

class SamplesFrame(Frame):
    """
    Dual-channel flipped time-domain oscillogramme stack.
    """
    def __init__(
        self,
        parent,
        config: Optional[FrameConfig] = None,
        visuals: Optional[OscillogrammeStyle] = None
    ):
        resolved_config = config if config is not None else FrameConfig()
        super().__init__(parent, config=resolved_config)

        import dataclasses
        self.oscillograme = visuals if visuals is not None else OscillogrammeStyle()

        # self.oscillograme_l = dataclasses.replace(self.oscillograme, bar_style=dataclasses.replace(self.oscillograme.bar_style,bar_style=BarStyle(led_gap=0)))
        # self.oscillograme_r = dataclasses.replace(self.oscillograme, bar_style=dataclasses.replace(self.oscillograme.bar_style,bar_style=BarStyle(led_gap=0, flip=True, colour_mode='horz')))

        self.oscillograme_l = dataclasses.replace(
            self.oscillograme, 
            bar_style=dataclasses.replace(self.oscillograme.bar_style, led_gap=0)
        )
        
        self.oscillograme_r = dataclasses.replace(
            self.oscillograme, 
            bar_style=dataclasses.replace(self.oscillograme.bar_style, led_gap=0, flip=True, colour_mode='horz')
        )
        self.configure()

    def configure(self):
        self += OscilogrammeBar(
            self,
            channel=Channel.LEFT,
            config=FrameConfig(scalers=(1.0, 0.5), align=('left', 'top')),
            visuals=self.oscillograme_r

        )
        self += OscilogrammeBar(
            self,
            channel=Channel.RIGHT,
            config=FrameConfig(scalers=(1.0, 0.5), align=('left', 'bottom')),
            visuals=self.oscillograme_r,

        )
