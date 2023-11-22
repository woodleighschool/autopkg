#!/usr/local/autopkg/python

import os
import stat

from autopkglib import Processor, ProcessorError

__all__ = ["FolderCreator"]


class FolderCreator(Processor):
    """Processor to create folders with specified permissions."""

    description = __doc__
    input_variables = {
        "folders": {
            "required": True,
            "description": (
                "An array of dictionaries, each containing 'path' and 'perms' keys."
            ),
        },
    }
    output_variables = {}

    def main(self):
        folders = self.env.get("folders", [])
        for folder in folders:
            path = folder.get("path")
            perms = folder.get("perms")

            if not path or not perms:
                raise ProcessorError(
                    "Both 'path' and 'perms' must be specified for each folder.")

            try:
                if not os.path.exists(path):
                    os.makedirs(path)
                    self.output(f"Created folder: {path}")

                # Set permissions
                # Permissions should be a string like "0755"
                os.chmod(path, int(perms, 8))
                self.output(f"Set permissions {perms} on folder: {path}")

            except Exception as e:
                raise ProcessorError(f"Error creating folder '{path}': {e}")


if __name__ == "__main__":
    processor = FolderCreator()
    processor.execute_shell()
