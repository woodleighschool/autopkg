#!/usr/local/autopkg/python
# -*- coding: utf-8 -*-

import os

from autopkglib import Processor, ProcessorError


class PathChmod(Processor):
    description = "Recursively applies chmod to a list of paths. Silently skips paths that don't exist."

    input_variables = {
        "path_list": {
            "required": True,
            "description": "List of paths to chmod recursively.",
        },
        "mode": {
            "required": False,
            "description": "Octal mode to apply (e.g. 0o755). Defaults to 0o755.",
            "default": 0o755,
        },
    }

    output_variables = {}

    def main(self):
        mode = int(self.env.get("mode", 0o755))
        for path in self.env["path_list"]:
            if not os.path.exists(path):
                continue
            for dirpath, dirnames, filenames in os.walk(path):
                try:
                    os.chmod(dirpath, mode | 0o111)
                except OSError as e:
                    raise ProcessorError(f"chmod failed on {dirpath}: {e}")
                for fname in filenames:
                    fpath = os.path.join(dirpath, fname)
                    try:
                        os.chmod(fpath, mode)
                    except OSError as e:
                        raise ProcessorError(f"chmod failed on {fpath}: {e}")
            self.output(f"chmod {oct(mode)} applied recursively to: {path}")


if __name__ == "__main__":
    PROCESSOR = PathChmod()
    PROCESSOR.execute_shell()
