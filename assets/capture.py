"""Capture screenshots of HTML visual assets using Playwright."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r"C:\Users\shiva\AppData\Local\Programs\Python\Python311\Lib\site-packages")

import os
from pathlib import Path

ASSETS = Path(__file__).parent
ROOT = ASSETS.parent


def capture(name, viewport_w=1280):
    html_path = ASSETS / f"{name}.html"
    png_path = ASSETS / f"{name}.png"
    if not html_path.exists():
        print(f"SKIP: {html_path} not found")
        return
    print(f"Capturing {html_path} -> {png_path} ...")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": viewport_w, "height": 800})
        page.goto(f"file:///{html_path.resolve().as_posix()}")
        page.wait_for_load_state("networkidle")
        page.screenshot(path=str(png_path), full_page=True)
        browser.close()
    print(f"  Saved: {png_path} ({os.path.getsize(png_path)} bytes)")


if __name__ == "__main__":
    capture("banner", 1280)
    capture("terminal", 900)
    capture("workflow", 1280)
    print("\nDone — all screenshots captured.")
