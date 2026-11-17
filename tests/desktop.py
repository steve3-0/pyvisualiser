"""
    Desktop Visualiser - main entry point for the application
    Tests screens.
    Screens are defined in desktop_screens.py

"""

from pyvisualiser.styles.presets import EmbeddedHiFiProfile
from pyvisualiser.visualisers.vumeters import *
from pyvisualiser.visualisers.metadata import *
from pyvisualiser.visualisers.spectrum import *
from pyvisualiser.visualisers.oscillogramme import *


from   desktop_hero import DesktopNexusScreen, AuraCanvasScreen, StellarPulseScreen

from   pyvisualiser import ScreenController
import platform

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="pygame.pkgdata")
# Suppress setuptools pkg_resources deprecation warnings originating from third-party libraries like pygame
warnings.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources is deprecated.*")


SCREENS = (DesktopNexusScreen, AuraCanvasScreen, StellarPulseScreen )
# SCREENS = (AuraCanvasScreen, )#StellarPulseScreen, )#DesktopNexusScreen, AuraCanvasScreen )
""" 
    Determine the underlying hardware plaform - NB: Pi is assumed to use the KMS graphics driver 
    the loopback and roon zones are all configured by the user to match their system
""" 

PI_PLATFORM  = { "gfx": "pi_kms", "loopback":"loopin", "roon_zone":"pre3" }
MAC_PLATFORM = { "gfx": "gl", "loopback":"BlackHole 2ch", "roon_zone":"MacViz" }
# Warning.filterwarnings("ignore", category=UserWarning, message=".*pkg_resources is deprecated.*")

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
    
if __name__ == "__main__":
    from pyvisualiser.styles.profiles import ProfileManager
    from pyvisualiser.styles.presets import DesktopWidgetProfile
    ProfileManager.set_profile(DesktopWidgetProfile)

    visualiser = ScreenController(SCREENS, hw_platform=machine() )

    try:
        visualiser.run()
    except KeyboardInterrupt:
        visualiser.stop()





