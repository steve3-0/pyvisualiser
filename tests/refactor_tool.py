#!/usr/bin/env python3
"""
pyvisualiser - Automated Screen API Migration Tool
==================================================

Safely migrates test screen files to the new FrameConfig and Dataclass API.

Usage:
    # 1. Preview changes (Dry run - does not touch files)
    python tools/migrate_screen_apis.py tests/screens3.py --dry-run

    # 2. Apply changes with automatic .bak backup
    python tools/migrate_screen_apis.py tests/screens3.py --write

    # 3. Batch apply to all test screen files
    python tools/migrate_screen_apis.py tests/screens3.py tests/VUscreens.py tests/testscreens.py --write
"""

import sys
import re
import difflib
import argparse
from pathlib import Path


def ensure_imports(content: str) -> str:
    """Ensures required modern API classes are imported."""
    required = [
        "FrameConfig",
        "Channel",
        "MetadataKey",
        "TextStyle",
        "ImageStyle",
        "ProgressStyle",
    ]
    missing = [req for req in required if req not in content]
    if not missing:
        return content

    import_line = f"from pyvisualiser import {', '.join(missing)}\n"
    # Insert after docstring or future imports
    lines = content.splitlines(keepends=True)
    insert_idx = 0
    in_docstring = False

    for idx, line in enumerate(lines):
        if line.strip().startswith(('"""', "'''")):
            if not in_docstring:
                in_docstring = True
                continue
            else:
                in_docstring = False
                insert_idx = idx + 1
                break
        elif line.startswith("import ") or line.startswith("from "):
            insert_idx = idx
            break

    lines.insert(insert_idx, import_line)
    return "".join(lines)


def refactor_frame_init(content: str) -> str:
    """
    Refactors:
        Frame.__init__(self, platform, theme='hifi', background=BG, padding=10, outline=OUT)
        super().__init__(platform, theme='hifi', background=BG)
    Into:
        super().__init__(platform, config=FrameConfig(theme='hifi', background=BG, padding=10, outline=OUT))
    """
    pattern = re.compile(
        r"(?:Frame\.__init__|super\(\)\.__init__)\s*\(\s*self\s*,\s*(\w+)\s*,\s*([^)]+)\)",
        re.MULTILINE
    )

    def _replace(match):
        parent_var = match.group(1)
        args_str = match.group(2)
        
        # Don't modify if already using config=
        if "config=" in args_str:
            return match.group(0)

        # Parse known config arguments
        config_params = []
        passthrough = []
        for piece in re.split(r",\s*(?=[a-zA-Z_]\w*\s*=)", args_str):
            piece = piece.strip()
            if not piece:
                continue
            if re.match(r"^(theme|background|outline|padding|scalers|align|square|z_order)\s*=", piece):
                config_params.append(piece)
            else:
                passthrough.append(piece)

        if not config_params:
            return match.group(0)

        cfg_call = f"config=FrameConfig({', '.join(config_params)})"
        all_args = [parent_var, cfg_call] + passthrough
        return f"super().__init__({', '.join(all_args)})"

    return pattern.sub(_replace, content)


def refactor_framers(content: str) -> str:
    """
    Refactors:
        ColFramer(self, col_ratios=(1, 2), padding=10, outline=OUT, padpc=0.1)
    Into:
        ColFramer(self, col_ratios=(1, 2), padpc=0.1, config=FrameConfig(padding=10, outline=OUT))
    """
    pattern = re.compile(
        r"(ColFramer|RowFramer)\s*\(\s*([^,\n\)]+)(?:,\s*col_ratios=([^,\n\)]+)|,\s*row_ratios=([^,\n\)]+)|,\s*([^,\n\)]+))?(.*?)\)",
        re.DOTALL
    )

    def _replace(match):
        framer_type = match.group(1)
        parent = match.group(2).strip()
        r1, r2, r3 = match.group(3), match.group(4), match.group(5)
        rest = match.group(6)

        ratios = r1 or r2 or r3
        if "config=" in rest:
            return match.group(0)

        config_params = []
        framer_params = []

        # Split remaining arguments
        raw_args = [a.strip() for a in re.split(r",\s*(?=[a-zA-Z_]\w*\s*=)", rest) if a.strip()]
        for arg in raw_args:
            if re.match(r"^(padding|outline|background|theme|z_order)\s*=", arg):
                config_params.append(arg)
            else:
                framer_params.append(arg)

        args = [parent]
        if ratios:
            kw = "col_ratios" if "Col" in framer_type else "row_ratios"
            if "=" in ratios:
                args.append(ratios)
            else:
                args.append(f"{kw}={ratios}")

        if framer_params:
            args.extend(framer_params)

        if config_params:
            args.append(f"config=FrameConfig({', '.join(config_params)})")

        return f"{framer_type}({', '.join(args)})"

    return pattern.sub(_replace, content)


