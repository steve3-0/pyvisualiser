"""
pyvisualiser - Core State Carriers
==================================

Lightweight, typed, and immutable snapshots for real-time audio telemetry
and media playback state.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict
import numpy as np


@dataclass(frozen=True)
class AudioSnapshot:
    """Instantaneous audio DSP analysis snapshot."""
    vu: Dict[str, float] = field(default_factory=lambda: {"left": 0.0, "right": 0.0, "mono": 0.0})
    peaks: Dict[str, float] = field(default_factory=lambda: {"left": 0.0, "right": 0.0, "mono": 0.0})
    bins: Dict[str, np.ndarray] = field(default_factory=lambda: {"mono": np.zeros(64, dtype=np.float32)})
    samples: Dict[str, np.ndarray] = field(default_factory=lambda: {"mono": np.zeros(1024, dtype=np.int16)})
    bass: float = 0.0
    treble: float = 0.0
    bpm: float = 0.0
    is_beat: bool = False
    centroid: float = 0.0
    flux: float = 0.0
    kurtosis: float = 0.0

    def get_vu(self, channel: str = "mono") -> float:
        return self.vu.get(channel, self.vu.get("mono", 0.0))

    def get_peak(self, channel: str = "mono") -> float:
        return self.peaks.get(channel, self.peaks.get("mono", 0.0))


@dataclass(frozen=True)
class MediaSnapshot:
    """Current track playback metadata and preamp hardware status."""
    track: str = "Ready"
    artist: str = ""
    album: str = ""
    duration: float = 0.0
    elapsed: float = 0.0
    volume: str = "40"
    volume_db: float = 0.0
    source: str = "Roon"
    format: str = "FLAC"
    sample_rate: str = "44.1kHz 16bit"
    playing: bool = False
    album_art: Optional[str] = None
    artist_art: Optional[str] = None

    @property
    def elapsed_pc(self) -> float:
        """Percentage of track elapsed (guaranteed 0.0 to 1.0 safe from ZeroDivision)."""
        if self.duration <= 0.0:
            return 0.0
        return max(0.0, min(1.0, self.elapsed / self.duration))

    @property
    def remaining(self) -> float:
        """Remaining duration in seconds."""
        return max(0.0, self.duration - self.elapsed)

    def format_elapsed(self) -> str:
        """Formatted string 'M:SS'."""
        secs = int(max(0.0, self.elapsed))
        return f"{secs // 60}:{secs % 60:02d}"

    def format_remaining(self) -> str:
        """Formatted string 'M:SS'."""
        secs = int(max(0.0, self.remaining))
        return f"{secs // 60}:{secs % 60:02d}"