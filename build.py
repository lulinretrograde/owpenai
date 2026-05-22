#!/usr/bin/env python3

import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from uwuify import uwuify

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

BASE = "https://openai.com"
GH_BASE = "/owpenai"

PAGES = [
    "/",
    "/about",
    "/research",
    "/safety",
    "/blog",
    "/api",
    "/sora",
    "/pricing",
    "/careers",
]

SKIP = {"script", "style", "code", "pre", "noscript"}

docs = Path("docs")
docs.mkdir(exist_ok=True)


def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"  failed {url}: {e}")
        return None


def page_path(url_path):
    clean = url_path.strip("/")
    if not clean:
        return docs / "index.html"
    dest = docs / clean / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def download_asset(path):
    # strip query string for local filename
    local_path = docs / path.lstrip("/").split("?")[0]
    if local_path.exists():
        return
    local_path.parent.mkdir(parents=True, exist_ok=True)
    r = fetch(BASE + path)
    if r:
        local_path.write_bytes(r.content)


def fix_asset_links(soup):
    for tag in soup.find_all("link", href=True):
        href = tag["href"]
        if href.startswith("/_next/"):
            download_asset(href.split("?")[0])
            tag["href"] = GH_BASE + href.split("?")[0]

    for tag in soup.find_all(src=True):
        src = tag["src"]
        if src.startswith("/_next/"):
            download_asset(src.split("?")[0])
            tag["src"] = GH_BASE + src.split("?")[0]


def fix_page_links(soup):
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        p = urllib.parse.urlparse(href)
        if p.netloc in ("", "openai.com", "www.openai.com"):
            path = p.path.rstrip("/") or "/"
            tag["href"] = GH_BASE + ("/" if path == "/" else path + "/")


def uwuify_tree(soup):
    for node in soup.find_all(string=True):
        if node.parent and node.parent.name in SKIP:
            continue
        if not node.strip():
            continue
        node.replace_with(uwuify(str(node)))


def build_page(path):
    print(f"fetching {path}")
    r = fetch(BASE + path)
    if not r:
        return

    soup = BeautifulSoup(r.text, "lxml")

    for tag in soup.find_all("script"):
        tag.decompose()

    fix_asset_links(soup)
    fix_page_links(soup)
    uwuify_tree(soup)

    page_path(path).write_text(str(soup), encoding="utf-8")


for path in PAGES:
    build_page(path)
    time.sleep(1)

print("done. run: python3 -m http.server --directory docs")
