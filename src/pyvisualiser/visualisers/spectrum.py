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
from pyvisualiser.core.frame_config import FrameConfig, PI, Centred
from pyvisualiser.core.components import Bar, Text, Line, Box, Image, ArcsOctaves, BarStyle, SpectrumStyle
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.ballistics import MeterBallistics, FFTBallistics
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
            self.ballistics = FFTBallistics()

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
        channel: Channel | str = Channel.MONO,
        config: Optional[FrameConfig] = None,
        visuals: Optional[SpectrumStyle] = None
    ):
        self.channel = Channel.from_str(str(channel))

        self.spectrum_style = visuals if visuals is not None else SpectrumStyle()
        self.bar_style = self.spectrum_style.bar_style

        resolved_config = config if config is not None else FrameConfig()

        Frame.__init__(self, parent, config=resolved_config)
        self.configure()

    def configure(self):
        spectrum_w, spectrum_h = self.abs_wh
        Spectrum.__init__(
            self,
            spectrum_w,
            barsize_pc=self.spectrum_style.barsize_pc,
            barw_min=self.spectrum_style.barw_min,
            barw_max=self.spectrum_style.barw_max,
            ballistics=self.spectrum_style.ballistics,
            platform=self.platform
        )
        self.bar = Bar(self, box_size=(self.width, spectrum_h), bar_style=self.bar_style)

    def update_screen(self, audio=None, media=None):
        self.read(self.channel, audio_snapshot=audio)

        is_flipped = getattr(self.spectrum_style, 'flip', False)
        col_mode = getattr(self.spectrum_style, 'colour_mode', 'vert')
        right_offset = getattr(self.bar_style, 'right_offset', 0)

        if is_flipped:
            n = len(self.current)
            for i, item in enumerate(reversed(self.current)):
                x = i * (self.barw + self.bar_gap)
                orig_idx = n - 1 - i
                orig_x = orig_idx * (self.barw + self.bar_gap)
                colour_index = orig_x if col_mode == 'horz' else None
                peak_val = self.peaks[orig_idx]
                self.bar.draw(x + right_offset, item.smoothed(), self.barw, peak_val, colour_index=colour_index)
        else:
            for i in range(len(self.current)):
                x = i * (self.barw + self.bar_gap)
                colour_index = 1000-x if col_mode == 'horz' else None
                self.bar.draw(x + right_offset, self.current[i].smoothed(), self.barw, self.peaks[i], colour_index=colour_index)
        return True
    
    @property
    def width(self):
        return self.bars * (self.bar_gap+self.barw)



""" A visualiser based on a circle display of spectrum lines """
class Diamondiser(Frame, Spectrum):
    """Circular radial spectrum analyzer."""
    def __init__(
        self,
        parent,
        channel: Channel | str = Channel.MONO,
        config: Optional[FrameConfig] = None,
        visuals: Optional[SpectrumStyle] = None,
        ballistics: Optional[FFTBallistics] = None
    ):
        self.channel = Channel.from_str(str(channel))
        self.ballistics = ballistics
        self.spectrum_style = visuals if visuals is not None else SpectrumStyle(barsize_pc=1.0)
        self.bar_style = self.spectrum_style.bar_style

        resolved_config = config if config is not None else FrameConfig(square=True)
        super().__init__(parent, config=resolved_config)
        self.configure()

    def configure(self):
        Spectrum.__init__(
            self,
            self.w,
            barsize_pc=self.spectrum_style.barsize_pc,
            bandwidth=8000,
            ballistics=self.ballistics,
            platform=self.platform
        )
        self.max_radius = self.h / 2
        self.ray_angle = 1.0 / max(1, self.bars)
        self.centre_pc = 0.8
        from pyvisualiser.core.components import Line
        import numpy as np

        self.rays = [
            Line(
                self,
                endstops=(np.pi / 2, 5 * np.pi / 2),
                width=int(self.spectrum_style.barsize_pc * 2),
                tick_pc=self.centre_pc,
                centre_offset=0,
                radius=self.max_radius,
                colour='mid'
            )
            for _ in range(self.bars)
        ]

    def update_screen(self, audio=None, media=None):
        self.read(self.channel, audio_snapshot=audio)
        radius = self.centre_pc
        for ray_index, ray in enumerate(self.rays):
            col = self.max_radius * (ray_index / max(1, self.bars))
            amp = radius * self.current[ray_index].smoothed() if self.current[ray_index].smoothed() > 0 else 0
            ray.drawFrameCentredVector(ray_index * self.ray_angle, amplitude=amp, gain=1 - radius, colour=col)
        return True


