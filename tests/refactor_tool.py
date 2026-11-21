#!/usr/bin/env python3
"""
pyvisualiser - Robust AST Screen API Migrator v2
================================================
Parses Python screen files into an Abstract Syntax Tree to accurately refactor:
- Frame.__init__ / super().__init__
- ColFramer & RowFramer (scans padding, outline, background -> config=FrameConfig(...))
- VUMeter & VUFrame
- MetaImages & MetaData (preserving exact string metadata keys)
- Injects required modern imports cleanly.

Usage:
    python tools/migrate_screen_apis_ast_v2.py tests/screens3.py --dry-run
    python tools/migrate_screen_apis_ast.py tests/screens3.py --write
"""

import sys
import ast
import argparse
import difflib
from pathlib import Path


class ComprehensiveTransformer(ast.NodeTransformer):
    """Accurately transforms legacy screen AST nodes into the modern API."""

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)

        func_name = self._get_func_name(node.func)

        # 1. Refactor Frame.__init__ or super().__init__
        if func_name in ("__init__", "super"):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "__init__":
                return self._transform_init_call(node)

        # 2. Refactor ColFramer and RowFramer
        if func_name in ("ColFramer", "RowFramer"):
            return self._transform_framer_call(node)

        # 3. Refactor VUMeter
        if func_name == "VUMeter":
            return self._transform_vumeter_call(node)

        # 4. Refactor MetaData
        if func_name == "MetaData":
            return self._transform_metadata_call(node)

        # 5. Refactor MetaImages
        if func_name == "MetaImages":
            return self._transform_metaimages_call(node)

        return node

    def _get_func_name(self, func_node) -> str:
        if isinstance(func_node, ast.Name):
            return func_node.id
        elif isinstance(func_node, ast.Attribute):
            return func_node.attr
        return ""

    def _extract_config_keywords(self, keywords: list[ast.keyword]) -> tuple[list[ast.keyword], list[ast.keyword]]:
        """Splits keywords into FrameConfig-bound properties vs remaining component properties."""
        config_keys = {"theme", "background", "outline", "padding", "margin", "scalers", "align", "square", "z_order"}
        config_keywords = []
        remaining_keywords = []

        for kw in keywords:
            if kw.arg in config_keys:
                # If there's already a config= keyword, we unpack or merge later; handle basic grouping here
                config_keywords.append(kw)
            else:
                remaining_keywords.append(kw)
        return config_keywords, remaining_keywords

    def _build_frame_config_call(self, config_keywords: list[ast.keyword]) -> ast.keyword:
        return ast.keyword(
            arg="config",
            value=ast.Call(
                func=ast.Name(id="FrameConfig", ctx=ast.Load()),
                args=[],
                keywords=config_keywords
            )
        )

    def _transform_init_call(self, node: ast.Call) -> ast.Call:
        if any(kw.arg == "config" for kw in node.keywords):
            return node

        cfg_kws, rem_kws = self._extract_config_keywords(node.keywords)
        if not cfg_kws:
            return node

        node.keywords = rem_kws + [self._build_frame_config_call(cfg_kws)]
        return node

    def _transform_framer_call(self, node: ast.Call) -> ast.Call:
        if any(kw.arg == "config" for kw in node.keywords):
            return node

        cfg_kws, rem_kws = self._extract_config_keywords(node.keywords)
        if not cfg_kws:
            return node

        node.keywords = rem_kws + [self._build_frame_config_call(cfg_kws)]
        return node

    def _transform_vumeter_call(self, node: ast.Call) -> ast.Call:
        # VUMeter(parent, 'left', style=meter, outline=OUT, background=BG)
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            ch_val = str(node.args[1].value).lower()
            node.args[1] = ast.Attribute(
                value=ast.Name(id="Channel", ctx=ast.Load()),
                attr=ch_val.upper(),
                ctx=ast.Load()
            )

        cfg_kws, rem_kws = [], []
        for kw in node.keywords:
            if kw.arg == "style":
                kw.arg = "visuals"
                rem_kws.append(kw)
            elif kw.arg in {"outline", "background", "padding", "margin", "theme", "z_order", "square", "align", "scalers"}:
                cfg_kws.append(kw)
            else:
                rem_kws.append(kw)

        if cfg_kws:
            rem_kws.append(self._build_frame_config_call(cfg_kws))

        node.keywords = rem_kws
        return node

    def _transform_metadata_call(self, node: ast.Call) -> ast.Call:
        # MetaData(parent, metadata_type='track', colour='foreground')
        # Check if 2nd arg is positional string (e.g. 'track')
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            key_val = str(node.args[1].value)
            node.args[1] = ast.keyword(
                arg="key",
                value=ast.Constant(value=key_val)
            )
            # Convert keyword argument if it was a positional list item
            node.args = [node.args[0]]
            node.keywords.insert(0, ast.keyword(arg="key", value=ast.Constant(value=key_val)))

        style_keys = {"colour", "justify", "font_size", "wrap", "typeface"}
        style_kws, rem_kws = [], []

        for kw in node.keywords:
            if kw.arg in style_keys:
                style_kws.append(kw)
            else:
                rem_kws.append(kw)

        if style_kws:
            style_call = ast.keyword(
                arg="visuals",
                value=ast.Call(
                    func=ast.Name(id="TextStyle", ctx=ast.Load()),
                    args=[],
                    keywords=style_kws
                )
            )
            node.keywords = rem_kws + [style_call]
        else:
            node.keywords = rem_kws

        return node

    def _transform_metaimages_call(self, node: ast.Call) -> ast.Call:
        # MetaImages(parent, 'album', opacity=120, reflection=True, outline=...)
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            key_val = str(node.args[1].value)
            node.args = [node.args[0]]
            node.keywords.insert(0, ast.keyword(arg="key", value=ast.Constant(value=key_val)))

        cfg_kws, style_kws, rem_kws = [], [], []
        for kw in node.keywords:
            if kw.arg in {"outline", "background", "padding", "margin", "square", "z_order", "scalers", "align"}:
                cfg_kws.append(kw)
            elif kw.arg in {"opacity", "reflection", "corner_radius"}:
                style_kws.append(kw)
            else:
                rem_kws.append(kw)

        if style_kws:
            rem_kws.append(ast.keyword(
                arg="visuals",
                value=ast.Call(
                    func=ast.Name(id="ImageStyle", ctx=ast.Load()),
                    args=[],
                    keywords=style_kws
                )
            ))
        if cfg_kws:
            rem_kws.append(self._build_frame_config_call(cfg_kws))

        node.keywords = rem_kws
        return node


