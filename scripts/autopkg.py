#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "autopkg-repos.json"
DEFAULT_REPO_ROOT = Path(
    os.environ.get("WOODLEIGH_AUTOPKG_REPO_ROOT", Path.home() / "Library/AutoPkg/RecipeRepos")
)
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
NAME_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
REF_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")
RECIPE_PATH_PATTERN = re.compile(r"\.recipe(?:\.(?:plist|yaml|yml))?$")
RECIPE_IDENTIFIER_PATTERN = re.compile(
    r"^Identifier:\s*([A-Za-z0-9._-]+)\s*$", re.MULTILINE
)
SECRET_KEY_PATTERN = re.compile(
    r"(?:api[_-]?key|authorization|credential|password|secret|token)", re.IGNORECASE
)


class Error(RuntimeError):
    pass


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Error(f"Cannot read {path}: {error}") from error
    validate_manifest(manifest, path)
    return manifest


def validate_manifest(manifest: object, source: Path | str) -> None:
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        raise Error(f"{source}: version must be 1")
    repositories = manifest.get("repositories")
    if not isinstance(repositories, list) or not repositories:
        raise Error(f"{source}: repositories must be a non-empty array")

    names: set[str] = set()
    urls: set[str] = set()
    for index, repository in enumerate(repositories):
        location = f"{source}: repositories[{index}]"
        if not isinstance(repository, dict):
            raise Error(f"{location} must be an object")
        if set(repository) != {"name", "url", "ref", "revision"}:
            raise Error(f"{location} must contain name, url, ref, and revision")

        name = repository["name"]
        url = repository["url"]
        ref = repository["ref"]
        revision = repository["revision"]
        if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
            raise Error(f"{location}: invalid name")
        if name in names:
            raise Error(f"{location}: duplicate name {name}")
        names.add(name)
        if not isinstance(url, str) or not url.startswith("https://github.com/"):
            raise Error(f"{location}: url must be an HTTPS GitHub repository")
        canonical_url = url.removesuffix(".git").removesuffix("/")
        if canonical_url in urls:
            raise Error(f"{location}: duplicate url {url}")
        urls.add(canonical_url)
        if not isinstance(ref, str) or not REF_PATTERN.fullmatch(ref) or ".." in ref:
            raise Error(f"{location}: invalid ref")
        if not isinstance(revision, str) or not SHA_PATTERN.fullmatch(revision):
            raise Error(f"{location}: revision must be a lowercase 40-character SHA")


def git(path: Path, *arguments: str, capture: bool = False) -> str:
    command = ["git", "-C", str(path), *arguments]
    result = subprocess.run(
        command,
        check=False,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if result.returncode:
        detail = result.stderr.strip() if result.stderr else ""
        raise Error(f"Command failed: {' '.join(command)}{': ' + detail if detail else ''}")
    return result.stdout.strip() if result.stdout else ""


def canonical_url(value: str) -> str:
    return value.removesuffix(".git").removesuffix("/")


def sync_repositories(manifest: dict[str, Any], repo_root: Path) -> list[Path]:
    repo_root.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for repository in manifest["repositories"]:
        destination = repo_root / repository["name"]
        if not destination.exists():
            result = subprocess.run(
                ["git", "clone", repository["url"], str(destination)],
                check=False,
            )
            if result.returncode:
                raise Error(f"Could not clone {repository['url']}")
        if not (destination / ".git").is_dir():
            raise Error(f"{destination} exists but is not a Git repository")

        origin = git(destination, "remote", "get-url", "origin", capture=True)
        if canonical_url(origin) != canonical_url(repository["url"]):
            raise Error(f"{destination}: origin is {origin}, expected {repository['url']}")
        if git(destination, "status", "--porcelain", capture=True):
            raise Error(f"{destination}: refusing to change a dirty checkout")

        ref = repository["ref"]
        revision = repository["revision"]
        git(
            destination,
            "fetch",
            "--no-tags",
            "origin",
            f"+refs/heads/{ref}:refs/remotes/origin/{ref}",
        )
        git(destination, "cat-file", "-e", f"{revision}^{{commit}}")
        result = subprocess.run(
            [
                "git",
                "-C",
                str(destination),
                "merge-base",
                "--is-ancestor",
                revision,
                f"refs/remotes/origin/{ref}",
            ],
            check=False,
        )
        if result.returncode:
            raise Error(f"{repository['name']}: {revision} is not on origin/{ref}")
        git(destination, "checkout", "--detach", "--force", revision)
        print(f"{repository['name']}: {revision[:12]}")
        paths.append(destination)
    return paths


def load_old_manifest(base: str | None, old_manifest: Path | None) -> dict[str, Any] | None:
    if old_manifest:
        return load_manifest(old_manifest)
    if not base:
        return None
    result = subprocess.run(
        ["git", "show", f"{base}:autopkg-repos.json"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        return None
    try:
        manifest = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise Error(f"Invalid autopkg-repos.json at {base}: {error}") from error
    validate_manifest(manifest, f"{base}:autopkg-repos.json")
    return manifest


def compare_url(url: str, old_revision: str, new_revision: str) -> str:
    return f"{canonical_url(url)}/compare/{old_revision}...{new_revision}"


def relevant_changes(name: str, changed_paths: list[str]) -> list[str]:
    trust_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "RecipeOverrides").glob("*.munki.recipe.yaml"))
    )
    relevant = [path for path in changed_paths if f"/{name}/{path}" in trust_text]
    if name == "com.github.woodleighschool.woodstar":
        relevant.extend(path for path in changed_paths if path.startswith("autopkg/"))
    return sorted(set(relevant))


