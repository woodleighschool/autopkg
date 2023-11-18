# autopkg

Automagically downloads, packages and uploads packages to JAMF.

To get started, download and install [autopkg](https://github.com/autopkg/autopkg/releases), and add this repo:

```bash
autopkg repo-add https://github.com/woodleighschool/autopkg.git
autopkg repo-add https://github.com/grahampugh/jamf-upload
```

Looking through this repo, you will see packages that are setup to download, package and/or upload to JAMF automatically. In the structure:

```
<AppName>
	├── <AppName>.jamf.recipe.yaml
	├── <AppName>.pkg.recipe.yaml
	├── <AppName>.download.recipe.yaml
	└── <AppName>.png
```

# Development

NMP

# Using autopkg

To build packages, use `autopkg run`, eg:

```bash
autopkg run <app>.<action>.recipe.yaml
```

### Explanation of <action>

There are 3 actions (steps) in this setup, `jamf`, `pkg` and `download`.

| Action     | Explanation                                                                                                    |
| ---------- | -------------------------------------------------------------------------------------------------------------- |
| `jamf`     | Uploads the packaged pkg from `pkg` to jamf, and recreates policies                                            |
| `pkg`      | Packages up the `.dmg` (if source is a `.dmg`) to a `.pkg` and auto names the `.pkg` to `<name>-<version>.pkg` |
| `download` | downloads the `.dmg` or `.pkg` and verifies it's authenticity                                                  |
