#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections.abc import Mapping
from pathlib import Path

from ruamel.yaml import YAML


ROOT = Path(__file__).resolve().parents[1]
WOODSTAR_IMPORTER = (
    "com.github.woodleighschool.woodstar.processors/WoodstarMunkiImporter"
)


def validate(root: Path) -> None:
    yaml = YAML(typ="safe")
    recipes = sorted(root.rglob("*.munki.recipe.yaml"))
    if not recipes:
        raise ValueError(f"{root}: no Munki recipes found")
    gitops = 0
    for path in recipes:
        recipe = yaml.load(path.read_text(encoding="utf-8"))
        if not isinstance(recipe, Mapping):
            raise ValueError(f"{path}: recipe must be a mapping")
        marker = recipe.get("GitOps")
        if marker is not None and marker is not True:
            raise ValueError(f"{path}: GitOps must be true when present")
        gitops += marker is True
        process = recipe.get("Process")
        if not isinstance(process, list):
            raise ValueError(f"{path}: Process must be an array")
        importers = [
            step
            for step in process
            if isinstance(step, Mapping) and step.get("Processor") == WOODSTAR_IMPORTER
        ]
        if len(importers) != 1:
            raise ValueError(f"{path}: expected exactly one {WOODSTAR_IMPORTER}")
    print(f"Validated {len(recipes)} Woodstar Munki recipes ({gitops} GitOps)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Woodleigh AutoPkg recipes")
    parser.add_argument("--root", type=Path, default=ROOT)
    arguments = parser.parse_args()
    try:
        validate(arguments.root)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
