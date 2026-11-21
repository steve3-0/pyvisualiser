"""
pyvisualiser - Frame Configuration
==================================

Strongly-typed, immutable configuration container for layout, hierarchy,
and styling across all Frame subclasses.
"""

from dataclasses import dataclass, replace
from typing import Optional, Tuple, Union
from .base_defs import HorizontalAlign, VerticalAlign
from ..styles.styles import BackgroundStyle, OutlineStyle


@dataclass(frozen=True)
class FrameConfig:
    """Unified layout, hierarchy, and styling specification for any Frame."""
    scalers: Tuple[float, float] = (1.0, 1.0)
    align: Tuple[Union[HorizontalAlign, str], Union[VerticalAlign, str]] = (
        HorizontalAlign.CENTRE,
        VerticalAlign.MIDDLE,
    )
    padding: int = 0
    margin: int = 0
    square: bool = False
    z_order: int = 0
    theme: Optional[str] = None
    background: Optional[BackgroundStyle] = None
    outline: Optional[OutlineStyle] = None

    def change(self, **changes) -> "FrameConfig":
        """
        Create a new FrameConfig based on this instance with specified attributes changed.
        
        Example:
            child_config = parent.config.clone(align=('centre', 'middle'), padding=10)
        """
        return replace(self, **changes)


    def __post_init__(self):
        # Validate scalers
        sw, sh = self.scalers
        if sw <= 0.0 or sh <= 0.0:
            raise ValueError(f"Frame scalers must be strictly positive floats, got {self.scalers}")

        # Enforce non-negative padding and margin
        if self.padding < 0:
            object.__setattr__(self, "padding", 0)
        if self.margin < 0:
            object.__setattr__(self, "margin", 0)

    @classmethod
    def default(cls) -> "FrameConfig":
        """Default full-scale, centered configuration."""
        return cls()

    @classmethod
    def centered(
        cls,
        scalers: Tuple[float, float] = (1.0, 1.0),
        padding: int = 0,
        theme: Optional[str] = None,
        background: Optional[BackgroundStyle] = None,
        outline: Optional[OutlineStyle] = None,
    ) -> "FrameConfig":
        """Convenience constructor for centered frames."""
        return cls(
            scalers=scalers,
            align=(HorizontalAlign.CENTRE, VerticalAlign.MIDDLE),
            padding=padding,
            theme=theme,
            background=background,
            outline=outline,
        )

FullScale      = (1.0,1.0)
Centred        = ('centre', 'middle')
PI             = 3.14159265358979323846    