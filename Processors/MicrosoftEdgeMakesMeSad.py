#!/usr/local/autopkg/python

import os

from autopkglib import Processor, ProcessorError

__all__ = ["FolderCreator"]


class MicrosoftEdgeMakesMeSad(Processor):
	"""Processor to create folders with specified permissions."""

	description = __doc__
	input_variables = {
		"pathname": {
			"required": True,
			"description": (
				"The full path to the Microsoft Edge package"
			),
		},
	}
	output_variables = {
		"filename": {
			"description": [
				"The name of the payload package inside the distribution package"
			]
		}
	}

	def main(self):
		filepath = self.env.get("pathname")
		filename = os.path.split(filepath)[1]
		
		self.env["filename"] = filename
		self.output("The filename is: %s" % filename)


if __name__ == "__main__":
	processor = MicrosoftEdgeMakesMeSad()
	processor.execute_shell()
