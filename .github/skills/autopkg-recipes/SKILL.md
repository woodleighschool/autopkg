---
name: autopkg-recipes
description: Use when creating, reviewing, or fixing AutoPkg download, package, Munki, or Intune recipes in Woodleigh's recipe repository, including parent selection, source inspection, installs detection, and uninstall behavior.
---

# Woodleigh AutoPkg recipes

Build the smallest recipe chain that turns a maintained, verified source into an honest Munki item.
The templates in this skill are the repository's canonical starting points. Existing recipes may
predate this contract; inspect them only for a specific behavior the templates do not cover.

This skill adapts the practical recipe structure from
[dataJAR's AutoPkg skill](https://github.com/autopkg/dataJAR-recipes/blob/master/.github/skills/autopkg-recipes/SKILL.md)
to Woodleigh's direct Woodstar importer, naming, targeting, and static-review boundaries.

## Build an evidence ladder

Read `AGENTS.md`, then gather only enough evidence to choose a likely-working chain:

1. Search the prepared AutoPkg index by the application name, vendor, and aliases.
2. Inspect the strongest current upstream `.munki.` recipe first, then work backwards through its
   full parent chain. Treat its payload paths, installs, removal, scripts, and artifact variables as
   operational evidence. Do not copy a child's paths while skipping the parent that creates them.
3. Classify the source shape and complexity from that chain. A DMG containing one app or a package
   imported directly by a maintained Munki recipe usually needs no further asset inspection.
4. If material facts remain uncertain and a direct vendor asset URL is available, call
   `inspect-apple-archive` when the tool exists. Good triggers are component or conditional
   packages, nested installers, missing upstream Munki recipes, conflicting paths, or a package
   parent that rewrites scripts or rebuilds the installer.
5. Treat archive inspection as best-effort structural evidence. If it fails once, do not fight the
   tool or recreate macOS archive handling. Fall back to the strongest evidence that has not been
   contradicted by a real run, and keep the resulting assumptions clear in review. Runtime evidence
   outranks an upstream recipe's historical paths.

Do not download and inspect every asset. The tool cannot prove that macOS will mount or install an
artifact, that conditional package choices will execute, or that the resulting app will work. Its
purpose is to replace consequential path guesses cheaply when upstream evidence is incomplete.

The selected chain must still verify the final downloaded app or installer through a maintained
parent or local `CodeSignatureVerifier`. With AutoPkg 3, pin app bundles using their designated
`requirement`; `expected_authority_names` pins installer packages only.

Use `references/source-templates.md` once the source shape is known. Replace every template token
with observed data. Do not leave guessed paths, signatures, receipt identifiers, or scripts.

## Select the local chain

Prefer these shapes, in order:

- A maintained parent already yields a verified DMG containing the app: add one local `.munki`
  recipe and consume the parent's actual artifact output directly, commonly `%dmg_path%` or
  `%pathname%`.
- A maintained parent already yields a verified deployable package: add one local `.munki` recipe
  and consume the parent's actual package output directly. If the upstream `.munki` uses a package
  parent that modifies scripts, payload layout, permissions, or installer behavior, reuse that
  parent rather than partially recreating it below the download recipe.
- A maintained parent yields a verified archive or app that must be converted into a deployable
  DMG: perform only that required conversion in the local `.munki` recipe.
- No sustainable parent exists: add the smallest local `.download` recipe that resolves the latest
  source and verifies it, followed by the matching `.munki` recipe.
- Add a local `.pkg` recipe only when Woodleigh must construct or materially change the installer.

Bind a parent's real output variable at the processor that consumes it. Never insert a recipe or a
`VariableSetter`, `Copier`, `Versioner`, or `PkgCopier` merely to rename the artifact, expose
`pkg_path`, create a versioned cache filename, or mirror an upstream layer. In particular, a
verified DMG can be passed from its real parent output to `MunkiIconExtractor` and
`WoodstarMunkiImporter` as-is.

A `.download` recipe owns only source resolution, download, extraction when verification requires
it, and verification. It does not create Munki metadata or a deployable copy of an already usable
artifact. Version discovery belongs there only when it is necessary to resolve the current download
URL; it is not a reason to rename the downloaded file.

## Construct honest Munki metadata

- Use the exact official product title, including its version where applicable, for `NAME`. Derive
  one folder, filename, and identifier slug by stripping spaces and punctuation while preserving
  product casing: `rekordbox 7` becomes `rekordbox7`, while `Visual Studio Code` becomes
  `VisualStudioCode`. Use `NAME` for Munki `name` and leave `display_name` unset.
- Default to `All Hosts` with `optional_installs` and `managed_updates` unless the request narrows
  the audience. Use only labels allowed by `AGENTS.md`.
- Let `makepkginfo` derive installs and version metadata for an ordinary DMG containing an app.
  Pass the exact app bundle to `munkiimport_appname` when selection is useful.
- For a package, unpack only far enough to derive accurate installs metadata, minimum OS, or an
  icon. Use paths established by its upstream Munki chain or best-effort inspection; do not paste a
  generic component path. Import the original verified package, not the inspection copy.
- Add `MunkiInstallsItemsCreator` only when `makepkginfo` cannot derive correct application installs
  from the imported artifact. Merge its output immediately with an argument-free
  `MunkiPkginfoMerger`; a later explicit version merge is a separate processor step.
- Add an explicit version merge or `version_comparison_key` only when the real app or package proves
  the automatically selected version is wrong.
- Conditional component packages can leave package receipts that do not prove the intended
  component installed. When upstream behavior or a first run exposes that case, declare `installs`
  against a persistent versioned app, bundle, or support path instead of trusting the receipt.
- Extract the icon from the existing DMG or inspected payload. Do not copy an app solely for icon
  extraction.
- Keep application-specific install or postinstall scripts only when current upstream behavior or
  the payload proves they are needed. Prefer the vendor package's supported behavior.

### Uninstall behavior

The uninstall declaration must describe a removal path that actually works:

- A drag-and-drop app imported from a DMG normally uses `remove_copied_items` with unattended
  uninstall enabled.
- A vendor package uses its maintained vendor uninstaller or a narrow, evidenced removal script
  when one exists.
- Use `removepackages` only when the package receipts completely own the intended payload and
  removing those receipts is safe.
- If safe complete removal is not established, omit `uninstallable` and uninstall fields. A missing
  uninstall button is better than a partial or destructive uninstall.

Follow `AGENTS.md` for blocking applications. Omit the field when it merely repeats the app name;
use an explicit empty list only when Munki must not block a safely running app or supervised service.

## Escape the templates deliberately

Use a targeted existing recipe only when the source templates cannot express an observed artifact
fact, such as a nested installer, multiple payload apps, a vendor bootstrapper, a required package
transformation, or nonstandard version comparison. State that fact and the smallest template delta
in the pull request. Do not call a source an oddball merely because an existing recipe has more
layers or processors.

The goal is a small recipe that probably works from the best available evidence, not a claim that
static review eliminated runtime failures. A first real run may expose conditional installer or
payload behavior that requires a narrow follow-up; record static checks honestly and do not claim
the recipe or processor ran.

Stop for one concise clarification only when the missing answer changes installation, removal,
edition, channel, licensing, or whether Woodleigh must own a fragile transformation. Stop without a
recipe if no current, sustainable, verifiable source exists.

## Review before publishing

Reject a change that does any of the following without an observed necessity:

- creates a local `.download` below a maintained verified download parent;
- runs `Versioner`, then `Copier`, then `VariableSetter` just to produce a renamed `pkg_path`;
- adds a `.pkg` that only copies an already deployable package;
- stages an app only to generate installs metadata or an icon for a DMG import;
- copies `display_name`, redundant `blocking_applications`, scripts, or uninstall metadata from an
  old upstream recipe without checking current behavior;
- claims safe uninstall, version detection, architecture, or verification without evidence.

Never run `autopkg run`, `mise run local`, or a local processor while preparing or reviewing a pull
request. Run only `mise run lint` and repository-owned static checks. Keep the change and pull
request limited to the requested application.