def ensure_imports(tree: ast.Module) -> ast.Module:
    required = {"FrameConfig", "Channel", "MetadataKey", "TextStyle", "ImageStyle", "ProgressStyle"}
    existing_imports = set()

    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.names:
            for name in node.names:
                existing_imports.add(name.name)

    missing = required - existing_imports
    if missing:
        import_node = ast.ImportFrom(
            module="pyvisualiser",
            names=[ast.alias(name=m) for m in sorted(missing)],
            level=0
        )
        tree.body.insert(0, import_node)

    return tree


def migrate_file(file_path: Path, dry_run: bool = True) -> bool:
    print(f"\nProcessing (AST v2): {file_path}")
    source_code = file_path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        print(f"  [X] Syntax error parsing {file_path}: {e}")
        return False

    transformer = ComprehensiveTransformer()
    new_tree = transformer.visit(tree)
    new_tree = ensure_imports(new_tree)
    ast.fix_missing_locations(new_tree)

    modified_code = ast.unparse(new_tree)

    if source_code.strip() == modified_code.strip():
        print("  -> No changes needed.")
        return False

    diff = list(difflib.unified_diff(
        source_code.splitlines(),
        modified_code.splitlines(),
        fromfile=str(file_path),
        tofile=f"{file_path} (AST v2 refactored)",
        lineterm=""
    ))
    print("\n".join(diff[:60]))

    if not dry_run:
        backup = file_path.with_suffix(file_path.suffix + ".bak")
        backup.write_text(source_code, encoding="utf-8")
        file_path.write_text(modified_code, encoding="utf-8")
        print(f"  [+] Saved changes. Backup created at: {backup.name}")
    else:
        print("  [*] Dry-run only. Use --write to apply changes.")

    return True


def main():
    parser = argparse.ArgumentParser(description="pyvisualiser AST v2 API Migrator")
    parser.add_argument("files", nargs="+", help="Screen files to process")
    parser.add_argument("--write", action="store_true", help="Apply changes directly")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview diffs")
    args = parser.parse_args()

    for target in args.files:
        p = Path(target)
        if p.is_file():
            migrate_file(p, dry_run=not args.write)


if __name__ == "__main__":
    main()