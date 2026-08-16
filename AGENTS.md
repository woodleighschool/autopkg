# AutoPkg recipe work

This repository owns Woodleigh's reviewed AutoPkg recipes and processors. `autopkg-gitops`
separately owns the pinned repositories, generated trust overrides, and recipes allowed to run.

When adding an application:

- All managed Macs are Apple Silicon. Use the `arm64` or Apple Silicon variant when upstream offers
  an architecture choice. Intel support is unnecessary unless the request explicitly requires it;
  do not ask for clarification about this.
- `All Hosts` is the normal target and means the managed Apple Silicon fleet. Default ordinary
  requests to `All Hosts` with `optional_installs` and `managed_updates`; do not ask which target to
  use unless the request calls for a narrower audience or different update behaviour.
- Prefer an established upstream AutoPkg recipe and recipe chain. Adding an upstream recipe
  repository is fine when it is the sustainable source.
- Inspect an upstream `.munki.` recipe first when one exists, then work backwards through its parent
  chain. Establish what each parent contributes before selecting the local shape.
- Treat recipes hosted under `github.com/autopkg` as trusted operational evidence, not current truth.
  Check old paths, scripts, permissions and metadata against the present payload and Woodleigh's
  intended behaviour before carrying them forward.
- Keep the local chain as small as Woodleigh policy allows. A `.download` recipe obtains and verifies
  the source artifact. Add a local `.pkg` recipe only when Woodleigh must construct or materially
  modify the deployable artifact. The `.munki` recipe owns Woodleigh and Munki behaviour, including
  metadata, installs detection, icon extraction, cache filename normalization, targeting, import and
  cleanup.
- Do not add an intermediate recipe merely to rename or copy a verified artifact, extract an icon,
  establish Munki metadata, expose `pkg_path`, or imitate the upstream hierarchy. Those operations
  can live in the local `.munki` recipe.
- When an upstream `.pkg` changes installer scripts, permissions, UI, prompts or other installation
  behaviour, determine whether the transformation is required to produce a usable artifact or is an
  operational preference. Reuse required transformations. If adopting optional behaviour would make
  Woodleigh own extra maintenance or fragility and the desired experience is unknown, ask one concise
  question before implementing it.
- Trace the complete download ancestry. The final download must be verified directly or through a
  trusted parent, normally with code-signature or signing verification.
- Prefer maintained vendor or upstream sources. Do not use fixed-version URLs or fragile download
  workarounds. Custom downloaders and processors are a last resort.
- Keep recipe identifiers under `com.github.woodleighschool.*`, including the `.munki.` recipe type.
  Do not rename Munki recipes to `.woodstar.`.
- Use `com.github.woodleighschool.woodstar.processors/WoodstarMunkiImporter` as the final
  Munki-oriented import step where appropriate.
- Woodstar targets may use only the generic labels `All Hosts`, `All Staff`, and `All Students`.
  Narrow to staff or students only when the request calls for it. Do not invent, enumerate, or reuse
  other operational labels merely because an existing recipe exposes one.
- Resolve ordinary implementation choices yourself, including processors, cache filenames and
  obvious recipe-layer decisions. Ask only when missing information materially changes the user or
  device experience, such as optional upstream installer modifications, a genuinely ambiguous
  edition, channel or licence, incompatible uninstall/update behaviour, or the absence of a
  sustainable verified source. When clarification is required, do not make a speculative recipe.
- If no sustainable, verifiable source exists, stop and explain the problem instead of fabricating
  a recipe.
- Keep the change limited to the requested application.

Never execute an AutoPkg recipe or a local processor while handling an issue or preparing or
reviewing a pull request. In particular, do not run `autopkg run` or `mise run local`. Pre-review
validation is limited to `mise run lint` and other repository-owned static checks.

Application additions always produce a pull request in this repository. A second pull
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
