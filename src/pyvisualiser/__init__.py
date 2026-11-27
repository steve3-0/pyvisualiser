"""
PyVisualiser - Audio Visualization Library
==========================================

A high-performance GPU-accelerated audio visualization framework
supporting macOS desktop and embedded Raspberry Pi 5 preamplifiers.
"""

import sys
import warnings

# Suppress setuptools pkg_resources deprecation warnings from third-party libraries (pygame)
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources is deprecated.*")

__version__ = "2.0.0"
__author__ = "Baloothebear4"

# Optional macOS platform extensions
if sys.platform == "darwin":
    try:
        import Cocoa  # noqa: F401
        import Quartz  # noqa: F401
    except ImportError:
        pass

# Core Subsystems
from .core.processaudio import AudioProcessor, AudioAnalyser
from .core.displaydriver import (
    GraphicsDriver,
    GraphicsDriverGL,
    GraphicsDriverPi,
    GraphicsDriverMac,
    GeometryPass,
)
from .core.components import (
    Frame,
    Bar,
    Image,
    Text,
    Box,
    Line,
    Outline,
    FontCacheManager,
)
from .core.base_defs import (
    Channel,
    Orientation,
    HorizontalAlign,
    VerticalAlign,
    ThemeColour,
    MetadataKey,
    RenderLayer,
)
from .core.framecore import Frame, ColFramer, RowFramer, ListNext, Colour, Cache, Smoother
from .core.screenhandler import ScreenController, Platform, EventHandler, HWInterface
from .core.render import RenderContext, RenderTarget, Compositor, RenderPass, BlurPass, CompositePass
from .core.frame_config import FrameConfig  # Unified layout, hierarchy, and styling specification for any Frame

# Visualiser Components
from .visualisers.vumeters import VUFrame, VUMeter, VU2chFrame, VU2chHorzFrame, VUFlipFrame, VUMeterImageFrame
from .visualisers.metadata import MetaDataFrame, MetaData, MetaImages
from .visualisers.playprogress import PlayProgressFrame, CircularProgress
from .visualisers.text import TextFrame
from .visualisers.spectrum import SpectrumFrame, Spectrum, Diamondiser, Octaviser
from .visualisers.oscillogramme import Oscilogramme, OscilogrammeBar, SamplesFrame
from .visualisers.advanced_frames import EchoWaveFrame, KaleidoscopeFrame, PulseOrbFrame, SpectrumWaveFrame, FreqWaveFrame
from .visualisers.glvisualisers import ShaderFrame, Kalidoscope, SpectrumMesh
from .core.glwrapper import GLSLFrame, GLSLRenderPass

# Style System
# Style System & Presets
from .styles.styles import (
    BarStyle,
    BarEffects,
    PlayProgressStyle,
    SpectrumStyle,
    VUMeterStyle,
    VUNeedleStyle,
    VUMeterScale,
    ShadowStyle,        
    BackgroundStyle,
    AmbientGlowStyle,
    ReactiveGlowStyle,  
    PeakAccentStyle,
    StarfieldStyle,
    CloudStyle,
    EdgeLightStyle,
    OutlineStyle,
    TextStyle,
    ReflectionStyle,
    VignetteStyle,
    NoiseStyle,
    OscillogrammeStyle,
)
from .styles.presets import (
    EmbeddedHiFiProfile,
    DesktopWidgetProfile,
    LUXURY_PROFILE,
    NEON_PROFILE,
    MINIMAL_PROFILE,
    NeonGlow,
    StrongEffect,
    DreamEffect,
    BackgroundDefault,
    PaletteDefault,
    OutlineDefault,
)
from .styles.profiles import ProfileManager, ProfileControls, ProfileController
from .styles.ballistics import MeterBallistics, FFTBallistics


def get_version() -> str:
    return __version__


__all__ = [
    "ScreenController",
    "Platform",
    "EventHandler",
    "HWInterface",
    "Frame",
    "ColFramer",
    "RowFramer",
    "ListNext",
    "Colour",
    "Cache",
    "Smoother",
    "Bar",
    "Text",
    "Image",
    "Box",
    "Line",
    "Outline",
    "FontCacheManager",
    "AudioProcessor",
    "AudioAnalyser",
    "GraphicsDriver",
    "GraphicsDriverGL",
    "GeometryPass",
    "RenderContext",
    "RenderTarget",
    "Compositor",
    "RenderPass",
    "BlurPass",
    "CompositePass",
    "VUFrame",
    "VUMeter",
    "VU2chFrame",
    "VU2chHorzFrame",
    "VUFlipFrame",
    "VUMeterImageFrame",
    "SpectrumFrame",
    "Spectrum",
    "Diamondiser",
    "Octaviser",
    "Oscilogramme",
    "OscilogrammeBar",
    "SamplesFrame",
    "EchoWaveFrame",
    "KaleidoscopeFrame",
    "PulseOrbFrame",
    "SpectrumWaveFrame",
    "FreqWaveFrame",
    "Kalidoscope",
    "SpectrumMesh",
    "ShaderFrame",
    "MetaDataFrame",
    "MetaData",
    "MetaImages",
    "PlayProgressFrame",
    "TextFrame",
    "CircularProgress",
    "BarStyle",
    "BarEffects",
    "SpectrumStyle",
    "VUMeterStyle",
    "VUNeedleStyle",
    "VUMeterScale",
    "ShadowStyle",
    "BackgroundStyle",
    "AmbientGlowStyle",
    "ReactiveGlowStyle",
    "PeakAccentStyle",
    "StarfieldStyle",
    "CloudStyle",
    "EdgeLightStyle",
    "OutlineStyle",
    "TextStyle",
    "ReflectionStyle",
    "VignetteStyle",
    "NoiseStyle",
    "PlayProgressStyle",
    "OscillogrammeStyle",
    "EmbeddedHiFiProfile",
    "DesktopWidgetProfile",
    "LUXURY_PROFILE",
    "NEON_PROFILE",
    "MINIMAL_PROFILE",
    "NeonGlow",
    "ProfileManager",
    "ProfileControls",
    "ProfileController",
    "get_version",
    "Channel",
    "Orientation",
    "HorizontalAlign",
    "VerticalAlign",
    "ThemeColour",
    "MetadataKey",
    "RenderLayer",
    "FrameConfig",
    "MeterBallistics", 
    "FFTBallistics"
]