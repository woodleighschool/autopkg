# autopkg

Automagically downloads, packages and uploads packages to JAMF.

To get started, download and install [autopkg](https://github.com/autopkg/autopkg/releases), and add this repo:

```bash
autopkg repo-add https://github.com/woodleighschool/autopkg.git
autopkg repo-add https://github.com/grahampugh/jamf-upload
```

```bash
defaults write ~/Library/Preferences/com.github.autopkg.plist JSS_URL "https://<instance>.jamfcloud.com"
defaults write ~/Library/Preferences/com.github.autopkg.plist API_USERNAME '<username>'
defaults write ~/Library/Preferences/com.github.autopkg.plist API_PASSWORD '<password>'
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

You can also build all working recipies using
```bash
autopkg run --recipe-list ~/Library/AutoPkg/RecipeRepos/com.github.woodleighschool.autopkg/run_all.recipe.yaml
```

### Explanation of <action>

There are 3 actions (steps) in this setup, `jamf`, `pkg` and `download`.

| Action     | Explanation                                                                                                    |
| ---------- | -------------------------------------------------------------------------------------------------------------- |
| `jamf`     | Uploads the packaged pkg from `pkg` to jamf, and recreates policies                                            |
| `pkg`      | Packages up the `.dmg` (if source is a `.dmg`) to a `.pkg` and auto names the `.pkg` to `<name>-<version>.pkg` |
| `download` | downloads the `.dmg` or `.pkg` and verifies it's authenticity                                                  |

```yaml
Process:
  - Processor: com.github.woodleighschool.processors/JamfPolicyXMLGenerator
    Arguments:
      policy_name: ALL - %NAME% - ALL
      policy_category: Self Service
      install_button_text: "test"
      scope:
        all_computers: false
        include:
          computers:
            - id: 493
              name: "UPS-HOSKC28"
              udid: "6ECFA7A2-DBC0-53BB-AC2E-7B777ECCFA6C"
          computer_groups:
            - id: 68
              name: "Penbank Campus - Students"
            - id: 15
              name: "Senior Campus - Students"
          departments:
            - id: 11
              name: "Staff"
            - id: 21
              name: "IT"
        exclude:
```