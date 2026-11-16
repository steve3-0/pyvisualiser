#!/usr/bin/env python3
"""
Test Harness for Task 3.4: Dynamic Parameter Specifications & Bounded Controls
Verifies that:
1. ProfileController respects individual min/max bounds from PARAMETER_SPECS.
2. Extreme positive or negative adjustments (e.g. +/- 5.0) clamp correctly to limits (e.g. vignette [0.0, 1.0], intensity [0.0, 3.0]).
3. Unknown parameters emit warnings without crashing.
"""

import os
import sys
import logging

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

from pyvisualiser.styles.profiles import ProfileController, PARAMETER_SPECS


def test_parameter_bounding():
    print("=" * 70)
    print("Running Task 3.4 Verification Test: Parameter Bound Clamping")
    print("=" * 70)

    controller = ProfileController()

    # 1. Test vignette upper bound (max_val = 1.0)
    controller.controls.vignette = 0.5
    controller.adjust('vignette', 5.0)  # Extreme positive delta
    print(f"[*] Adjusting vignette by +5.0 -> Result: {controller.controls.vignette}")
    assert controller.controls.vignette == 1.0, f"Expected vignette clamped to 1.0, got {controller.controls.vignette}"
    print("[+] Verified: Vignette correctly clamped to upper bound 1.0.")

    # 2. Test vignette lower bound (min_val = 0.0)
    controller.adjust('vignette', -10.0)  # Extreme negative delta
    print(f"[*] Adjusting vignette by -10.0 -> Result: {controller.controls.vignette}")
    assert controller.controls.vignette == 0.0, f"Expected vignette clamped to 0.0, got {controller.controls.vignette}"
    print("[+] Verified: Vignette correctly clamped to lower bound 0.0.")

    # 3. Test intensity upper bound (max_val = 3.0)
    controller.controls.intensity = 2.5
    controller.adjust('intensity', 10.0)
    print(f"[*] Adjusting intensity by +10.0 -> Result: {controller.controls.intensity}")
    assert controller.controls.intensity == 3.0, f"Expected intensity clamped to 3.0, got {controller.controls.intensity}"
    print("[+] Verified: Intensity correctly clamped to upper bound 3.0.")

    # 4. Test unknown key safety (should log warning, no exception)
    print("[*] Testing unknown key resilience...")
    controller.adjust('nonexistent_knob', 1.0)
    print("[+] Verified: Unknown parameter keys handled safely without crashing.")

    # 5. Verify all defined specs are covered
    print(f"[*] Total managed parameters in specs: {len(PARAMETER_SPECS)}")
    assert 'vignette' in PARAMETER_SPECS
    assert 'intensity' in PARAMETER_SPECS
    assert 'softness' in PARAMETER_SPECS

    print("\n" + "=" * 70)
    print("[+] ALL TASK 3.4 PARAMETER BOUNDING TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    test_parameter_bounding()