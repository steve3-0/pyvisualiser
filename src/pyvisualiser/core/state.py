"""

    - Lightweight, typed state carriers for audio telemetry and media metadata.

Mar 2026 Baloothebeare4 v1    
"""
from dataclasses import dataclass, field
import numpy as np


@dataclass(frozen=True)
class AudioSnapshot:
    """Instantaneous audio analysis data."""
    vu: dict[str, float] = field(default_factory=lambda: {'left': 0.0, 'right': 0.0, 'mono': 0.0})
    peaks: dict[str, float] = field(default_factory=lambda: {'left': 0.0, 'right': 0.0, 'mono': 0.0})
    bins: dict[str, np.ndarray] = field(default_factory=lambda: {'mono': np.zeros(64, dtype=np.float32)})
    samples: dict[str, np.ndarray] = field(default_factory=lambda: {'mono': np.zeros(1024, dtype=np.int16)})
    bass: float = 0.0
    treble: float = 0.0
    bpm: float = 0.0
    is_beat: bool = False


@dataclass(frozen=True)
class MediaSnapshot:
    """Current track playback metadata and preamp state."""
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
    album_art: str | None = None
    artist_art: str | None = None

    @property
    def elapsedpc(self) -> float:
        return (self.elapsed / self.duration) if self.duration > 0 else 0.0

    @property
    def remaining(self) -> float:
        return max(0.0, self.duration - self.elapsed)