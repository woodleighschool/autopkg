#!/usr/local/autopkg/python

from __future__ import absolute_import
import xml.etree.ElementTree as ET
from autopkglib import Processor, ProcessorError, URLGetter

__all__ = ["Microsoft365VersionerGetter"]

FEED_URL = "https://macadmins.software/latest.xml"


class Microsoft365VersionerGetter(URLGetter):
    """Provides the version and download URL of the specified package"""

    input_variables = {
        "package_id": {
            "description": "ID of the package to look for.",
            "required": True,
        }
    }
    output_variables = {
        "version": {
            "description": "Version of the specified package.",
        },
        "download_url": {
            "description": "Download URL of the specified package.",
        }
    }
    description = __doc__

    def get_package_info(self, feed_url, package_id):
        """Parse the XML feed for the specified package information"""
        try:
            xml = self.download(feed_url)
        except Exception as e:
            raise ProcessorError("Can't download %s: %s" % (feed_url, e))

        root = ET.fromstring(xml)
        for package in root.iter('package'):
            if package.find('id').text == package_id:
                download_url = package.find('download').text
                version = package.find('cfbundleversion').text
                shortversion = package.find('cfbundleshortversionstring').text
                return download_url, version, shortversion

        raise ProcessorError(
            "Package ID not found in the feed: %s" % package_id)

    def main(self):
        package_id = self.env["package_id"]
        download_url, version, shortversion = self.get_package_info(FEED_URL, package_id)

        self.env["version"] = version
        self.env["download_url"] = download_url
        self.env["shortversion"] = shortversion
        self.output("Found Package: Version %s, Download URL: %s" %
                    (version, download_url))


if __name__ == "__main__":
    processor = Microsoft365VersionerGetter()
    processor.execute_shell()
