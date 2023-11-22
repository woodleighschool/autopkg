#!/usr/local/autopkg/python

from __future__ import absolute_import

import os
import subprocess
from autopkglib import Processor, ProcessorError  # noqa: F401

__all__ = ["Permer"]


class Permer(Processor):
    """Processor to apply ownership and permissions to files and directories."""

    description = __doc__
    input_variables = {
        "chown": {
            "required": True,
            "description": (
                "List of dictionaries, each specifying 'path', 'user', 'group', "
                "'perms', and 'recursive' for applying ownership and permissions."
            ),
        },
    }
    output_variables = {}

    def main(self):
        chown_list = self.env.get("chown", [])
        for item in chown_list:
            path = item.get("path")
            user = item.get("user")
            group = item.get("group")
            perms = item.get("perms")
            recursive = item.get("recursive", False)

            if not os.path.exists(path):
                raise ProcessorError(f"Path '{path}' does not exist.")

            # Apply user and group
            if user or group:
                user_group = f"{user}:{group}" if user and group else user or group
                chown_command = ["chown"]
                if recursive:
                    chown_command.append("-R")
                chown_command.extend([user_group, path])

                try:
                    subprocess.check_call(chown_command)
                    self.output(f"Applied ownership {user_group} to {path}")
                except subprocess.CalledProcessError as error:
                    raise ProcessorError(f"Failed to apply ownership: {error}")

            # Apply permissions
            if perms:
                chmod_command = ["chmod"]
                if recursive:
                    chmod_command.append("-R")
                chmod_command.extend([perms, path])

                try:
                    subprocess.check_call(chmod_command)
                    self.output(f"Applied permissions {perms} to {path}")
                except subprocess.CalledProcessError as error:
                    raise ProcessorError(
                        f"Failed to apply permissions: {error}")


if __name__ == "__main__":
    processor = Permer()
    processor.execute_shell()