def diff_repositories(
    manifest: dict[str, Any],
    old_manifest: dict[str, Any] | None,
    repo_root: Path,
) -> dict[str, Any]:
    if old_manifest is None:
        return {"baseline": False, "changes": []}

    old_by_name = {repository["name"]: repository for repository in old_manifest["repositories"]}
    changes: list[dict[str, Any]] = []
    for repository in manifest["repositories"]:
        old = old_by_name.get(repository["name"])
        if not old or old["revision"] == repository["revision"]:
            continue
        destination = repo_root / repository["name"]
        old_revision = old["revision"]
        new_revision = repository["revision"]
        try:
            git(destination, "cat-file", "-e", f"{old_revision}^{{commit}}")
        except Error:
            git(destination, "fetch", "--no-tags", "origin", old_revision)
        paths = git(
            destination,
            "diff",
            "--name-only",
            old_revision,
            new_revision,
            capture=True,
        ).splitlines()
        changes.append(
            {
                "name": repository["name"],
                "ref": repository["ref"],
                "old_revision": old_revision,
                "new_revision": new_revision,
                "compare_url": compare_url(repository["url"], old_revision, new_revision),
                "changed_paths": paths,
                "changed_recipe_paths": [
                    path for path in paths if RECIPE_PATH_PATTERN.search(path)
                ],
                "changed_python_paths": [path for path in paths if path.endswith(".py")],
                "relevant_paths": relevant_changes(repository["name"], paths),
            }
        )
    return {"baseline": True, "changes": changes}


def diff_markdown(report: dict[str, Any]) -> str:
    lines = ["## AutoPkg upstream changes", ""]
    if not report["baseline"]:
        lines.append("No previous manifest is available for comparison.")
    elif not report["changes"]:
        lines.append("No pinned upstream revisions changed.")
    else:
        for change in report["changes"]:
            lines.extend(
                [
                    f"### [{change['name']}]({change['compare_url']})",
                    "",
                    f"`{change['old_revision'][:12]}` to `{change['new_revision'][:12]}` on `{change['ref']}`",
                    "",
                    (
                        f"Changed {len(change['changed_paths'])} files: "
                        f"{len(change['changed_recipe_paths'])} recipes and "
                        f"{len(change['changed_python_paths'])} Python files."
                    ),
                    "",
                ]
            )
            relevant = change["relevant_paths"]
            if relevant:
                lines.append("Files used by the production recipe chains:")
                lines.append("")
                lines.extend(f"- `{path}`" for path in relevant)
            else:
                lines.append("No changed file is directly referenced by current parent trust metadata.")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def recipe_identifiers() -> list[str]:
    try:
        recipe_list = plistlib.loads((ROOT / "recipe-list.munki.xml").read_bytes())
    except (OSError, plistlib.InvalidFileException) as error:
        raise Error(f"Invalid recipe-list.munki.xml: {error}") from error
    if not isinstance(recipe_list, dict):
        raise Error("recipe-list.munki.xml must be a dictionary")
    recipes = recipe_list.get("recipes")
    if not isinstance(recipes, list) or not all(isinstance(recipe, str) for recipe in recipes):
        raise Error("recipe-list.munki.xml recipes must be an array of identifiers")
    return recipes


def tracked_override_identifiers() -> set[str]:
    identifiers: set[str] = set()
    for path in (ROOT / "RecipeOverrides").glob("*.munki.recipe.yaml"):
        try:
            match = RECIPE_IDENTIFIER_PATTERN.search(path.read_text(encoding="utf-8"))
        except OSError as error:
            raise Error(f"Cannot read {path}: {error}") from error
        if not match:
            raise Error(f"{path}: missing or invalid Identifier")
        identifier = match.group(1)
        if identifier in identifiers:
            raise Error(f"Duplicate tracked override identifier: {identifier}")
        identifiers.add(identifier)
    return identifiers


