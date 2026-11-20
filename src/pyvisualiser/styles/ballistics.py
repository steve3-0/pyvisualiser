"""
pyvisualiser - Motion Dynamics & Ballistics
===========================================

Decouples physical motion timing, temporal smoothing, and peak-hold physics
from visual geometric styling.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MeterBallistics:
    """Motion dynamics and temporal filtering for analogue & digital VU meters."""
    decay_rate: float = 0.30          # Fractional decay per frame (0.01 to 0.99)
    peak_decay_rate: float = 0.005    # Fall-off rate for floating peak markers
    smoothing_samples: int = 10       # Moving average window size for needle inertia
    peak_hold_frames: int = 30        # Frames to freeze peak before initiating decay
    overshoot_damping: float = 0.85   # Damping factor for skeuomorphic needle bounce

    def __post_init__(self):
        if not (0.0 < self.decay_rate < 1.0):
            raise ValueError(f"decay_rate must be between 0.0 and 1.0, got {self.decay_rate}")
        if self.smoothing_samples < 1:
            object.__setattr__(self, "smoothing_samples", 1)


@dataclass(frozen=True)
class FFTBallistics:
    """Motion dynamics and temporal filtering for spectrum analysers."""
    attack_rate: float = 0.90         # Rising responsiveness factor (0.0 to 1.0)
    decay_rate: float = 0.25          # Falling decay rate per frame
    peak_decay_rate: float = 0.02     # Floating peak marker decay rate
    smoothing_factor: float = 0.50    # Temporal blending between consecutive FFT frames

    def __post_init__(self):
        if not (0.0 < self.decay_rate < 1.0):
            raise ValueError(f"decay_rate must be between 0.0 and 1.0, got {self.decay_rate}")