class Octaviser(Frame, Spectrum):
    """Concentric radial octave arcs."""
    def __init__(
        self,
        parent,
        channel: Channel | str = Channel.MONO,
        config: Optional[FrameConfig] = None,
        visuals: Optional[SpectrumStyle] = None
    ):
        self.channel = Channel.from_str(str(channel))
        
        self.spectrum_style = visuals if visuals is not None else SpectrumStyle()
        self.ballistics = self.spectrum_style.ballistics

        resolved_config = config if config is not None else FrameConfig(align=('left', 'bottom'))
        super().__init__(parent, config=resolved_config)

        self.configure()

    def configure(self):
        Spectrum.__init__(
            self,
            self.w,
            barsize_pc=5,
            ballistics=self.ballistics,
            platform=self.platform
        )
        self.num_octaves = len(self.octaves)
        self.arcs = ArcsOctaves(self, config=self.config, NumOcts=self.num_octaves)


    def update_screen(self, audio=None, media=None):
        self.read(self.channel, audio_snapshot=audio)
        # Delegate draw to arcs
        return True


class StereoSpectrumFrame(Frame):
    """Dual-channel vertical split spectrum analyzer."""
    def __init__(
        self,
        parent,
        config: Optional[FrameConfig] = None,
        visuals: Optional[SpectrumStyle] = None
    ):
        resolved_config = config if config is not None else FrameConfig()
        super().__init__(parent, config=resolved_config)
        self.spectrum_style = visuals if visuals is not None else SpectrumStyle(barw_min=15, barsize_pc=0.5)
        self.configure()

    def configure(self):
        style_r = SpectrumStyle(
            barsize_pc=self.spectrum_style.barsize_pc,
            barw_min=self.spectrum_style.barw_min,
            bar_style=BarStyle(led_gap=5, peak_h=3, radius=0)
        )
        style_l = SpectrumStyle(
            barsize_pc=self.spectrum_style.barsize_pc,
            barw_min=self.spectrum_style.barw_min,
            bar_style=BarStyle(led_gap=5, peak_h=3, radius=0)
        )
        self += SpectrumFrame(
            self,
            channel=Channel.RIGHT,
            config=FrameConfig(scalers=(1.0, 0.5), align=('left', 'top')),
            visuals=style_r
        )
        self += SpectrumFrame(
            self,
            channel=Channel.LEFT,
            config=FrameConfig(scalers=(1.0, 0.5), align=('left', 'bottom')),
            visuals=style_l
        )

    def update_screen(self, audio=None, media=None):
        self.draw_outline()
        self.draw_background()
        draw_list = sorted(self.frames, key=lambda x: getattr(x, 'z_order', 0))
        for f in draw_list:
            f.draw_outline()
            f.draw_background()
            f.update_screen(audio=audio, media=media)
        return True


class Spectrum2chFrame(Frame):
    """Dual-channel side-by-side vertical split spectrum."""
    def __init__(
        self,
        parent,
        config: Optional[FrameConfig] = None,
        visuals: Optional[SpectrumStyle] = None
    ):
        resolved_config = config if config is not None else FrameConfig()
        super().__init__(parent, config=resolved_config)
        self.spectrum_style = visuals
        self.configure()

    def configure(self):
        from pyvisualiser.core.framecore import ColFramer
        cols = ColFramer(self, col_ratios=(1, 1), config=FrameConfig(scalers=(0.7, 0.7), padding=10))
        cols += SpectrumFrame(cols, channel=Channel.LEFT, visuals=self.spectru)
        cols += SpectrumFrame(cols, channel=Channel.RIGHT, visuals=self.spectrum_style)


        
