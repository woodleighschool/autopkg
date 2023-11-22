import os

# Function to create a directory
def create_directory(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    else:
        print(f"Directory {dir_name} already exists.")

# Function to create a file with given content
def create_file(file_path, content):
    with open(file_path, "w") as file:
        file.write(content)

# Main script
def main():
    app_name = input(
        "Enter the application name (e.g., 'Autodesk Fusion 360'): ").strip()
    dir_name = app_name.replace(" ", "")
    create_directory(dir_name)

    # Content for AutodeskFusion360.pkg.recipe.yaml
    pkg_recipe_content = f"""Identifier: com.github.woodleighschool.pkg.{dir_name}
ParentRecipe: com.github.woodleighschool.download.{dir_name}

Input:
  NAME: {app_name}

Process:
"""
    create_file(os.path.join(
        dir_name, f"{dir_name}.pkg.recipe.yaml"), pkg_recipe_content)

    # Content for AutodeskFusion360.jamf.recipe.yaml
    jamf_recipe_content = f"""Identifier: com.github.woodleighschool.jamf.{dir_name}
ParentRecipe: com.github.woodleighschool.pkg.{dir_name}

Input:
  NAME: {app_name}
  CATEGORY: <Category>
  POLICY_NAME: ALL - %NAME% - ALL
  SELF_SERVICE_DESCRIPTION: >
    <Description>

    Version: %version%

Process:

  - Processor: com.github.grahampugh.jamf-upload.processors/JamfCategoryUploader
    Arguments:
      category_name: "%CATEGORY%"

  - Processor: com.github.grahampugh.jamf-upload.processors/JamfPackageUploader
    Arguments:
      pkg_category: "%CATEGORY%"

  - Processor: com.github.woodleighschool.processors/JamfPolicyXMLGenerator
    Arguments:
      general:
        policy_name: "%POLICY_NAME%"
        policy_category: Self Service
        trigger_other: "%NAME%"
      scope:
        all_computers: true
      self_service:
        install_button_text: "Install"
        reinstall_button_text: "Reinstall"
        display_name: "%NAME%"
        description: "%SELF_SERVICE_DESCRIPTION%"
        categories:
          - name: "%CATEGORY%"
            display_in: true
            feature_in: false
      maintenance:
        recon: true
      user_interaction:
        message_start: "%NAME% is being installed."
        message_finish: "%NAME% has now been installed."
      output: "%RECIPE_CACHE_DIR%/%NAME%"
      
  - Processor: com.github.grahampugh.jamf-upload.processors/JamfPolicyUploader
    Arguments:
      icon: "%SELF_SERVICE_ICON%"
      policy_name: "%POLICY_NAME%"
      policy_template: "%POLICY_TEMPLATE%"
      replace_policy: "True"
      replace_icon: "True"

  - Processor: com.github.grahampugh.jamf-upload.processors/JamfPackageCleaner
    Arguments:
      pkg_name_match: "%NAME%"
      versions_to_keep: 1
"""
    create_file(os.path.join(
        dir_name, f"{dir_name}.jamf.recipe.yaml"), jamf_recipe_content)

    # Content for AutodeskFusion360.download.recipe.yaml
    download_recipe_content = f"""Identifier: com.github.woodleighschool.download.{dir_name}

Input:
  NAME: {app_name}
  DOWNLOAD_URL: ""

Process:
  - Processor: URLDownloader
    Arguments:
      url: "%DOWNLOAD_URL%"
      filename: "%NAME%.pkg"

  - Processor: EndOfCheckPhase

  - Processor: CodeSignatureVerifier
    Arguments:
      input_path: "%pathname%"
"""
    create_file(os.path.join(
        dir_name, f"{dir_name}.download.recipe.yaml"), download_recipe_content)


if __name__ == "__main__":
    main()
