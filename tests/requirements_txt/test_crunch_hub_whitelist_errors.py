import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Iterator
from unittest.mock import patch

import pytest
import requests

from crunch_convert.requirements_txt import CrunchHubWhitelist


@contextmanager
def _serve(status: int, body: bytes = b"") -> Iterator[tuple[str, list[str]]]:
    paths: list[str] = []

    class Handler(BaseHTTPRequestHandler):

        def do_GET(self):
            paths.append(self.path)

            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    try:
        yield f"http://127.0.0.1:{server.server_port}", paths
    finally:
        server.shutdown()
        server.server_close()


def test_server_error_is_retried_then_raised():
    with _serve(502) as (api_base_url, paths), patch("urllib3.util.retry.time.sleep"):
        whitelist = CrunchHubWhitelist(api_base_url=api_base_url)

        with pytest.raises(requests.HTTPError):
            whitelist.find_library(name="numpy")

    assert len(paths) == 4


def test_client_error_is_raised_without_retry():
    with _serve(400) as (api_base_url, paths):
        whitelist = CrunchHubWhitelist(api_base_url=api_base_url)

        with pytest.raises(requests.HTTPError):
            whitelist.find_library(name="numpy")

    assert len(paths) == 1


def test_empty_content_is_not_found():
    with _serve(200, b'{"content": []}') as (api_base_url, paths):
        whitelist = CrunchHubWhitelist(api_base_url=api_base_url)

        assert whitelist.find_library(name="unknown") is None

    assert len(paths) == 1
