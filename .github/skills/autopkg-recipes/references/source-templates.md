# Source templates

Choose the template by the artifact delivered by the selected parent, not by the number of layers
in an upstream repository. These are construction templates, not examples to paste unchanged.

- [Verified DMG containing an app](#verified-dmg-containing-an-app)
- [Verified installer package](#verified-installer-package)
- [DMG or ZIP containing an installer package](#dmg-or-zip-containing-an-installer-package)
- [Verified ZIP containing an app](#verified-zip-containing-an-app)
- [Direct DMG or package with no maintained parent](#direct-dmg-or-package-with-no-maintained-parent)

Replace these tokens everywhere:

- `APP_SLUG`: the official product name with spaces and punctuation removed while preserving
  product casing; `rekordbox 7` becomes `rekordbox7` and `Visual Studio Code` becomes
  `VisualStudioCode`. Use it identically for the folder, filename, and identifier component.
- `Application Name`: exact official human-facing product name, including its edition or major
  version when the vendor uses one
- `Application Name.app`: exact installed bundle name
- `PARENT_RECIPE`: selected maintained parent identifier
- `PARENT_DMG_PATH`: exact parent output expression for its verified deployable DMG, commonly
  `%dmg_path%` or `%pathname%`
- `PARENT_PKG_PATH`: exact parent output expression for its verified deployable package, commonly
  `%pkg_path%` or `%pathname%`
- `OBSERVED_COMPONENT_PAYLOAD`: exact expanded path to the relevant component package's `Payload`
- `OBSERVED_PAYLOAD_DESTINATION`: exact staging destination for that component's payload, such as
  `%RECIPE_CACHE_DIR%/payload/root/Applications` when its bare payload contains an app
- `OBSERVED_FAUX_ROOT`: exact staging root whose children mirror installed absolute paths, such as
  `%RECIPE_CACHE_DIR%/payload/root`
- metadata, paths, signing requirements, and certificate authorities: observed current values

## Verified DMG containing an app

When an existing parent produces a verified DMG, identify the exact output variable holding that
DMG and create only this Munki recipe. An ordinary drag-and-drop DMG does not need `Versioner`,
`Copier`, `VariableSetter`, `MunkiInstallsItemsCreator`, or a local `.download` alias.

```yaml
---
Identifier: com.github.woodleighschool.munki.APP_SLUG
ParentRecipe: PARENT_RECIPE
MinimumVersion: "3.0"

Input:
  MUNKI_CATEGORY: CATEGORY
  NAME: Application Name
  pkginfo:
    category: "%MUNKI_CATEGORY%"
    description: >-
      CURRENT DESCRIPTION
    developer: CURRENT DEVELOPER
    name: "%NAME%"
    unattended_install: true
    unattended_uninstall: true
    uninstall_method: remove_copied_items
    uninstallable: true

Process:
  - Processor: com.github.woodleighschool.processors/SwiftIconExtractor
    Arguments:
      app_name: Application Name.app
      pathname: PARENT_DMG_PATH

  - Processor: com.github.woodleighschool.woodstar.processors/WoodstarMunkiImporter
    Arguments:
      icon_path: "%icon_path%"
      munkiimport_appname: Application Name.app
      pkg_path: PARENT_DMG_PATH
      targets:
        exclude: []
        include:
          - actions:
              - optional_installs
              - managed_updates
            label_name: All Hosts
            package:
              strategy: latest

  - Processor: com.github.woodleighschool.woodstar.processors/WoodstarMunkiPackageCleaner
    Arguments:
      keep_version_count: 1
```

If the DMG contains more than one app, `app_name` and `munkiimport_appname` select the intended exact
bundle. Replace both `PARENT_DMG_PATH` tokens with the same observed parent expression. For example,
use `%dmg_path%` when `%pathname%` still refers to the source ZIP. Never create an alias layer to
normalize the variable name.

## Verified installer package

Use the parent's exact package output. If a maintained upstream Munki recipe imports it directly and
its generated receipt metadata is adequate, prefer the direct template. It is intentionally allowed
to have no icon; do not unpack a package merely to make the recipe look complete.

```yaml
---
Identifier: com.github.woodleighschool.munki.APP_SLUG
ParentRecipe: PARENT_RECIPE
MinimumVersion: "3.0"

Input:
  MUNKI_CATEGORY: CATEGORY
  NAME: Application Name
  pkginfo:
    category: "%MUNKI_CATEGORY%"
    description: >-
      CURRENT DESCRIPTION
    developer: CURRENT DEVELOPER
    name: "%NAME%"
    unattended_install: true

Process:
  - Processor: com.github.woodleighschool.woodstar.processors/WoodstarMunkiImporter
    Arguments:
      pkg_path: PARENT_PKG_PATH
      targets:
        exclude: []
        include:
          - actions:
              - optional_installs
              - managed_updates
            label_name: All Hosts
            package:
              strategy: latest

  - Processor: com.github.woodleighschool.woodstar.processors/WoodstarMunkiPackageCleaner
    Arguments:
      keep_version_count: 1
```

### Component package or payload-derived metadata

Use the expanded template only when accurate installs, minimum OS, version comparison, or icon data
requires the payload. Package internals vary, so every component, payload, faux-root, and installed
path must come from the full upstream Munki chain or successful best-effort inspection. The unpacked
payload exists only for inspection; import the original package.

If the upstream Munki recipe parents a package recipe that rewrites installer scripts, permissions,
payload layout, prompts, or other behavior, use that package parent. Never parent the download recipe
and copy only the downstream payload paths.

```yaml
---
Identifier: com.github.woodleighschool.munki.APP_SLUG
ParentRecipe: PARENT_RECIPE
MinimumVersion: "3.0"

Input:
  MUNKI_CATEGORY: CATEGORY
  NAME: Application Name
  pkginfo:
    category: "%MUNKI_CATEGORY%"
    description: >-
      CURRENT DESCRIPTION
    developer: CURRENT DEVELOPER
    name: "%NAME%"
    unattended_install: true

Process:
  - Processor: FlatPkgUnpacker
    Arguments:
      destination_path: "%RECIPE_CACHE_DIR%/unpacked"
      flat_pkg_path: PARENT_PKG_PATH
      purge_destination: true

  - Processor: PkgPayloadUnpacker
    Arguments:
      destination_path: OBSERVED_PAYLOAD_DESTINATION
      pkg_payload_path: OBSERVED_COMPONENT_PAYLOAD
      purge_destination: true

  - Processor: MunkiInstallsItemsCreator
    Arguments:
      derive_minimum_os_version: true
      faux_root: OBSERVED_FAUX_ROOT
      installs_item_paths:
        - /Applications/Application Name.app

  - Processor: MunkiPkginfoMerger

  - Processor: com.github.woodleighschool.processors/SwiftIconExtractor
    Arguments:
      app_name: Application Name.app
      pathname: "%RECIPE_CACHE_DIR%/payload"

  - Processor: PathDeleter
    Arguments:
      path_list:
        - "%RECIPE_CACHE_DIR%/unpacked"
        - "%RECIPE_CACHE_DIR%/payload"

  - Processor: com.github.woodleighschool.woodstar.processors/WoodstarMunkiImporter
    Arguments:
      icon_path: "%icon_path%"
      pkg_path: PARENT_PKG_PATH
      targets:
        exclude: []
        include:
          - actions:
              - optional_installs
              - managed_updates
            label_name: All Hosts
            package:
              strategy: latest

  - Processor: com.github.woodleighschool.woodstar.processors/WoodstarMunkiPackageCleaner
    Arguments:
      keep_version_count: 1
```

This template deliberately makes no uninstall claim. Add one of these only after proving it against
the actual package:

- vendor uninstaller: `uninstall_method: uninstall_script` plus a narrow `uninstall_script`;
- receipts fully and safely own the payload: `uninstall_method: removepackages`;
- installer safely upgrades while its supervised app or service runs: `blocking_applications: []`.

Set `uninstallable: true` and `unattended_uninstall: true` only with a complete safe removal method.
If package metadata reports the wrong application version, first establish the correct installed
version key. Then add only the necessary version merge or `version_comparison_key`; do not add a
cache-copy layer.

For conditional component packages, a receipt may exist even when the intended component was not
installed. If upstream behavior or a real run exposes that case, add `installs` for a persistent
versioned app, bundle, or support path. This is a runtime correction, not a reason to inspect every
ordinary package before review.

## DMG or ZIP containing an installer package

Treat extraction as a required transformation, not a reason to reproduce an upstream download,
package, and Munki hierarchy.

For a package inside a DMG, the download recipe verifies the package through its mounted path:

```yaml
- Processor: URLDownloader
  Arguments:
    url: "%DOWNLOAD_URL%"

- Processor: EndOfCheckPhase

- Processor: CodeSignatureVerifier
  Arguments:
    expected_authority_names:
      - "Developer ID Installer: CURRENT VENDOR (TEAMID)"
      - Developer ID Certification Authority
      - Apple Root CA
    input_path: "%pathname%/Application Installer.pkg"
```

The Munki recipe then extracts the package once because the direct Woodstar importer requires a
real local file. Prepend this to the verified-package template and use the resulting `%pkg_path%`:

```yaml
- Processor: PkgCopier
  Arguments:
    pkg_path: "%RECIPE_CACHE_DIR%/APP_SLUG.pkg"
    source_pkg: "%pathname%/Application Installer.pkg"
```

This is a legitimate `PkgCopier`: it extracts the deployable package from its container. Do not add
`Versioner`, `VariableSetter`, or a separate `.pkg` recipe around it.

For a ZIP containing a package, unarchive to a deterministic directory and verify the extracted
package in the download recipe:

```yaml
- Processor: URLDownloader
  Arguments:
    url: "%DOWNLOAD_URL%"

- Processor: EndOfCheckPhase

- Processor: Unarchiver
  Arguments:
    archive_path: "%pathname%"
    destination_path: "%RECIPE_CACHE_DIR%/expanded"
    purge_destination: true

- Processor: CodeSignatureVerifier
  Arguments:
    expected_authority_names:
      - "Developer ID Installer: CURRENT VENDOR (TEAMID)"
      - Developer ID Certification Authority
      - Apple Root CA
    input_path: "%RECIPE_CACHE_DIR%/expanded/Application Installer.pkg"
```

Use `%RECIPE_CACHE_DIR%/expanded/Application Installer.pkg` directly everywhere the verified-package
template uses `%pkg_path%`. Because the installer lives under `expanded`, move its `PathDeleter`
until after `WoodstarMunkiImporter`; never delete the artifact before import.

## Verified ZIP containing an app

An archive is not directly deployable by Munki. A local download recipe may unarchive and verify it,
and the Munki recipe may create the necessary DMG. If a maintained parent already does the first
half, use it instead of recreating the download recipe and match its actual destination path.

### Download and verification

Use the real current-source provider before `URLDownloader`: direct stable URL, Sparkle,
`GitHubReleasesInfoProvider`, or a narrow vendor-page search. Never hardcode a changing versioned
URL. This skeleton shows only the common terminal flow.

```yaml
---
Identifier: com.github.woodleighschool.download.APP_SLUG
MinimumVersion: "3.0"

Input:
  NAME: Application Name
  DOWNLOAD_URL: CURRENT STABLE OR RESOLVED URL

Process:
  - Processor: URLDownloader
    Arguments:
      filename: APP_SLUG.zip
      url: "%DOWNLOAD_URL%"

  - Processor: EndOfCheckPhase

  - Processor: Unarchiver
    Arguments:
      archive_path: "%pathname%"
      destination_path: "%RECIPE_CACHE_DIR%/expanded"
      purge_destination: true

  - Processor: CodeSignatureVerifier
    Arguments:
      input_path: "%RECIPE_CACHE_DIR%/expanded/Application Name.app"
      requirement: CURRENT DESIGNATED REQUIREMENT
```

### Munki conversion and import

```yaml
---
Identifier: com.github.woodleighschool.munki.APP_SLUG
ParentRecipe: com.github.woodleighschool.download.APP_SLUG
MinimumVersion: "3.0"

Input:
  MUNKI_CATEGORY: CATEGORY
  NAME: Application Name
  pkginfo:
    category: "%MUNKI_CATEGORY%"
    description: >-
      CURRENT DESCRIPTION
    developer: CURRENT DEVELOPER
    name: "%NAME%"
    unattended_install: true
    unattended_uninstall: true
    uninstall_method: remove_copied_items
    uninstallable: true

Process:
  - Processor: PlistReader
    Arguments:
      info_path: "%RECIPE_CACHE_DIR%/expanded/Application Name.app/Contents/Info.plist"
      plist_keys:
        CFBundleShortVersionString: version

  - Processor: com.github.woodleighschool.processors/SwiftIconExtractor
    Arguments:
      pathname: "%RECIPE_CACHE_DIR%/expanded/Application Name.app"

  - Processor: DmgCreator
    Arguments:
      dmg_path: "%RECIPE_CACHE_DIR%/APP_SLUG-%version%.dmg"
      dmg_root: "%RECIPE_CACHE_DIR%/expanded"

  - Processor: PathDeleter
    Arguments:
      path_list:
        - "%RECIPE_CACHE_DIR%/expanded"

  - Processor: com.github.woodleighschool.woodstar.processors/WoodstarMunkiImporter
    Arguments:
      icon_path: "%icon_path%"
      munkiimport_appname: Application Name.app
      pkg_path: "%RECIPE_CACHE_DIR%/APP_SLUG-%version%.dmg"
      targets:
        exclude: []
        include:
          - actions:
              - optional_installs
              - managed_updates
            label_name: All Hosts
            package:
              strategy: latest

  - Processor: com.github.woodleighschool.woodstar.processors/WoodstarMunkiPackageCleaner
    Arguments:
      keep_version_count: 1
```

Use the bundle's actual version key. If the expanded root contains unrelated payload, stage only the
files intended for the DMG; that copy is a required deployable-artifact transformation, not an alias.

## Direct DMG or package with no maintained parent

Create a local `.download` only after the index and upstream repositories show no sustainable
verified parent. Resolve the latest URL before the common terminal flow below.

For a DMG containing an app:

```yaml
- Processor: URLDownloader
  Arguments:
    url: "%DOWNLOAD_URL%"

- Processor: EndOfCheckPhase

- Processor: CodeSignatureVerifier
  Arguments:
    input_path: "%pathname%/Application Name.app"
    requirement: CURRENT DESIGNATED REQUIREMENT
```

For a direct installer package:

```yaml
- Processor: URLDownloader
  Arguments:
    url: "%DOWNLOAD_URL%"

- Processor: EndOfCheckPhase

- Processor: CodeSignatureVerifier
  Arguments:
    expected_authority_names:
      - "Developer ID Installer: CURRENT VENDOR (TEAMID)"
      - Developer ID Certification Authority
      - Apple Root CA
    input_path: "%pathname%"
```

Then use the matching Munki template above. Do not add `Versioner`, `Copier`, `VariableSetter`, or
`PkgCopier` between this verified artifact and its Munki consumer unless an observed artifact fact
requires a real transformation.
