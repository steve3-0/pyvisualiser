"""
Core Profile definitions for pyvisualiser.
A Profile is the top-level configuration hierarchy that defines the target environment
(e.g. Embedded HiFi Preamp, Desktop) and its default aesthetic styling.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, Dict
import logging

from .styles import BarEffects, BackgroundStyle, BarStyle, SpectrumStyle, VUMeterStyle, TextStyle

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    min_val: float
    max_val: float
    default: float
    step: float
    description: str = ""


# Master parameter specification map defining exact operational bounds
PARAMETER_SPECS: Dict[str, ParameterSpec] = {
    'intensity': ParameterSpec(name='intensity', min_val=0.0, max_val=3.0, default=0.8, step=0.05, description='Overall brightness/bloom intensity'),
    'softness': ParameterSpec(name='softness', min_val=0.0, max_val=1.0, default=0.5, step=0.05, description='Glow spread and blur factor'),
    'threshold': ParameterSpec(name='threshold', min_val=0.1, max_val=2.0, default=1.0, step=0.05, description='Bloom extraction floor threshold'),
    'energy': ParameterSpec(name='energy', min_val=0.0, max_val=1.0, default=0.5, step=0.05, description='Audio reactivity scaling'),
    'vignette': ParameterSpec(name='vignette', min_val=0.0, max_val=1.0, default=0.2, step=0.02, description='Cinematic border shadow strength'),
    'sharpness': ParameterSpec(name='sharpness', min_val=0.0, max_val=1.0, default=0.6, step=0.05, description='FXAA / detail balance'),
    'warmth': ParameterSpec(name='warmth', min_val=0.0, max_val=1.0, default=0.5, step=0.05, description='Color palette color grading temperature'),
    'saturation': ParameterSpec(name='saturation', min_val=0.0, max_val=2.0, default=0.8, step=0.05, description='Color richness'),
}


@dataclass
class ProfileControls:
    """Master perceptual controls that drive rendering parameters dynamically."""
    intensity: float = PARAMETER_SPECS['intensity'].default
    softness: float = PARAMETER_SPECS['softness'].default
    threshold: float = PARAMETER_SPECS['threshold'].default
    energy: float = PARAMETER_SPECS['energy'].default
    smoothness: float = 0.7
    warmth: float = PARAMETER_SPECS['warmth'].default
    saturation: float = PARAMETER_SPECS['saturation'].default
    depth: float = 0.3
    vignette: float = PARAMETER_SPECS['vignette'].default
    sharpness: float = PARAMETER_SPECS['sharpness'].default


class ProfileController:
    """Live-mutable controller that applies ProfileControls to the static styles and Compositor using strict ParameterSpecs."""
    def __init__(self, controls: Optional[ProfileControls] = None):
        if controls is None:
            controls = ProfileControls()
        self.controls = controls
        self.selected_index = 0
        self.parameters = list(PARAMETER_SPECS.keys())

    def select_next(self):
        self.selected_index = (self.selected_index + 1) % len(self.parameters)
        param_name = self.parameters[self.selected_index]
        print(f"ProfileController.select_next> {param_name} ({PARAMETER_SPECS[param_name].description})")

    def select_prev(self):
        self.selected_index = (self.selected_index - 1) % len(self.parameters)
        param_name = self.parameters[self.selected_index]
        print(f"ProfileController.select_prev> {param_name} ({PARAMETER_SPECS[param_name].description})")

    @property
    def selected_parameter(self) -> str:
        return self.parameters[self.selected_index]

    def adjust(self, key: Optional[str], delta: float):
        """Safely adjust a control parameter by delta, clamping strictly to its ParameterSpec bounds."""
        target = key if key is not None else self.selected_parameter
        
        if hasattr(self.controls, target) and target in PARAMETER_SPECS:
            spec = PARAMETER_SPECS[target]
            current = getattr(self.controls, target)
            new_val = max(spec.min_val, min(spec.max_val, current + delta))
            setattr(self.controls, target, new_val)
        else:
            logger.warning(f"ProfileController.adjust> Unknown or unmanaged parameter key: '{target}'. Ignoring adjustment.")

    def apply_profile(self, compositor, style=None):
        """Map the high-level perceptual controls down to technical rendering parameters."""
        if not compositor:
            return
            
        compositor.active_controls = self.controls
        compositor.fxaa_enabled = self.controls.sharpness > 0.3


@dataclass
class VisualiserProfile:
    """
    Base class for a complete Visualiser Profile.
    Defines the absolute root context for the application.
    """
    name: str = "Base Profile"
    target_resolution: tuple[int, int] = (1920, 1080)
    fullscreen: bool = False
    framerate: int = 60
    
    default_palette: str = 'std'
    effects: BarEffects = field(default_factory=BarEffects)
    
    background_style: Optional[BackgroundStyle] = None
    bar_style: Optional[BarStyle] = None
    spectrum_style: Optional[SpectrumStyle] = None
    vu_meter_style: Optional[VUMeterStyle] = None
    text_style: Optional[TextStyle] = None

    def get_style(self, component_type: str) -> Any:
        return getattr(self, f"{component_type}_style", None)


class ProfileManager:
    """Singleton manager for the active application profile and live controller."""
    _active_profile: Optional[VisualiserProfile] = None
    _controller: Optional[ProfileController] = None
    
    @classmethod
    def set_profile(cls, profile: VisualiserProfile):
        cls._active_profile = profile
        
    @classmethod
    def get_profile(cls) -> VisualiserProfile:
        if cls._active_profile is None:
            raise RuntimeError("No active profile set! Call ProfileManager.set_profile() before initialising visualisers.")
        return cls._active_profile

    @classmethod
    def get_controller(cls) -> ProfileController:
        if cls._controller is None:
            cls._controller = ProfileController()
        return cls._controller