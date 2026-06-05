#!/usr/bin/env python3
"""
autopkg_recipe_sort.py

Deterministically re-orders keys inside AutoPkg YAML recipes while preserving:
- comments and formatting (via ruamel.yaml round-trip)
- sequence (list) order (e.g., Process steps stay in the same order)
- block scalars (>, |) and quotes

What it sorts:
- top-level mapping keys (using a preferred order + alphabetical fallback)
- Input mapping keys (alphabetical)
- each Process step mapping keys (Processor, Arguments first; then alphabetical)
- Arguments mappings recursively (alphabetical), including nested mappings

Usage:
  # rewrite files in-place
  python3 autopkg_recipe_sort.py /path/to/recipes --inplace

  # write sorted output to stdout (single file)
  python3 autopkg_recipe_sort.py /path/to/recipe.yaml

  # process directory recursively (default: *.yaml, *.yml)
  python3 autopkg_recipe_sort.py /path/to/recipes --inplace --recursive

Notes:
- Requires: ruamel.yaml  (pip install ruamel.yaml)
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, Optional, Set

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
except Exception as e:  # noqa: BLE001
    raise SystemExit(
        "Missing dependency: ruamel.yaml\n"
        "Install with: pip install ruamel.yaml\n"
        f"Import error: {e}"
    )


TOP_LEVEL_PREFERRED_ORDER = [
    "Description",
    "Identifier",
    "ParentRecipe",
    "MinimumVersion",
    "Input",
    "Process",
]


def _sort_key_name(k: object) -> str:
    # Deterministic, case-insensitive sorting for str keys; fallback to repr.
    if isinstance(k, str):
        return k.casefold()
    return repr(k).casefold()


def reorder_commented_map_in_place(
    m: CommentedMap,
    preferred_order: Optional[Iterable[str]] = None,
    *,
    alpha_rest: bool = True,
) -> None:
    """
    Reorder keys in a CommentedMap in-place while letting ruamel keep comments
    attached to keys. This does not invent/remove keys and is deterministic.
    """
    if not isinstance(m, CommentedMap):
        return

    keys = list(m.keys())

    preferred: list[object] = []
    if preferred_order:
        pref_set = set(preferred_order)
        for p in preferred_order:
            if p in m:
                preferred.append(p)
        remaining = [k for k in keys if k not in pref_set]
    else:
        remaining = keys

    if alpha_rest:
        remaining = sorted(remaining, key=_sort_key_name)

    desired = preferred + remaining

    # Move in desired order
    for k in desired:
        if k in m:
            m.move_to_end(k, last=True)


def sort_node(node: object, *, context: str = "") -> None:
    """
    Recursively sort mappings, but never reorder sequences (lists).
    Context is used to apply structure-specific preferred ordering.
    """
    if isinstance(node, CommentedMap):
        if context == "top":
            reorder_commented_map_in_place(node, TOP_LEVEL_PREFERRED_ORDER)
        elif context == "process_step":
            reorder_commented_map_in_place(node, ["Processor", "Arguments"])
        else:
            reorder_commented_map_in_place(node, None)

        # Recurse into children with context hints
        for k, v in list(node.items()):
            if k == "Input":
                sort_node(v, context="input")
            elif k == "Process":
                sort_node(v, context="process")
            elif k == "Arguments":
                sort_node(v, context="arguments")
            else:
                sort_node(v, context="generic")

    elif isinstance(node, CommentedSeq):
        # Never reorder the list itself (keeps Process step order and any
        # commented-out list entries in-place as comments).
        if context == "process":
            for item in node:
                sort_node(item, context="process_step")
        else:
            for item in node:
                sort_node(item, context="generic")

    else:
        # scalars: nothing to do
        return


def load_yaml(path: Path) -> object:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 10_000  # avoid wrapping long lines
    with path.open("r", encoding="utf-8") as f:
        return yaml.load(f)


def dump_yaml(data: object) -> str:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 10_000
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.explicit_start = False
    yaml.explicit_end = False

    from io import StringIO

    buf = StringIO()
    yaml.dump(data, buf)
    return buf.getvalue()


def fix_yaml_newlines(content: str) -> str:
    """
    Post-process YAML to fix newlines:
    - Remove empty lines within Input and Processor blocks
    - Ensure exactly 1 blank line between Input and Process sections
    - Ensure exactly 1 blank line between Processor blocks
    """
    import re

    lines = content.split('\n')
    result = []
    in_block = False
    block_indent = 0
    block_type = None

    for i, line in enumerate(lines):
        # Check if this is a top-level section header (Input, Process, etc)
        section_match = re.match(r'^([A-Z][a-zA-Z]+):\s*$', line)
        if section_match:
            section_name = section_match.group(1)

            # Add blank line before section if needed (except at start)
            if result and result[-1].strip() != '':
                result.append('')

            result.append(line)
            in_block = True
            block_indent = 0
            block_type = section_name
            continue

        # Check if this is a Processor line (within Process block)
        if re.match(r'^(\s*)- Processor:', line):
            processor_indent = len(line) - len(line.lstrip())

            # Add exactly one blank line before processor (unless right after Process:)
            if result and result[-1].strip() != '' and not re.search(r'^\s*Process:\s*$', result[-1]):
                while result and result[-1].strip() == '':
                    result.pop()
                result.append('')

            result.append(line)
            in_block = True
            block_indent = processor_indent
            block_type = 'Processor'
            continue

        # If we're in a block
        if in_block:
            current_indent = len(line) - len(line.lstrip()) if line.strip() else 0

            # Check if we've left the block
            if line.strip() and current_indent <= block_indent and block_type in ('Input', 'Processor'):
                # Leaving block: clean trailing empty lines
                while result and result[-1].strip() == '':
                    result.pop()
                in_block = False
                result.append(line)
                continue

            # Skip empty lines within blocks
            if not line.strip():
                continue

            # Add the line (it's part of the block)
            result.append(line)
        else:
            # Outside blocks
            result.append(line)

    return '\n'.join(result)


def iter_recipe_files(
    root: Path,
    *,
    recursive: bool,
    exts: Set[str],
) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in exts:
            yield root
        return

    if not root.is_dir():
        return

    pattern = "**/*" if recursive else "*"
    for p in root.glob(pattern):
        if p.is_file() and p.suffix.lower() in exts:
            yield p


def process_file(path: Path, *, inplace: bool) -> Optional[str]:
    data = load_yaml(path)
    sort_node(data, context="top")
    out = dump_yaml(data)
    out = fix_yaml_newlines(out)

    if inplace:
        path.write_text(out, encoding="utf-8")
        return None
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministically sort AutoPkg YAML recipe keys.")
    ap.add_argument("path", type=Path, help="Recipe file or directory")
    ap.add_argument("--inplace", action="store_true", help="Rewrite files in-place")
    ap.add_argument("--recursive", action="store_true", help="Recurse into subdirectories")
    ap.add_argument(
        "--ext",
        action="append",
        default=None,
        help="File extension to include (repeatable). Default: .yaml and .yml",
    )
    args = ap.parse_args()

    exts = {".yaml", ".yml"} if not args.ext else {e if e.startswith(".") else f".{e}" for e in args.ext}
    targets = list(iter_recipe_files(args.path, recursive=args.recursive, exts={e.lower() for e in exts}))

    if not targets:
        raise SystemExit(f"No matching recipe files found under: {args.path}")

    # If stdout mode, only allow one file (keeps output unambiguous).
    if not args.inplace and len(targets) != 1:
        raise SystemExit("stdout mode requires exactly one recipe file (use --inplace for batch).")

    if args.inplace:
        for p in targets:
            process_file(p, inplace=True)
        return 0

    out = process_file(targets[0], inplace=False)
    assert out is not None
    print(out, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