def validate_recipes() -> None:
    recipes = recipe_identifiers()
    if len(recipes) != len(set(recipes)):
        raise Error("recipe-list.munki.xml contains duplicate recipes")
    tracked = tracked_override_identifiers()
    missing = sorted(set(recipes) - tracked)
    if missing:
        raise Error(f"Production recipes missing tracked overrides: {missing}")
    print(f"Validated {len(recipes)} production recipes and {len(tracked)} tracked overrides")


def resolve_recipes(requested: list[str], production: list[str]) -> list[str]:
    recipe_inputs = {
        input_name: identifier
        for identifier in production
        for input_name in (identifier, identifier.removeprefix("local.munki."))
    }
    unknown = sorted(set(requested) - recipe_inputs.keys())
    if unknown:
        raise Error(f"Not a production recipe: {', '.join(unknown)}")
    return [recipe_inputs[recipe] for recipe in requested] if requested else production


def scrub(value: object, secrets: list[str]) -> object:
    if isinstance(value, dict):
        return {
            str(key): "[redacted]" if SECRET_KEY_PATTERN.search(str(key)) else scrub(child, secrets)
            for key, child in value.items()
        }
    if isinstance(value, list):
        return [scrub(child, secrets) for child in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, "[redacted]")
    return value


def summary_results(report_path: Path, secrets: list[str]) -> list[dict[str, Any]]:
    if not report_path.exists():
        return []
    try:
        report = plistlib.loads(report_path.read_bytes())
    except (OSError, plistlib.InvalidFileException):
        return []
    summaries: list[dict[str, Any]] = []
    if not isinstance(report, list):
        return summaries
    for recipe in report:
        if not isinstance(recipe, list):
            continue
        for step in recipe:
            if not isinstance(step, dict) or not isinstance(step.get("Output"), dict):
                continue
            for key, value in step["Output"].items():
                if str(key).endswith("_summary_result"):
                    summaries.append(
                        {
                            "processor": step.get("Processor", "unknown"),
                            "result": scrub(value, secrets),
                        }
                    )
    return summaries


def run_markdown(result: dict[str, Any]) -> str:
    status = "succeeded" if result["exit_code"] == 0 else "failed"
    lines = ["## AutoPkg run", "", f"**Status:** {status}", "", "**Recipes:**"]
    lines.extend(f"- `{recipe}`" for recipe in result["recipes"])
    lines.extend(["", f"**Pinned repositories:** {len(result['repositories'])}", ""])
    if result["summaries"]:
        lines.append("### Processor summaries")
        lines.append("")
        for summary in result["summaries"]:
            text = summary["result"].get("summary_text", "result") if isinstance(summary["result"], dict) else "result"
            lines.append(f"- **{summary['processor']}:** {text}")
    else:
        lines.append("No processor summary results were reported.")
    return "\n".join(lines).rstrip() + "\n"


