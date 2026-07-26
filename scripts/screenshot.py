"""Screenshot a locally running page with headless Chromium (Playwright).

Dev-tooling only - lets pages be visually checked without a real browser.
Requires requirements-dev.txt to be installed and `playwright install chromium`
to have been run once.

Usage:
    python scripts/screenshot.py <url> <output.png> [--width 1440] [--height 900] [--mobile]
"""

import argparse

from playwright.sync_api import sync_playwright

MOBILE_WIDTH = 390
MOBILE_HEIGHT = 844


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("output")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    parser.add_argument("--mobile", action="store_true", help="Use a mobile viewport instead")
    args = parser.parse_args()

    width = MOBILE_WIDTH if args.mobile else args.width
    height = MOBILE_HEIGHT if args.mobile else args.height

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})
        page.goto(args.url, wait_until="networkidle")
        page.screenshot(path=args.output, full_page=True)
        browser.close()

    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
