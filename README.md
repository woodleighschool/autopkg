# Woodleigh AutoPkg Recipes

AutoPkg recipes for Woodleigh's macOS Munki imports and Windows Intune Win32 apps.

## Setup

```bash
autopkg repo-add /Users/ahyde/Library/AutoPkg/RecipeRepos/com.github.woodleighschool.autopkg
autopkg repo-add /Users/ahyde/GitHub/woodleighschool/wintune-autopkg
```

The Intune recipes use the `wintune-autopkg` processors and the standard AutoPkg preferences for Graph credentials.

## Munki

Munki recipes use the `*.munki.recipe.yaml` suffix and are listed in `recipe-list.munki.xml`.

```bash
autopkg run --recipe-list recipe-list.munki.xml
```

Keep `blocking_applications: []` explicit where Munki must not infer blockers from the app title.

## Intune

Intune recipes use the Windows flow:

```text
*.download.recipe.yaml -> *.pkg.recipe.yaml -> *.intune.recipe.yaml
```

The `*.pkg.recipe.yaml` step creates an `.intunewin` in the recipe cache root. The `*.intune.recipe.yaml` step creates or updates the Win32 app in Intune.

```bash
autopkg run --recipe-list recipe-list.intune.xml
```

When a vendor does not provide an AutoPkg-friendly latest version and download source, keep the installer in `Assets/` and package it directly. Local installers are intentionally ignored; recipe icons are tracked when they are used.

Shared macOS and Windows recipes keep the Munki parent identifiers as the plain names. Windows recipe chains include a platform token in the filename and identifier, for example `GoogleChrome-Win64.download.recipe.yaml` and `com.github.woodleighschool.intune.GoogleChrome-Win64`. Use the same shape for future platform splits, such as `-Win32` or `-WinARM64`.
