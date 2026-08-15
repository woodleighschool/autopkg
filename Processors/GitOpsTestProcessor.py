#!/usr/local/autopkg/python

from autopkglib import Processor


class GitOpsTestProcessor(Processor):
    description = "Records the GitOps test message without changing the host."

    input_variables = {
        "message": {
            "required": True,
            "description": "Message to expose as processor output.",
        }
    }
    output_variables = {
        "gitops_test_message": {
            "description": "The supplied GitOps test message.",
        }
    }

    def main(self):
        self.env["gitops_test_message"] = self.env["message"]
        self.output(f"GitOps test message: {self.env['message']}")


if __name__ == "__main__":
    PROCESSOR = GitOpsTestProcessor()
    PROCESSOR.execute_shell()
