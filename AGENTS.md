# AutoPkg recipe work

This repository owns Woodleigh's reviewed AutoPkg recipes and processors. `autopkg-gitops`
separately owns the pinned repositories, generated trust overrides, and recipes allowed to run.

When adding an application:

- Prefer an established upstream AutoPkg recipe and recipe chain. Adding an upstream recipe
  repository is fine when it is the sustainable source.
- Inspect an upstream `.munki.` recipe first when one exists, then work backwards through its parent
  chain. Preserve practical Munki metadata and setup behavior that still applies to the current
  release instead of rediscovering only the download mechanics.
- Treat recipes hosted under `github.com/autopkg` as trusted operational evidence, not current truth.
  Check old paths, scripts, permissions and metadata against the present payload and local policy
  before carrying them forward.
- Trace the complete download ancestry. The final download must be verified directly or through a
  trusted parent, normally with code-signature or signing verification.
- Prefer maintained vendor or upstream sources. Do not use fixed-version URLs or fragile download
  workarounds. Custom downloaders and processors are a last resort.
- Keep recipe identifiers under `com.github.woodleighschool.*`, including the `.munki.` recipe type.
  Do not rename Munki recipes to `.woodstar.`.
- Use `com.github.woodleighschool.woodstar.processors/WoodstarMunkiImporter` as the final
  Munki-oriented import step where appropriate.
- Woodstar targets may use only the generic labels `All Hosts`, `All Staff`, and `All Students`.
  Default ordinary requested applications to `All Hosts` with `optional_installs` and
  `managed_updates`; narrow to staff or students only when the request calls for it. Do not invent,
  enumerate, or reuse other operational labels merely because an existing recipe exposes one.
- If no sustainable, verifiable source exists, stop and explain the problem instead of fabricating
  a recipe.
- Keep the change limited to the requested application.

Never execute an AutoPkg recipe or a local processor while handling an issue or preparing or
reviewing a pull request. In particular, do not run `autopkg run` or `mise run local`. Pre-review
validation is limited to `mise run lint` and other repository-owned static checks.

Application additions always produce a draft pull request in this repository. A second draft pull
request in `woodleighschool/autopkg-gitops` is needed only when the recipe introduces a new upstream
recipe repository:

1. This repository contains the recipe or source change.
2. The optional GitOps pull request pins the new upstream repository. Leave the Woodleigh source
   revision for Renovate to update after this pull request merges. Do not edit generated
   `RecipeOverrides` by hand.

Only recipes suitable for unattended recurring checks belong in GitOps. A recipe with a fixed
version or a payload copied from `Assets`, `/Applications`, or another local folder remains an
on-demand source recipe and must not gain a GitOps override. Local icons do not make an otherwise
dynamic recipe on-demand.
There is no separate enabled or disabled list: every override present in GitOps is run.

Keep pull request descriptions proportional to the recipe: reference the request, identify the
chosen ancestry and verification boundary, state whether a new GitOps pin was needed, and record the
static checks run.
