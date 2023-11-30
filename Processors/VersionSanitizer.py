#!/usr/local/autopkg/python

import re
from autopkglib import Processor, ProcessorError

__all__ = ["VersionSanitizer"]


class VersionSanitizer(Processor):
    """Sanitizes version strings based on a specified pattern"""

    input_variables = {
        "pattern": {
            "description": "The pattern to sanitize the version string to. Example: 'x.xx.xx'",
            "required": True,
        }
    }
    output_variables = {}
    description = __doc__

    def sanitize_version(self, version, pattern):
        """Sanitize the version string based on the given pattern"""
        pattern_regex = pattern.replace('x', '\d+')
        match = re.match(pattern_regex, version)
        if match:
            return match.group()
        else:
            raise ProcessorError(
                "Version does not match the specified pattern")

    def main(self):
        version = self.env.get("version", "")
        if not version:
            raise ProcessorError(
                "No version string provided in the environment")

        pattern = self.env["pattern"]
        version = self.sanitize_version(version, pattern)

        self.env["version"] = version
        self.output("Sanitized Version: %s" % version)


if __name__ == "__main__":
    processor = VersionSanitizer()
    processor.execute_shell()
