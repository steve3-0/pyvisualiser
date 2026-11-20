"""
pyvisualiser - Core Foundational Definitions
=============================================

Typed enumerations and base constants using British English conventions.
Supports Python 3.10+ via a backwards-compatible StrEnum shim.
"""

import sys
from enum import Enum

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    class StrEnum(str, Enum):
        """Python 3.10 compatible StrEnum implementation."""
        def __str__(self) -> str:
            return str(self.value)

        def __eq__(self, other: object) -> bool:
            if isinstance(other, str):
                return self.value == other
            return super().__eq__(other)

        def __hash__(self) -> int:
            return hash(self.value)


class Channel(StrEnum):
    """Audio signal channel identifiers."""
    LEFT = "left"
    RIGHT = "right"
    MONO = "mono"

    @classmethod
    def from_str(cls, value: str) -> "Channel":
        clean = value.strip().lower()
        for member in cls:
            if member.value == clean:
                return member
        raise ValueError(f"Unknown Channel: {value}. Expected one of: {[m.value for m in cls]}")


class Orientation(StrEnum):
    """Layout growth direction for meters, bars, and progressions."""
    VERTICAL = "vert"
    HORIZONTAL = "horz"

    # Aliases
    VERT = "vert"
    HORZ = "horz"


class HorizontalAlign(StrEnum):
    """Horizontal alignment anchors."""
    LEFT = "left"
    CENTRE = "centre"
    RIGHT = "right"
    COLUMN = "col"

    # American English spelling alias
    CENTER = "centre"


class VerticalAlign(StrEnum):
    """Vertical alignment anchors."""
    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"
    ROW = "row"


class ThemeColour(StrEnum):
    """Standard semantic theme colour keys."""
    FOREGROUND = "foreground"
    BACKGROUND = "background"
    LIGHT = "light"
    MID = "mid"
    DARK = "dark"
    ALERT = "alert"


class MetadataKey(StrEnum):
    """Standard metadata query and binding keys."""
    TRACK = "track"
    ARTIST = "artist"
    ALBUM = "album"
    DURATION = "duration"
    ELAPSED = "elapsed"
    VOLUME = "volume"
    SOURCE = "source"
    SAMPLE_RATE = "sample_rate"
    FORMAT = "format"


class RenderLayer(StrEnum):
    """Execution stages for the multi-stage compositor."""
    BACKGROUND = "background"
    EMISSIVE = "emissive"
    GLOW = "glow"
    VECTOR_UI = "vector_ui"
    TYPOGRAPHY = "typography"
    OVERLAY = "overlay"