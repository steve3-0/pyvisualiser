"""
    Audio Visualiser programme based on preDAC recorder
    this is a sandpit environment to create ideas for use on preDAC
    but using pygame as a renderer to test on Mac OS

    This version aims to simulate the new display and create a range of visually appealing spectrum
    analysers:  Variables to experiment:
        - smoothing
        - decay profiles
        - peak profiles
        - bars made of rectangles

"""

import argparse
import sys
import platform
import warnings

from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
from pyvisualiser.visualisers.oscillogramme import *


from test_hero import *
from test_vua import *
from test_spectrum import *


from screens import *
from screens2 import *
from testscreens import *
from test_api_coverage import *
from test_advanced_visuals import *
from gltest import *
from pyvisualiser import ScreenController

warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources is deprecated.*")

# --- Screen Sets Definition ---
ALLSCREENS = ( MinSpectrumArt, TrackScreen, TrackSpectrumScreen, TrackSpectrumScreen2,\
            TrackSpectrumScreen3, TrackSpectrumScreen4, \
            TrackOscScreen, TrackVisScreen, TrackVisScreen2, TrackVisScreen3, TrackVUMeterScreen, TrackVUMeterScreen2, \
            ArtMetaSpectrumScreen, MinSpectrumArt, ColAlignedScreen  )

ART_SCREENS= (ArtistScreen, ImageTestScreen, ReflectionTestScreen)

SPECTRUM_TEST_SCREENS= (TestSpectrumScreen, StereoSpectrumLRScreen, FullSpectrumOffsetScreen, StereoSpectrumScreen, StereoSpectrumSplitScreen, \
                        MonoSpectrumScreen, MonoSpectrumLEDScreen, SpectrumStereoSplitFrame)

VU_TEST_SCREENS= (TrackVUMeterScreen2, VUImageScreen, VUScreen, VUVScreen, TestVUImageScreen1, TestVUImageScreen2, \
                  TestVUMetersScreen, TestVisualiserScreen, TestSpectrumScreen, TestVUScreen)
VU_BAR_TEST_SCREENS = (VUScreen, VUVScreen, TestVUScreen, IntensityTestScreen)
GEO_TEST_SCREENS= (ColAlignedScreen, RowAlignedScreen, \
                   F1, F2,  F3, F4, F5, F6, F7, F8 )

VU_METER_SCREENS = (VUTestScreen1,  VUTestScreen2,VUImageScreen, VUVintageScreen, VUModernScreen, VUTungstenScreen, 
                    VUNeedleStylesScreen,VUNeedleEffectsScreen, TestVUMetersScreen, TestVUImageScreen1, TestVUImageScreen2)

TEST_SCREENS = (AmbientGlowTunerScreen, AdvancedVisualsScreen, APICoverageScreen, BarParametersTestScreen, VUVScreen, IntensityTestScreen, OutlineGlowTestScreen )

MAIN_SCREENS= (TrackScreen, TrackVisScreen, TrackVisScreen2, TrackVisScreen3, TrackSpectrumScreen, \
               TrackSpectrumScreen2, MetaArtFrame, TrackSpectrumScreen3, TrackSpectrumScreen4,\
               TrackVUMeterScreen, TrackVUMeterScreen2, TrackOscScreen, MixedLEDScreen
               )  

FULL_SCREENS = (Screen1, Screen2, Screen3, Screen4, Screen5, Screen6, Screen7)

SUBFRAMES = (TrackScreen, TrackVisScreen, TrackVisScreen2, TrackVisScreen3, TrackSpectrumScreen, \
             TrackSpectrumScreen2, MetaArtFrame, TrackSpectrumScreen3, TrackSpectrumScreen4, TrackVUMeterScreen, \
             TrackVUMeterScreen2, TrackVUMeterScreen21, TrackOscScreen, MinSpectrumArt, \
             ArtMetaSpectrumScreen, BigDialsScreen2, ArtistScreen, VU2chFrame, VUFlipFrame, \
             VUHorzFrame, VU2chHorzFrame, MetaDataFrame, ArtistMetaDataFrame, \
             StereoSpectrumFrame, MetaMiniSpectrumFrame, SamplesFrame)

BASE_FRAMES = (TextFrame, PlayProgressFrame, ArtFrame, MetaImages, MetaData,\
               VUMeter, VUFrame, SpectrumFrame, OscilogrammeBar, Oscilogramme,\
               Octaviser, Diamondiser)

SUBFRAMES2 = (Spectrum2chFrame, SpectrumStereoFrame,  SpectrumStereoLRFrame,  SpectrumStereoSplitFrame,\
              SpectrumStereoOffsetFrame, VUMeterFrame1, VUMeterFrame2, VUMeterFrame3, VUMeterFrame4, VUMeterImageFrame)   

GLSCREENS  = (GLTestScreen3,GLTestScreen1, GLTestScreen2)

