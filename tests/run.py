"""
    Audio Visualiser test runner supporting screen groups and profile flags.
    Part of pyvisualiser v2.1.0
"""

import argparse
import sys
import platform
import warnings
import os
from pathlib import Path

# Ensure repo root and tests directory are in sys.path
TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
SRC_DIR = REPO_ROOT / "src"

for path in (str(SRC_DIR), str(TESTS_DIR), str(REPO_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
from pyvisualiser.visualisers.oscillogramme import *

# --- Suite Imports (Standard Absolute Imports) ---
from suite.test_desktop_profile import (
    DesktopNexusScreen,
    AuraCanvasScreen,
    StellarPulseScreen,
)
from suite.test_hero import (
    H1, H2, H3, H4, H5, H6, H7, H8, H9,
)
from suite.test_vua import (
    VUTungstenScreen,
    VUTestScreen1,
    VUTestScreen2,
    VUNeedleEffectsScreen,
    VUNeedleStylesScreen,
    VUImageScreen,
    VUVintageScreen,
    VUModernScreen,
    TestVUImageScreen1,
    TestVUImageScreen2,
    TestVUMetersScreen,
    VUMeterFrame1,
    VUMeterFrame2,
    VUMeterFrame3,
    VUMeterFrame4,
    TrackVUMeterScreen2,
)
from suite.test_spectrum import (
    SpectrumStereoFrame,
    SpectrumStereoLRFrame,
    SpectrumStereoSplitFrame,
    SpectrumStereoOffsetFrame,
    StereoSpectrumFrame,
    Spectrum2chFrame,
    StereoSpectrumLRScreen,
    FullSpectrumOffsetScreen,
    StereoSpectrumScreen,
    StereoSpectrumSplitScreen,
    MonoSpectrumScreen,
    MonoSpectrumLEDScreen,
    TestSpectrumScreen,
    TestDiamondiser,
    TestOctaviser,
)
from suite.test_full import (
    Screen1,
    Screen2,
    Screen3,
    Screen4,
    Screen5,
    Screen6,
    Screen7,
    ProfileTestScreen,
    LEDtestScreen,
    TrackScreen,
    TrackVisScreen,
    TrackVisScreen2,
    TrackSpectrumScreen,
    TrackSpectrumScreen2,
    MetaArtFrame,
    TrackSpectrumScreen3,
    TrackSpectrumScreen4,
    TrackVUMeterScreen,
    TrackVUMeterScreen21,
    MinSpectrumArt,
    ArtMetaSpectrumScreen,
    BigDialsScreen2,
)
from suite.test_vud import (
    VUScreen,
    VU2Screen,
    VUVScreen,
    TestVUScreen,
    IntensityTestScreen,
    BarParametersTestScreen,
)
from suite.test_art import (
    ImageTestScreen,
    ReflectionTestScreen,
    ArtistScreen,
    ImageTestScreen2,
)
from suite.test_meta import (
    ArtistMetaDataFrame,
    MetaMiniSpectrumFrame,
    ShadowTestScreen,
    ProgressScreen,
)
from suite.test_back import (
    F9,
    BloomImageTestScreen,
    BackgroundEffectsScreen0,
    BackgroundEffectsScreen1,
    BackgroundEffectsScreen2,
)
from suite.test_geo import (
    MixedLEDScreen,
    TestScreen,
    ColAlignedScreen,
    RowAlignedScreen,
    F1, F2, F3, F4, F5, F6, F7, F8,
)
from suite.test_visuals import (
    BarTest,
    AdvancedVisualsScreen,
    GlowTestScreen,
    BarEffectsTestScreen,
    AudioTest,
    AudioTestScreen,
    AudioTestScreen1,
    OutlineGlowTestScreen,
    AmbientGlowTunerScreen,
    APICoverageScreen,
)
from suite.test_shader import (
    GLmeshScreen,
    GLTestScreen1,
    GLTestScreen2,
    GLTestScreen3,
    GLTestScreen4,
)
from suite.test_osc import (
    TestOscScreen,
    TestOscBarScreen,
    TrackVisScreen3,
    TrackOscScreen
)

from pyvisualiser import ScreenController
from pyvisualiser.styles.profiles import ProfileManager
from pyvisualiser.styles.presets import EmbeddedHiFiProfile, DesktopWidgetProfile

warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources is deprecated.*")

# --- Screen Sets Definition ---

HERO_SCREENS = (H1, H2, H3, H4, H5, H6, H7, H8, H9)

DESKTOP_HERO_SCREENS = (DesktopNexusScreen, AuraCanvasScreen, StellarPulseScreen)

VU_METER_SCREENS = (
    VUTungstenScreen,
    VUTestScreen1,
    VUTestScreen2,
    VUNeedleEffectsScreen,
    VUNeedleStylesScreen,
    VUImageScreen,
    VUVintageScreen,
    VUModernScreen,
    TestVUImageScreen1,
    TestVUImageScreen2,
    TestVUMetersScreen,
    VUMeterFrame1,
    VUMeterFrame2,
    VUMeterFrame3,
    VUMeterFrame4,
    TrackVUMeterScreen2,
)

VU_BAR_TEST_SCREENS = (
    VUScreen,
    VU2Screen,
    VUVScreen,
    TestVUScreen,
    IntensityTestScreen,
    BarParametersTestScreen,
)

SPECTRUM_TEST_SCREENS = (
    TestSpectrumScreen,
    StereoSpectrumLRScreen,
    FullSpectrumOffsetScreen,
    StereoSpectrumScreen,
    StereoSpectrumSplitScreen,
    MonoSpectrumScreen,
    MonoSpectrumLEDScreen,
    TestDiamondiser,
    TestOctaviser,
    SpectrumStereoFrame,
    SpectrumStereoLRFrame,
    SpectrumStereoSplitFrame,
    SpectrumStereoOffsetFrame,
    StereoSpectrumFrame,
    Spectrum2chFrame,
)

OSC_SCREENS = (TestOscScreen, TestOscBarScreen, TrackVisScreen3)

ART_SCREENS = (
    ImageTestScreen,
    ReflectionTestScreen,
    ArtistScreen,
    ImageTestScreen2,
)

META_TEST_SCREENS = (
    ArtistMetaDataFrame,
    MetaMiniSpectrumFrame,
    ShadowTestScreen,
    ProgressScreen,
)

GEO_TEST_SCREENS = (
    ColAlignedScreen,
    RowAlignedScreen,
    MixedLEDScreen,
    TestScreen,
    F1, F2, F3, F4, F5, F6, F7, F8,
)

BACKGROUND_SCREENS = (
    BackgroundEffectsScreen0,
    BackgroundEffectsScreen1,
    BackgroundEffectsScreen2,
    BloomImageTestScreen,
    F9,
)

SHADER_SCREENS = (
    GLTestScreen1,
    GLTestScreen2,
    GLTestScreen3,
    GLTestScreen4,
)

TEST_VISUALS = (
    AdvancedVisualsScreen,
    GlowTestScreen,
    BarEffectsTestScreen,
    AudioTestScreen,
    AudioTestScreen1,
    OutlineGlowTestScreen,
    AmbientGlowTunerScreen,
    APICoverageScreen,
)

MAIN_SCREENS = (
    TrackScreen,
    TrackVisScreen,
    TrackVisScreen2,
    TrackVisScreen3,
    TrackSpectrumScreen,
    TrackSpectrumScreen2,
    MetaArtFrame,
    TrackSpectrumScreen3,
    TrackSpectrumScreen4,
    TrackVUMeterScreen,
    TrackVUMeterScreen21,
    TrackOscScreen,
    MinSpectrumArt,
    ArtMetaSpectrumScreen,
    BigDialsScreen2,
)

FULL_SCREENS = (
    Screen1,
    Screen2,
    Screen3,
    Screen4,
    Screen5,
    Screen6,
    Screen7,
    ProfileTestScreen,
    LEDtestScreen,
) + MAIN_SCREENS

ALLSCREENS = tuple(dict.fromkeys(
    HERO_SCREENS
    + DESKTOP_HERO_SCREENS
    + FULL_SCREENS
    + VU_METER_SCREENS
    + VU_BAR_TEST_SCREENS
    + SPECTRUM_TEST_SCREENS
    + SHADER_SCREENS
    + BACKGROUND_SCREENS
    + OSC_SCREENS
    + ART_SCREENS
    + META_TEST_SCREENS
    + GEO_TEST_SCREENS
    + TEST_VISUALS
))

QUICK = (VUScreen,)

# --- Screen Groups Mapping ---
SCREEN_GROUPS = {
    "hero": (HERO_SCREENS, "Hero validation screens (H1-H9)"),
    "desktop": (DESKTOP_HERO_SCREENS, "Desktop floating widget screens"),
    "spectrum": (SPECTRUM_TEST_SCREENS, "Spectrum analyzer test screens"),
    "vua": (VU_METER_SCREENS, "Analogue VU meter screens"),
    "vud": (VU_BAR_TEST_SCREENS, "Digital Bar VU test screens"),
    "geo": (GEO_TEST_SCREENS, "Geometry layout test screens"),
    "meta": (META_TEST_SCREENS, "Metadata, progress and shadow screens"),
    "back": (BACKGROUND_SCREENS, "Background effects, caustics and textures"),
    "visuals": (TEST_VISUALS, "Visual tuning, parameters, audio and coverage tests"),
    "art": (ART_SCREENS, "Art & image metadata screens"),
    "full": (FULL_SCREENS, "Full display layout screens"),
    "main": (MAIN_SCREENS, "Main production composite screens"),
    "osc": (OSC_SCREENS, "Oscillogramme & waveform screens"),
    "shader": (SHADER_SCREENS, "GLSL Shader visualizer screens"),
    "quick": (QUICK, "Quick single-screen smoke test"),
    "all": (ALLSCREENS, "All registered test screens across the entire suite"),
}

PI_PLATFORM = {"gfx": "pi_kms", "loopback": "loopin", "roon_zone": "pre3"}
MAC_PLATFORM = {"gfx": "gl", "loopback": "BlackHole 2ch", "roon_zone": "MacViz"}


def machine():
    uname = platform.uname()
    if uname.system == "Darwin":
        return MAC_PLATFORM
    elif uname.system == "Linux":
        if "rpi" in uname.release:
            return PI_PLATFORM
        else:
            return MAC_PLATFORM
    else:
        return MAC_PLATFORM


def build_help_description():
    desc = ["PreDAC Audio Visualiser Test Runner.\n\nAvailable Screen Groups & Classes:"]
    for group_name, (screens, description) in SCREEN_GROUPS.items():
        screen_names = [s.__name__ for s in screens]
        desc.append(f"  --{group_name} : {description}")
        desc.append(f"    Screens: {', '.join(screen_names)}\n")
    return "\n".join(desc)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run pyvisualiser with specific screen tests and profiles.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=build_help_description()
    )

    # Profile selection flag
    parser.add_argument(
        "-p", "--profile",
        choices=["e", "d"],
        default="e",
        help="Select active profile:\n  e : Embedded HiFi Profile (default)\n  d : Desktop Widget Profile"
    )

    # Screen Selectors
    group = parser.add_argument_group("Screen Selectors")
    for key, (_, desc) in SCREEN_GROUPS.items():
        group.add_argument(f"--{key}", action="store_true", help=f"Run {desc.lower()}")

    parser.add_argument(
        "classes", 
        nargs="*", 
        help="Explicit screen class name(s) to run (e.g. H1 TrackScreen)"
    )

    args = parser.parse_args()

    # Apply selected profile
    if args.profile == "d":
        ProfileManager.set_profile(DesktopWidgetProfile)
        print("[*] Active Profile: Desktop Widget Profile")
    else:
        ProfileManager.set_profile(EmbeddedHiFiProfile)
        print("[*] Active Profile: Embedded HiFi Profile")

    selected_screens = []
    group_matched = False

    for key, (screens, _) in SCREEN_GROUPS.items():
        if getattr(args, key, False):
            selected_screens.extend(screens)
            group_matched = True

    if args.classes:
        group_matched = True
        for cls_name in args.classes:
            cls_obj = globals().get(cls_name)
            if cls_obj and isinstance(cls_obj, type):
                selected_screens.append(cls_obj)
            else:
                print(f"Warning: Screen class '{cls_name}' not found or is not a valid class.")

    if not group_matched:
        print("No screens or groups specified. Running default HERO screens. Use -h or --help to see available options.")
        selected_screens = HERO_SCREENS

    # Deduplicate screens while preserving order
    # unique_screens = [x for x in selected_screens if x not in dict.fromkeys(selected_screens)]
# Correct deduplication preserving order
    unique_screens = list(dict.fromkeys(selected_screens))

    if not unique_screens:
        print("Error: No valid screens selected to run.")
        sys.exit(1)

    print(f"Running {len(unique_screens)} screen(s)...")
    
    visualiser = ScreenController(tuple(unique_screens), hw_platform=machine())

    try:
        visualiser.run()
    except KeyboardInterrupt:
        visualiser.stop()