def refactor_metadata_widgets(content: str) -> str:
    """
    Refactors:
        MetaData(rows, metadata_type='track', colour='foreground', justify='left')
    Into:
        MetaData(rows, key=MetadataKey.TRACK, visuals=TextStyle(colour='foreground', justify='left'))
    """
    pattern = re.compile(
        r"MetaData\s*\(\s*([^,)]+)\s*,\s*(?:metadata_type=)?['\"]([a-zA-Z_]+)['\"](.*?)\)",
        re.DOTALL
    )

    def _replace(match):
        parent = match.group(1).strip()
        meta_key = match.group(2).strip().upper()
        rest = match.group(3)

        style_args = []
        frame_args = []

        for arg in [a.strip() for a in re.split(r",\s*(?=[a-zA-Z_]\w*\s*=)", rest) if a.strip()]:
            if re.match(r"^(colour|justify|font_size|wrap|typeface)\s*=", arg):
                style_args.append(arg)
            else:
                frame_args.append(arg)

        args = [parent, f"key=MetadataKey.{meta_key}"]
        if frame_args:
            args.extend(frame_args)
        if style_args:
            args.append(f"visuals=TextStyle({', '.join(style_args)})")

        return f"MetaData({', '.join(args)})"

    return pattern.sub(_replace, content)


def refactor_vumeter(content: str) -> str:
    """
    Refactors:
        VUMeter(cols, 'left', style=meter, outline=OUT, background=BG)
    Into:
        VUMeter(cols, channel=Channel.LEFT, visuals=meter, config=FrameConfig(outline=OUT, background=BG))
    """
    pattern = re.compile(
        r"VUMeter\s*\(\s*([^,]+)\s*,\s*['\"](left|right|mono)['\"]\s*(.*?)\)",
        re.DOTALL
    )

    def _replace(match):
        parent = match.group(1).strip()
        channel = match.group(2).strip().upper()
        rest = match.group(3)

        config_args = []
        meter_args = []

        for arg in [a.strip() for a in re.split(r",\s*(?=[a-zA-Z_]\w*\s*=)", rest) if a.strip()]:
            if re.match(r"^(outline|background|padding|scalers|align|square)\s*=", arg):
                config_args.append(arg)
            elif arg.startswith("style="):
                meter_args.append(arg.replace("style=", "visuals="))
            else:
                meter_args.append(arg)

        args = [parent, f"channel=Channel.{channel}"]
        if config_args:
            args.append(f"config=FrameConfig({', '.join(config_args)})")
        if meter_args:
            args.extend(meter_args)

        return f"VUMeter({', '.join(args)})"

    return pattern.sub(_replace, content)


def migrate_file(file_path: Path, dry_run: bool = True) -> bool:
    print(f"\nProcessing: {file_path}")
    original = file_path.read_text(encoding="utf-8")
    
    modified = original
    modified = refactor_frame_init(modified)
    modified = refactor_framers(modified)
    modified = refactor_metadata_widgets(modified)
    modified = refactor_vumeter(modified)
    modified = ensure_imports(modified)

    if original == modified:
        print("  -> No changes needed.")
        return False

    # Show diff
    diff = list(difflib.unified_diff(
        original.splitlines(),
        modified.splitlines(),
        fromfile=str(file_path),
        tofile=f"{file_path} (refactored)",
        lineterm=""
    ))
    print("\n".join(diff[:60]))
    if len(diff) > 60:
        print(f"... ({len(diff) - 60} more diff lines)")

    if not dry_run:
        backup = file_path.with_suffix(file_path.suffix + ".bak")
        backup.write_text(original, encoding="utf-8")
        file_path.write_text(modified, encoding="utf-8")
        print(f"  [+] Saved changes. Backup created at: {backup.name}")
    else:
        print("  [*] Dry-run only. Use --write to apply changes.")

    return True


def main():
    parser = argparse.ArgumentParser(description="pyvisualiser API Screen Refactoring Tool")
    parser.add_argument("files", nargs="+", help="Files to process (e.g. tests/screens3.py)")
    parser.add_argument("--write", action="store_true", help="Apply changes directly to files with .bak backup")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Display diffs without modifying files")
    args = parser.parse_args()

    dry_run = not args.write
    for target in args.files:
        p = Path(target)
        if p.is_file():
            migrate_file(p, dry_run=dry_run)
        else:
            print(f"File not found: {target}")


if __name__ == "__main__":
    main()