TEST_SCREENS2 = (BackgroundEffectsScreen0, BackgroundEffectsScreen1, BackgroundEffectsScreen2, AmbientGlowTunerScreen,OutlineGlowTestScreen,ProfileTestScreen, \
                 AudioTestScreen, BarEffectsTestScreen, LEDtestScreen, GlowTestScreen)

HERO_SCREENS  = (H1,H2,H3,H4,H5,H6,H7,H8,H9)
QUICK = (VUScreen,)

ALLSCREENS = []
# Dictionary mapping argument names to their respective screen tuples and descriptions
SCREEN_GROUPS = {
    "hero": (HERO_SCREENS, "Hero validation screens"),
    "spectrum": (SPECTRUM_TEST_SCREENS, "Spectrum test screens"),
    "vua": (VU_METER_SCREENS, "Analogue VU meter screens"),
    "vud": (VU_BAR_TEST_SCREENS, "Digital Bar VU test screens"),
    "geo": (GEO_TEST_SCREENS, "Geometry layout test screens"),
    "test": (TEST_SCREENS + TEST_SCREENS2, "Feature & component test screens"),
    "art": (ART_SCREENS, "Art & image metadata screens"),
    "full": (FULL_SCREENS, "Full display layout screens"),
    "gl": (GLSCREENS, "OpenGL integration test screens"),
    "main": (MAIN_SCREENS, "Main production screens"),
    "all": (ALLSCREENS, "All registered screens"),
    "q": (QUICK,"current test screen"),
    "subs": (SUBFRAMES+SUBFRAMES2, "Subframe components"),
    "major": (SPECTRUM_TEST_SCREENS+VU_METER_SCREENS+VU_BAR_TEST_SCREENS+ART_SCREENS, "Major frame components"),
}

for group_name, (screens, _) in SCREEN_GROUPS.items():
    ALLSCREENS.extend(screens)

PI_PLATFORM  = { "gfx": "pi_kms", "loopback":"loopin", "roon_zone":"pre3" }
MAC_PLATFORM = { "gfx": "gl", "loopback":"BlackHole 2ch", "roon_zone":"MacViz" }

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
    """Dynamically builds detailed help text showing sets and their member screens."""
    desc = ["PreDAC Audio Visualiser Test Runner.\n\nAvailable Screen Groups & Classes:"]
    for group_name, (screens, description) in SCREEN_GROUPS.items():
        screen_names = [s.__name__ for s in screens]
        desc.append(f"  --{group_name} : {description}")
        desc.append(f"    Screens: {', '.join(screen_names)}\n")
    return "\n".join(desc)

if __name__ == "__main__":
    from pyvisualiser.styles.profiles import ProfileManager
    from pyvisualiser.styles.presets import EmbeddedHiFiProfile
    ProfileManager.set_profile(EmbeddedHiFiProfile)

    # Set up argument parser with custom formatting to list groups nicely
    parser = argparse.ArgumentParser(
        description="Run pyvisualiser with specific screen tests.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=build_help_description()
    )

    # Add mutually exclusive or additive flags for screen groups
    group = parser.add_argument_group("Screen Selectors")
    for key, (_, desc) in SCREEN_GROUPS.items():
        group.add_argument(f"--{key}", action="store_true", help=f"Run {desc.lower()}")

    # Add argument to accept explicit class names
    parser.add_argument(
        "classes", 
        nargs="*", 
        help="Explicit screen class name(s) to run (e.g. TrackScreen H1)"
    )

    args = parser.parse_args()

    # Collect selected screens
    selected_screens = []

    # Check which groups were requested via flags
    group_matched = False
    for key, (screens, _) in SCREEN_GROUPS.items():
        if getattr(args, key, False):
            selected_screens.extend(screens)
            group_matched = True

    # Check if explicit screen class names were provided in command line arguments
    if args.classes:
        group_matched = True
        # Look up class names from globals() context
        for cls_name in args.classes:
            cls_obj = globals().get(cls_name)
            if cls_obj and isinstance(cls_obj, type):
                selected_screens.append(cls_obj)
            else:
                print(f"Warning: Screen class '{cls_name}' not found or is not a valid class.")

    # Fallback default if no arguments are provided (defaults to HERO_SCREENS or whatever you prefer)
    if not group_matched:
        print("No screens or groups specified. Running default HERO screens. Use -h or --help to see available options.")
        selected_screens = HERO_SCREENS

    # Deduplicate screens while preserving order
    seen = set()
    unique_screens = [x for x in selected_screens if not (x in seen or seen.add(x))]

    if not unique_screens:
        print("Error: No valid screens selected to run.")
        sys.exit(1)

    print(f"Running {len(unique_screens)} screen(s)...")
    
    visualiser = ScreenController(tuple(unique_screens), hw_platform=machine())

    try:
        visualiser.run()
    except KeyboardInterrupt:
        visualiser.stop()