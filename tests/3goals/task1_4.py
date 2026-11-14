#!/usr/bin/env python3
"""
Test Harness for Task 1.4: Cross-Platform Packaging & Dependencies Hardening
Verifies that:
1. pyproject.toml is syntactically valid and parsed with tomllib.
2. PEP 508 environment markers correctly exclude pyobjc packages when evaluating for Linux/RPi.
3. PEP 508 environment markers include pyobjc packages when evaluating for macOS (Darwin).
4. requirements-pi.txt contains zero references to macOS frameworks.
5. pyvisualiser imports cleanly without unshielded platform-dependent dependencies.
"""

import os
import sys

# Ensure tomllib availability (Python 3.11+ built-in)
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        raise ImportError("Task 1.4 test requires Python 3.11+ or 'tomli' package.")

from packaging.requirements import Requirement


def find_repo_root() -> str:
    """Dynamically traverse upward from this file to locate the repo root."""
    current = os.path.abspath(os.path.dirname(__file__))
    while current != os.path.dirname(current):
        if os.path.exists(os.path.join(current, "pyproject.toml")):
            return current
        current = os.path.dirname(current)
    raise FileNotFoundError("Could not find repository root containing pyproject.toml")


REPO_ROOT = find_repo_root()
SRC_PATH = os.path.join(REPO_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


def test_packaging_configuration():
    print("=" * 70)
    print("Running Task 1.4 Verification Test: Cross-Platform Packaging")
    print(f"Repo Root Detected: {REPO_ROOT}")
    print("=" * 70)

    pyproject_path = os.path.join(REPO_ROOT, "pyproject.toml")
    requirements_path = os.path.join(REPO_ROOT, "requirements.txt")
    requirements_pi_path = os.path.join(REPO_ROOT, "requirements-pi.txt")

    assert os.path.exists(pyproject_path), f"Missing {pyproject_path}"
    assert os.path.exists(requirements_path), f"Missing {requirements_path}"
    assert os.path.exists(requirements_pi_path), f"Missing {requirements_pi_path}"

    # 1. Parse pyproject.toml
    print("[*] Test 1: Parsing pyproject.toml...")
    with open(pyproject_path, "rb") as f:
        pyproject_data = tomllib.load(f)

    project_section = pyproject_data.get("project", {})
    dependencies = project_section.get("dependencies", [])
    assert len(dependencies) > 0, "No dependencies declared in pyproject.toml"

    # 2. Simulate dependency resolution for Linux / Raspberry Pi
    print("[*] Test 2: Evaluating dependencies for Linux (RPi 5)...")
    linux_env = {"sys_platform": "linux"}
    resolved_linux_deps = []

    for dep_str in dependencies:
        req = Requirement(dep_str)
        if req.marker is None or req.marker.evaluate(linux_env):
            resolved_linux_deps.append(req.name.lower())

    # Verify no pyobjc packages are resolved on Linux
    pyobjc_on_linux = [d for d in resolved_linux_deps if "pyobjc" in d]
    print(f"[*] Linux resolved dependencies count: {len(resolved_linux_deps)}")
    assert len(pyobjc_on_linux) == 0, (
        f"CRITICAL: pyobjc dependencies resolved on Linux! Found: {pyobjc_on_linux}"
    )
    print("[+] Verified: Zero pyobjc dependencies resolved under Linux environment marker.")

    # 3. Simulate dependency resolution for macOS
    print("\n[*] Test 3: Evaluating dependencies for macOS (Darwin)...")
    darwin_env = {"sys_platform": "darwin"}
    resolved_darwin_deps = []

    for dep_str in dependencies:
        req = Requirement(dep_str)
        if req.marker is None or req.marker.evaluate(darwin_env):
            resolved_darwin_deps.append(req.name.lower())

    pyobjc_on_darwin = [d for d in resolved_darwin_deps if "pyobjc" in d]
    print(f"[*] macOS resolved dependencies count: {len(resolved_darwin_deps)}")
    assert len(pyobjc_on_darwin) >= 3, (
        f"Expected at least 3 pyobjc dependencies on macOS, found {len(pyobjc_on_darwin)}"
    )
    print(f"[+] Verified: macOS correctly resolved pyobjc dependencies: {pyobjc_on_darwin}")

    # 4. Check requirements-pi.txt
    print("\n[*] Test 4: Auditing requirements-pi.txt...")
    with open(requirements_pi_path, "r", encoding="utf-8") as f:
        pi_lines = f.readlines()

    for line_idx, line in enumerate(pi_lines, start=1):
        clean_line = line.strip().lower()
        if clean_line and not clean_line.startswith("#"):
            assert "pyobjc" not in clean_line, (
                f"Forbidden pyobjc package in requirements-pi.txt at line {line_idx}: {line}"
            )
    print("[+] Verified: requirements-pi.txt is clean of macOS packages.")

    # 5. Verify pyvisualiser root import safety
    print("\n[*] Test 5: Testing clean module import...")
    import pyvisualiser  # noqa: F401

    assert hasattr(pyvisualiser, "ScreenController"), "Failed to export ScreenController"
    assert hasattr(pyvisualiser, "GeometryPass"), "Failed to export GeometryPass"
    print(f"[+] Verified: pyvisualiser (v{pyvisualiser.get_version()}) imported cleanly.")

    print("\n" + "=" * 70)
    print("[+] ALL TASK 1.4 PACKAGING TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_packaging_configuration()