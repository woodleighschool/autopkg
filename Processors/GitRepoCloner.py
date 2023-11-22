#!/usr/local/autopkg/python

from __future__ import absolute_import

import subprocess
import shutil
import os
from autopkglib import Processor, ProcessorError  # noqa: F401

__all__ = ["GitRepoCloner"]


class GitRepoCloner(Processor):
    """Processor to clone a Git repository, overwriting the destination if it already exists."""

    description = __doc__
    input_variables = {
        "repo_url": {
            "required": True,
            "description": "URL of the Git repository to be cloned.",
        },
        "destination_path": {
            "required": True,
            "description": "Path where the Git repository will be cloned.",
        },
        "clone_branch": {
            "required": False,
            "description": "Specific branch to be cloned. Optional.",
        },
        "clone_depth": {
            "required": False,
            "description": "Depth for the clone. Optional, for shallow cloning.",
        },
    }
    output_variables = {}

    def main(self):
        repo_url = self.env.get("repo_url")
        destination_path = self.env.get("destination_path")
        clone_branch = self.env.get("clone_branch", "")
        clone_depth = self.env.get("clone_depth", "")

        # Check if the destination path exists, and if so, delete it
        if os.path.exists(destination_path):
            self.output(
                f"Destination path {destination_path} already exists. Removing it.")
            shutil.rmtree(destination_path)

        clone_command = ["git", "clone", repo_url, destination_path]

        if clone_branch:
            clone_command.extend(["--branch", clone_branch])

        if clone_depth:
            clone_command.extend(["--depth", clone_depth])

        try:
            subprocess.check_call(clone_command)
            self.output(f"Cloned repository {repo_url} to {destination_path}")
        except subprocess.CalledProcessError as error:
            raise ProcessorError(f"Failed to clone repository: {error}")


if __name__ == "__main__":
    processor = GitRepoCloner()
    processor.execute_shell()
