#!/usr/local/autopkg/python

from __future__ import absolute_import

import os
import re
from autopkglib import Processor, ProcessorError  # noqa: F401

__all__ = ["BashVariableExtractor"]


class BashVariableExtractor(Processor):
    """Processor to extract the value of a Bash variable from a given file."""

    description = __doc__
    input_variables = {
        "variable_name": {
            "required": True,
            "description": "Name of the Bash variable to extract.",
        },
        "file_path": {
            "required": True,
            "description": "Path to the Bash file to search in.",
        },
    }
    output_variables = {} # undefined output

    def main(self):
        variable_name = self.env.get("variable_name")
        file_path = self.env.get("file_path")

        if not os.path.exists(file_path):
            raise ProcessorError(f"File {file_path} does not exist.")

        variable_pattern = re.compile(rf"^{variable_name}=['\"]?(.*?)['\"]?$")

        with open(file_path, 'r') as file:
            for line in file:
                match = variable_pattern.match(line.strip())
                if match:
                    self.env[variable_name] = match.group(1)
                    self.output(f"{variable_name} = {self.env[variable_name]}")
                    break
            else:
                raise ProcessorError(
                    f"Variable {variable_name} not found in {file_path}")


if __name__ == "__main__":
    processor = BashVariableExtractor()
    processor.execute_shell()
