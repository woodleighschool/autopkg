#!/usr/local/autopkg/python

import json
import time
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from Foundation import NSDate, NSMutableURLRequest, NSRunLoop, NSURL, NSURLSession
from autopkglib import Processor, ProcessorError


class EpsonDownloadInfoProvider(Processor):
    description = "Finds an Epson download using Epson Download Center metadata."

    input_variables = {
        "device_id": {
            "required": True,
            "description": "Epson Download Center device ID.",
        },
        "os": {
            "required": True,
            "description": "Epson Download Center operating-system code.",
        },
        "cti": {
            "required": True,
            "description": "Epson content type identifier to select.",
        },
        "region": {
            "required": False,
            "default": "GB",
            "description": "Epson Download Center region code.",
        },
        "language": {
            "required": False,
            "default": "en",
            "description": "Epson Download Center language code.",
        },
        "api_url": {
            "required": False,
            "default": "https://download-center.epson.com/api/v1/modules/",
            "description": "Epson Download Center modules endpoint.",
        },
        "download_base_url": {
            "required": False,
            "default": "https://d21ceiiri21o6e.cloudfront.net",
            "description": "Epson's public file origin used for Download Center files.",
        },
        "request_timeout": {
            "required": False,
            "default": 30,
            "description": "Metadata request timeout in seconds.",
        },
    }
    output_variables = {
        "url": {"description": "Download URL for the selected Epson item."},
        "version": {"description": "Version of the selected Epson item."},
    }

    def main(self):
        query = urlencode(
            {
                "device_id": self.env["device_id"],
                "os": self.env["os"],
                "region": self.env.get("region", "GB"),
                "language": self.env.get("language", "en"),
            }
        )
        api_url = f"{self.env.get('api_url', '').rstrip('/')}/?{query}"
        payload = self._get_json(api_url)

        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            raise ProcessorError("Epson metadata response does not contain an items list")

        cti = str(self.env["cti"])
        matches = [
            item
            for item in items
            if isinstance(item, dict) and str(item.get("cti")) == cti
        ]
        if len(matches) != 1:
            found = ", ".join(
                sorted(
                    f"{item.get('cti')} ({item.get('version')})"
                    for item in items
                    if isinstance(item, dict)
                )
            )
            raise ProcessorError(
                f"Expected one Epson item with CTI {cti}, found {len(matches)}. "
                f"Available items: {found or 'none'}"
            )

        item = matches[0]
        source_url = item.get("url")
        version = item.get("version")
        if not isinstance(source_url, str) or not source_url:
            raise ProcessorError("Selected Epson item does not contain a download URL")
        if not isinstance(version, str) or not version:
            raise ProcessorError("Selected Epson item does not contain a version")

        source = urlsplit(source_url)
        if source.scheme != "https" or source.hostname not in {
            "download-center.epson.com",
            "download3.ebz.epson.net",
        }:
            raise ProcessorError(f"Unexpected Epson download URL: {source_url}")

        filename = source.path.rpartition("/")[2]
        if not filename:
            raise ProcessorError(f"Could not determine filename from Epson URL: {source_url}")

        url = source_url
        if source.hostname == "download-center.epson.com":
            if not source.path.startswith("/f/module/"):
                raise ProcessorError(f"Unexpected Epson Download Center path: {source.path}")
            download_base = urlsplit(self.env.get("download_base_url", ""))
            if download_base.scheme != "https" or not download_base.netloc:
                raise ProcessorError("download_base_url must be an HTTPS URL")
            url = urlunsplit(
                (
                    download_base.scheme,
                    download_base.netloc,
                    quote(source.path, safe="/%"),
                    source.query,
                    "",
                )
            )

        self.env["url"] = url
        self.env["version"] = version
        self.output(f"Found Epson {cti} version {version}: {filename}")

    def _get_json(self, url):
        ns_url = NSURL.URLWithString_(url)
        if ns_url is None:
            raise ProcessorError(f"Invalid Epson metadata URL: {url}")

        timeout = float(self.env.get("request_timeout", 30))
        request = NSMutableURLRequest.requestWithURL_(ns_url)
        request.setTimeoutInterval_(timeout)
        request.setValue_forHTTPHeaderField_("application/json", "Accept")
        request.setValue_forHTTPHeaderField_("Mozilla/5.0", "User-Agent")
        result = {"done": False, "data": None, "response": None, "error": None}

        def completed(data, response, error):
            result.update(done=True, data=data, response=response, error=error)

        task = NSURLSession.sharedSession().dataTaskWithRequest_completionHandler_(
            request, completed
        )
        task.resume()

        deadline = time.monotonic() + timeout
        run_loop = NSRunLoop.currentRunLoop()
        while not result["done"] and time.monotonic() < deadline:
            run_loop.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))

        if not result["done"]:
            task.cancel()
            raise ProcessorError(f"Timed out requesting Epson metadata after {timeout:g}s")
        if result["error"] is not None:
            raise ProcessorError(f"Could not request Epson metadata: {result['error']}")

        response = result["response"]
        status = response.statusCode() if response is not None else None
        if status != 200:
            raise ProcessorError(f"Epson metadata request returned HTTP {status}")

        try:
            return json.loads(bytes(result["data"]).decode("utf-8"))
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ProcessorError(f"Could not parse Epson metadata response: {error}") from error


if __name__ == "__main__":
    PROCESSOR = EpsonDownloadInfoProvider()
    PROCESSOR.execute_shell()
