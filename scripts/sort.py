#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import deepcopy
from io import StringIO
from pathlib import Path

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
except Exception as error:  # noqa: BLE001
    raise SystemExit(f"Missing dependency: ruamel.yaml\n{error}")


ROOT = Path(__file__).resolve().parents[1]
TOP_LEVEL_KEYS = [
    "Identifier",
    "ParentRecipe",
    "MinimumVersion",
    "Input",
    "Process",
]


def key_name(value: object) -> str:
    return value.casefold() if isinstance(value, str) else repr(value).casefold()


def sort_mapping(mapping: CommentedMap, preferred_keys: list[str] | None = None) -> None:
    preferred = [key for key in preferred_keys or [] if key in mapping]
    preferred_set = set(preferred)
    rest = sorted((key for key in mapping if key not in preferred_set), key=key_name)
    for key in preferred + rest:
        mapping.move_to_end(key)


def sort_value(value: object) -> None:
    if isinstance(value, CommentedMap):
        sort_mapping(value)
        for child in value.values():
            sort_value(child)
    elif isinstance(value, CommentedSeq):
        for child in value:
            sort_value(child)


def normalize_recipe(recipe: CommentedMap) -> None:
    recipe.pop("Description", None)
    sort_mapping(recipe, TOP_LEVEL_KEYS)

    recipe_input = recipe.get("Input")
    if isinstance(recipe_input, CommentedMap):
        sort_mapping(recipe_input)
        if "pkginfo" in recipe_input:
            recipe_input.move_to_end("pkginfo")
        for child in recipe_input.values():
            sort_value(child)

    process = recipe.get("Process")
    if isinstance(process, CommentedSeq):
        for step in process:
            if not isinstance(step, CommentedMap):
                continue
            sort_mapping(step, ["Processor", "Arguments"])
            sort_value(step.get("Arguments"))


def mapping_order(value: object) -> object:
    if isinstance(value, CommentedMap):
        return tuple((key, mapping_order(child)) for key, child in value.items())
    if isinstance(value, CommentedSeq):
        return tuple(mapping_order(child) for child in value)
    return None


def load_recipe(path: Path) -> tuple[YAML, CommentedMap] | None:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 10_000
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.explicit_start = True
    yaml.explicit_end = False
    recipe = yaml.load(path.read_text(encoding="utf-8"))
    if not isinstance(recipe, CommentedMap):
        return None
    return yaml, recipe


def process_recipe(path: Path, check: bool) -> bool:
    original = path.read_text(encoding="utf-8")
    loaded = load_recipe(path)
    if loaded is None:
        return True
    yaml, recipe = loaded
    normalized = deepcopy(recipe)
    normalize_recipe(normalized)
    if mapping_order(recipe) == mapping_order(normalized):
        return True
    if not check:
        output = StringIO()
        yaml.dump(normalized, output)
        path.write_text(output.getvalue(), encoding="utf-8")
    return False


def recipe_paths(arguments: list[str]) -> list[Path]:
    if not arguments:
        return sorted(ROOT.rglob("*.recipe.yaml"))
    paths = [Path(argument) for argument in arguments]
    invalid = [
        path
        for path in paths
        if not path.is_file() or not path.name.endswith(".recipe.yaml")
    ]
    if invalid:
        raise SystemExit(f"Not an AutoPkg recipe: {invalid[0]}")
    return sorted(paths)


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize recipes")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("recipes", nargs="*")
    arguments = parser.parse_args()

    recipes = recipe_paths(arguments.recipes)
    changed = [recipe for recipe in recipes if not process_recipe(recipe, arguments.check)]
    if arguments.check and changed:
        for recipe in changed:
            print(recipe.relative_to(ROOT) if recipe.is_relative_to(ROOT) else recipe)
        print(f"{len(changed)} recipes need normalization")
        return 1

    print(f"Normalized {len(changed)} of {len(recipes)} recipes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
