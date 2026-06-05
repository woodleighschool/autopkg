#!/usr/bin/env python3
from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
except Exception as error:  # noqa: BLE001
    raise SystemExit(f"Missing dependency: ruamel.yaml\n{error}")


TOP_LEVEL_KEYS = [
    "Description",
    "Identifier",
    "ParentRecipe",
    "MinimumVersion",
    "Input",
    "Process",
]


def key_name(value: object) -> str:
    return value.casefold() if isinstance(value, str) else repr(value).casefold()


def move_keys(mapping: CommentedMap, ordered_keys: list[object]) -> None:
    for key in ordered_keys:
        if key in mapping:
            mapping.move_to_end(key)


def sort_mapping(mapping: CommentedMap, preferred_keys: list[str] | None = None) -> None:
    preferred = [key for key in preferred_keys or [] if key in mapping]
    preferred_set = set(preferred)
    rest = sorted((key for key in mapping if key not in preferred_set), key=key_name)
    move_keys(mapping, preferred + rest)


def sort_value(value: object) -> None:
    if isinstance(value, CommentedMap):
        sort_mapping(value)
        for child in value.values():
            sort_value(child)
        return

    if isinstance(value, CommentedSeq):
        for child in value:
            sort_value(child)


def sort_process_steps(steps: object) -> None:
    if not isinstance(steps, CommentedSeq):
        return

    for step in steps:
        if isinstance(step, CommentedMap):
            sort_mapping(step, ["Processor", "Arguments"])
            sort_value(step.get("Arguments"))


def sort_recipe(path: Path) -> None:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 10_000
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.explicit_start = True
    yaml.explicit_end = False

    recipe = yaml.load(path.read_text(encoding="utf-8"))
    if not isinstance(recipe, CommentedMap):
        return

    sort_mapping(recipe, TOP_LEVEL_KEYS)
    sort_value(recipe.get("Input"))
    sort_process_steps(recipe.get("Process"))

    output = StringIO()
    yaml.dump(recipe, output)
    path.write_text(output.getvalue(), encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 1:
        raise SystemExit("usage: python sort.py")

    recipes = sorted(Path.cwd().rglob("*.recipe.yaml"))
    for recipe in recipes:
        sort_recipe(recipe)

    print(f"Sorted {len(recipes)} AutoPkg recipes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
