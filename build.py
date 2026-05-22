#!/usr/bin/env python3
"""
Scrapes key pages from openai.com, uwuifies all visible text, and writes
static HTML into docs/ for GitHub Pages.
"""

import os
import re
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString

from uwuify import uwuify

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

BASE_URL = "https://openai.com"

# Pages to scrape — extend this list as desired
PAGES = [
    "/",
    "/about",
    "/research",
    "/safety",
    "/blog",
    "/api",
    "/chatgpt",
    "/sora",
    "/pricing",
    "/careers",
]

# Tags whose text content should NOT be uwuified
SKIP_TAGS = {"script", "style", "code", "pre", "noscript", "meta", "link"}

DOCS = Path("docs")
DOCS.mkdir(exist_ok=True)


def url_to_path(url_path: str) -> Path:
    """Map a URL path like /about to docs/about/index.html."""
    clean = url_path.strip("/") or "index"
    dest = DOCS / clean / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def rewrite_links(soup: BeautifulSoup, current_path: str) -> None:
    """Rewrite internal hrefs so they work on GitHub Pages."""
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        parsed = urllib.parse.urlparse(href)
        if parsed.netloc in ("", "openai.com", "www.openai.com"):
            path = parsed.path.rstrip("/") or "/"
            if path == "/":
                tag["href"] = "/owpenai/"
            else:
                tag["href"] = f"/owpenai{path}/"
        # leave external links as-is


def uwuify_tree(soup: BeautifulSoup) -> None:
    """Walk every text node and uwuify it in-place."""
    for node in soup.find_all(string=True):
        if node.parent and node.parent.name in SKIP_TAGS:
            continue
        if not node.strip():
            continue
        node.replace_with(uwuify(str(node)))


def fetch(path: str) -> str | None:
    url = BASE_URL + path
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  SKIP {url}: {e}")
        return None


def process_page(path: str) -> None:
    print(f"Fetching {path} ...")
    html = fetch(path)
    if html is None:
        return

    soup = BeautifulSoup(html, "lxml")

    # Remove elements that would break layout or re-fetch scripts
    for tag in soup.find_all(["script"]):
        tag.decompose()

    uwuify_tree(soup)
    rewrite_links(soup, path)

    # Inject a small banner
    banner = soup.new_tag("div", style=(
        "position:fixed;bottom:16px;right:16px;background:#10a37f;"
        "color:#fff;padding:8px 14px;border-radius:999px;"
        "font-family:sans-serif;font-size:14px;z-index:99999;"
        "box-shadow:0 2px 8px rgba(0,0,0,.3);"
    ))
    banner.string = "uwuified by uwu-openai ✨"
    if soup.body:
        soup.body.append(banner)

    dest = url_to_path(path)
    dest.write_text(str(soup), encoding="utf-8")
    print(f"  -> {dest}")


def main():
    for path in PAGES:
        process_page(path)
        time.sleep(1)  # be polite
    print("\nDone! Serve with: python -m http.server --directory docs")


if __name__ == "__main__":
    main()
