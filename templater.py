import os

# Function to create a file with given content
def create_file(file_path, content):
    with open(file_path, "w") as file:
        file.write(content)

# Take user input for App name
app_name = input(
    "Enter the application name (e.g., 'Autodesk Fusion 360'): ").strip()
# Create recipe directory
dir_name = app_name.replace(" ", "")
if not os.path.exists(dir_name):
    os.makedirs(dir_name)
else:
    print(f"Directory {dir_name} already exists.")

# Write content to yaml's
'''
Content for Content for .pkg.recipe.yaml
'''
pkg_recipe_content = f"""
Identifier: com.github.woodleighschool.pkg.{dir_name}
ParentRecipe: com.github.woodleighschool.download.{dir_name}

Input:
  NAME: {app_name}

Process:
  - Processor: FlatPkgUnpacker
    Arguments:
      destination_path: "%RECIPE_CACHE_DIR%/unpack"
      flat_pkg_path: "%pathname%"

  - Processor: PkgPayloadUnpacker
    Arguments:
      destination_path: "%RECIPE_CACHE_DIR%/payload"
      pkg_payload_path: "%RECIPE_CACHE_DIR%/unpack/<Name>.pkg/Payload"

  - Processor: PlistReader
    Arguments:
      info_path: "%RECIPE_CACHE_DIR%/payload/%NAME%.app"

  - Processor: PkgCopier
    Arguments:
      pkg_path: "%RECIPE_CACHE_DIR%/%NAME%-%version%.pkg"
      source_pkg: "%pathname%"

  - Processor: PathDeleter
    Arguments:
      path_list:
        - "%RECIPE_CACHE_DIR%/payload"
        - "%RECIPE_CACHE_DIR%/unpack"
"""
create_file(os.path.join(
    dir_name, f"{dir_name}.pkg.recipe.yaml"), pkg_recipe_content)

'''
Content for .jamf.recipe.yaml
'''
jamf_recipe_content = f"""
Identifier: com.github.woodleighschool.jamf.{dir_name}
ParentRecipe: com.github.woodleighschool.pkg.{dir_name}

Input:
  NAME: {app_name}
  CATEGORY: <Main Category>
  POLICY_NAME: ALL - %NAME% - ALL
  SELF_SERVICE_DESCRIPTION: >
    <Description>

Process:
  - Processor: com.github.grahampugh.jamf-upload.processors/JamfPackageUploader
    Arguments:
      pkg_category: "%CATEGORY%"

  - Processor: com.github.woodleighschool.processors/JamfPolicyXMLGenerator
    Arguments:
      general:
        policy_name: "%POLICY_NAME%"
        policy_category: Applications
        frequency: Ongoing
        trigger_other: "%NAME%"
      scope:
        all_computers: True
      package:
      self_service:
        show: True
        display_name: "%NAME%"
        description: "%SELF_SERVICE_DESCRIPTION%"
        categories:
          - name: "%CATEGORY%"
            display_in: True
            feature_in: True
      maintenance:
      files_processes:
      user_interaction:
      output: "%RECIPE_CACHE_DIR%/%NAME%"

  - Processor: com.github.grahampugh.jamf-upload.processors/JamfPolicyUploader
    Arguments:
      icon: "%NAME%.png"
      policy_name: "%POLICY_NAME%"
      policy_template: "%RECIPE_CACHE_DIR%/%NAME%.xml"
      replace_policy: "True"
      replace_icon: "True"

  - Processor: com.github.grahampugh.jamf-upload.processors/JamfPatchUploader
    Arguments:
      enabled: "true"
      patch_softwaretitle: "%NAME%"
      patch_name: "%NAME% - Force"
      patch_template: "PolicyPatchTemplateForce.xml"
      patch_icon_policy_name: "%POLICY_NAME%"
      grace_period_duration: "60"
      min_os: ""
      kill_app_name: ""
      kill_app_bundle_id: ""
      replace_patch: "True"

  - Processor: com.github.grahampugh.jamf-upload.processors/JamfPackageCleaner
    Arguments:
      pkg_name_match: "%NAME%"
      versions_to_keep: 1

"""
create_file(os.path.join(
    dir_name, f"{dir_name}.jamf.recipe.yaml"), jamf_recipe_content)

'''
Content for .download.recipe.yaml
'''
download_recipe_content = f"""
Identifier: com.github.woodleighschool.download.{dir_name}

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