def append_github_summary(markdown: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with Path(summary_path).open("a", encoding="utf-8") as summary:
            summary.write(markdown)


def write_autopkg_preferences(
    destination: Path,
    manifest: dict[str, Any],
    repo_paths: list[Path],
    override_dir: Path,
) -> None:
    local_recipe_dirs = sorted(
        {
            path.parent
            for path in ROOT.glob("*/*.recipe.yaml")
            if path.parent != ROOT / "RecipeOverrides"
        }
    )
    preferences = {
        "RECIPE_MAP_PATH": str(destination.with_name("recipe-map.json")),
        "RECIPE_OVERRIDE_DIRS": [str(override_dir)],
        "RECIPE_REPOS": {
            str(path): {"URL": repository["url"]}
            for repository, path in zip(manifest["repositories"], repo_paths, strict=True)
        },
        "RECIPE_SEARCH_DIRS": [
            *(str(path) for path in local_recipe_dirs),
            *(str(path) for path in repo_paths),
        ],
    }
    with destination.open("wb") as output:
        plistlib.dump(preferences, output)


def run_autopkg(manifest: dict[str, Any], repo_root: Path, recipes: list[str], output_dir: Path) -> int:
    autopkg = shutil.which("autopkg")
    makepkginfo = Path("/usr/local/munki/makepkginfo")
    if not autopkg:
        raise Error("autopkg is not installed")
    if not makepkginfo.is_file() or not os.access(makepkginfo, os.X_OK):
        raise Error("/usr/local/munki/makepkginfo is required")
    if not os.environ.get("WOODSTAR_URL"):
        raise Error("WOODSTAR_URL is required")
    if not os.environ.get("WOODSTAR_TOKEN"):
        raise Error("WOODSTAR_TOKEN is required")

    selected = resolve_recipes(recipes, recipe_identifiers())

    repo_paths = sync_repositories(manifest, repo_root)
    output_dir.mkdir(parents=True, exist_ok=True)

    child_env = os.environ.copy()
    child_env["AUTOPKG_FAIL_RECIPES_WITHOUT_TRUST_INFO"] = "1"
    child_env["AUTOPKG_WOODSTAR_URL"] = child_env["WOODSTAR_URL"]
    child_env["AUTOPKG_WOODSTAR_API_KEY"] = child_env["WOODSTAR_TOKEN"]
    if child_env.get("ACTIVINSPIRE_SERIAL"):
        child_env["AUTOPKG_ACTIVINSPIRE_SERIAL"] = child_env["ACTIVINSPIRE_SERIAL"]

    with tempfile.TemporaryDirectory(prefix="woodleigh-autopkg-") as temporary:
        temporary_path = Path(temporary)
        override_dir = temporary_path / "overrides"
        override_dir.mkdir()
        for source in (ROOT / "RecipeOverrides").glob("*.munki.recipe.yaml"):
            shutil.copy2(source, override_dir / source.name)
        report_path = temporary_path / "autopkg-results.plist"
        preferences_path = temporary_path / "autopkg-preferences.plist"
        write_autopkg_preferences(preferences_path, manifest, repo_paths, override_dir)

        generated = subprocess.run(
            [autopkg, "generate-recipe-map", f"--prefs={preferences_path}"],
            env=child_env,
            check=False,
        )
        if generated.returncode:
            raise Error("AutoPkg could not generate the recipe map")

        command = [
            autopkg,
            "run",
            "--quiet",
            f"--prefs={preferences_path}",
            "--report-plist",
            str(report_path),
            *selected,
        ]
        completed = subprocess.run(command, env=child_env, check=False)
        summaries = summary_results(report_path, [child_env["WOODSTAR_TOKEN"]])

    result = {
        "exit_code": completed.returncode,
        "recipes": selected,
        "repositories": {
            repository["name"]: repository["revision"] for repository in manifest["repositories"]
        },
        "parent_trust_enforced": True,
        "summaries": summaries,
    }
    (output_dir / "autopkg-summary.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown = run_markdown(result)
    (output_dir / "autopkg-summary.md").write_text(markdown, encoding="utf-8")
    append_github_summary(markdown)
    return completed.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="GitOps runner for Woodleigh AutoPkg recipes")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate", help="validate the manifest and production recipe list")
    subparsers.add_parser("sync", help="materialize pinned upstream repositories")

    diff = subparsers.add_parser("diff", help="summarize pinned upstream changes")
    diff.add_argument("--base", default=os.environ.get("AUTOPKG_DIFF_BASE", "origin/main"))
    diff.add_argument("--old-manifest", type=Path)
    diff.add_argument("--json", type=Path)
    diff.add_argument("--markdown", type=Path)

    run = subparsers.add_parser("run", help="run production recipes")
    run.add_argument("recipes", nargs="*")
    run.add_argument("--output-dir", type=Path, default=ROOT / ".artifacts")
    return parser


def main() -> int:
    parser = build_parser()
    arguments = parser.parse_args()
    try:
        manifest = load_manifest(arguments.manifest)
        if arguments.command == "validate":
            validate_recipes()
            print(f"Validated {len(manifest['repositories'])} pinned repositories")
            return 0
        if arguments.command == "sync":
            sync_repositories(manifest, arguments.repo_root)
            return 0
        if arguments.command == "diff":
            sync_repositories(manifest, arguments.repo_root)
            old_manifest = load_old_manifest(arguments.base, arguments.old_manifest)
            report = diff_repositories(manifest, old_manifest, arguments.repo_root)
            markdown = diff_markdown(report)
            if arguments.json:
                arguments.json.parent.mkdir(parents=True, exist_ok=True)
                arguments.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            if arguments.markdown:
                arguments.markdown.parent.mkdir(parents=True, exist_ok=True)
                arguments.markdown.write_text(markdown, encoding="utf-8")
            print(markdown, end="")
            append_github_summary(markdown)
            return 0
        if arguments.command == "run":
            return run_autopkg(manifest, arguments.repo_root, arguments.recipes, arguments.output_dir)
    except Error as error:
        parser.error(str(error))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
