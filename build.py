#!/usr/bin/env python3

import os
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString

from uwuify import uwuify

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

BASE = "https://openai.com"

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

SKIP = {"script", "style", "code", "pre", "noscript"}

docs = Path("docs")
docs.mkdir(exist_ok=True)


def page_path(url_path):
    clean = url_path.strip("/") or "index"
    dest = docs / clean / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def fix_links(soup):
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        p = urllib.parse.urlparse(href)
        if p.netloc in ("", "openai.com", "www.openai.com"):
            path = p.path.rstrip("/") or "/"
            if path == "/":
                tag["href"] = "/owpenai/"
            else:
                tag["href"] = f"/owpenai{path}/"


def uwuify_tree(soup):
    for node in soup.find_all(string=True):
        if node.parent and node.parent.name in SKIP:
            continue
        if not node.strip():
            continue
        node.replace_with(uwuify(str(node)))


def fetch(path):
    try:
        r = requests.get(BASE + path, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"failed {path}: {e}")
        return None


def build_page(path):
    print(f"fetching {path}")
    html = fetch(path)
    if not html:
        return

    soup = BeautifulSoup(html, "lxml")

    for tag in soup.find_all("script"):
        tag.decompose()

    uwuify_tree(soup)
    fix_links(soup)

    banner = soup.new_tag("div", style=(
        "position:fixed;bottom:16px;right:16px;background:#10a37f;"
        "color:#fff;padding:8px 14px;border-radius:999px;"
        "font-family:sans-serif;font-size:14px;z-index:99999;"
        "box-shadow:0 2px 8px rgba(0,0,0,.3);"
    ))
    banner.string = "uwuified >w<"
    if soup.body:
        soup.body.append(banner)

    page_path(path).write_text(str(soup), encoding="utf-8")


for path in PAGES:
    build_page(path)
    time.sleep(1)

print("done. run: python -m http.server --directory docs")
