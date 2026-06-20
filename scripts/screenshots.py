#!/usr/bin/env python3
"""Capture homepage screenshots (desktop, mobile, 404) from a built site.

Serves the built output over a short-lived local HTTP server so that
same-origin assets (portrait, font, favicon) resolve, then drives a headless
Chromium via Playwright. Run with the Playwright venv interpreter, e.g.

    ~/.venvs/playwright/bin/python scripts/screenshots.py public tmp/screenshots
"""

from __future__ import annotations

import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright


# name, path, viewport, full_page
SHOTS = [
    ("desktop", "/", {"width": 1280, "height": 800}, False),
    ("mobile", "/", {"width": 390, "height": 844}, True),
    ("404", "/404.html", {"width": 1280, "height": 800}, False),
]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args: object) -> None:  # keep output quiet
        pass


def serve(root: Path) -> tuple[socketserver.TCPServer, int]:
    handler = functools.partial(QuietHandler, directory=str(root))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


def capture(root: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    httpd, port = serve(root)
    base = f"http://127.0.0.1:{port}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            for name, path, viewport, full in SHOTS:
                page = browser.new_page(viewport=viewport, device_scale_factor=2)
                page.goto(base + path)
                page.wait_for_load_state("networkidle")
                target = out / f"{name}.png"
                page.screenshot(path=str(target), full_page=full)
                page.close()
                print(f"wrote {target}")
            browser.close()
    finally:
        httpd.shutdown()


def main(argv: list[str]) -> int:
    root = Path(argv[0]) if argv else Path("public")
    out = Path(argv[1]) if len(argv) > 1 else Path("tmp/screenshots")
    if not (root / "index.html").exists():
        print(f"no built site at {root}/index.html — run `make build` first", file=sys.stderr)
        return 1
    capture(root, out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
