# Woodleigh AutoPkg

This repository owns the production Munki recipe list, trusted parent chains, and exact upstream repository revisions used to import applications into Woodstar.

## Local use

Install [Mise](https://mise.jdx.dev/), then run:

```bash
mise install
mise run lint
mise run repos:sync
```

Running recipes requires AutoPkg and Munki's `/usr/local/munki/makepkginfo`.

`autopkg-repos.json` is the source of truth for upstream repositories. Each repository is checked out at its recorded commit in a detached HEAD. Sync refuses repositories with a different origin, local changes, or a revision that is not on the configured branch.

To inspect a pin update:

```bash
mise run repos:diff
```

To run every production recipe, or one recipe:

```bash
WOODSTAR_URL=https://woodstar.example \
  WOODSTAR_TOKEN=secret \
  mise run autopkg:run

WOODSTAR_URL=https://woodstar.example \
  WOODSTAR_TOKEN=secret \
  mise run autopkg:run -- GoogleChrome
```

The wrapper passes the Woodstar values to AutoPkg as `AUTOPKG_WOODSTAR_URL` and `AUTOPKG_WOODSTAR_API_KEY`. Parent trust is mandatory. AutoPkg's raw report contains recipe inputs and is kept only in a temporary local directory; `.artifacts/` receives a scrubbed JSON and Markdown summary.

`scripts/sort.py` normalizes recipe structure and key order. Oxfmt owns formatting for every supported file, including recipe YAML.
