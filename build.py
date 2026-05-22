#!/usr/bin/env python3

import re
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
    "/api",
    "/sora",
    "/pricing",
    "/careers",
]

SKIP_TAGS = {"script", "style", "code", "pre", "noscript"}

docs = Path("docs")
docs.mkdir(exist_ok=True)

downloaded = set()


def fetch(url, binary=False):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.content if binary else r.text
    except Exception as e:
        print(f"  failed {url}: {e}")
        return None


def local_path(url_path):
    clean = url_path.split("?")[0].lstrip("/")
    return docs / clean


def to_abs(url, base=None):
    """Always return a full https:// URL."""
    if url.startswith("http"):
        return url.split("?")[0]
    if url.startswith("/"):
        return BASE + url.split("?")[0]
    if base:
        return urllib.parse.urljoin(base, url).split("?")[0]
    return BASE + "/" + url.split("?")[0]


def url_to_local(abs_url):
    p = urllib.parse.urlparse(abs_url)
    if p.netloc not in ("openai.com", "www.openai.com"):
        return docs / p.netloc / p.path.lstrip("/")
    return docs / p.path.lstrip("/")


def local_web_path(abs_url):
    p = urllib.parse.urlparse(abs_url)
    if p.netloc not in ("openai.com", "www.openai.com"):
        return "/" + p.netloc + p.path
    return p.path


def download_asset(url, css_base=None):
    abs_u = to_abs(url, css_base)
    if abs_u in downloaded:
        return
    downloaded.add(abs_u)

    dest = url_to_local(abs_u)
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)

    data = fetch(abs_u, binary=True)
    if not data:
        return
    dest.write_bytes(data)

    if abs_u.endswith(".css"):
        css_text = data.decode("utf-8", errors="ignore")
        p = urllib.parse.urlparse(abs_u)
        this_base = p.scheme + "://" + p.netloc + p.path.rsplit("/", 1)[0] + "/"

        for ref in re.findall(r'url\(["\']?([^"\')\s]+)["\']?\)', css_text):
            if not ref.startswith("data:"):
                download_asset(ref, css_base=this_base)

        def rewrite_ref(m):
            ref = m.group(1)
            if ref.startswith("data:"):
                return m.group(0)
            return f'url({GH_BASE}{local_web_path(to_abs(ref, this_base))})'

        css_text = re.sub(r'url\(["\']?([^"\')\s]+)["\']?\)', rewrite_ref, css_text)
        dest.write_text(css_text, encoding="utf-8")


def fix_asset_links(soup):
    for tag in soup.find_all("link", href=True):
        href = tag["href"]
        if href.startswith("/_next/"):
            download_asset(href)
            tag["href"] = GH_BASE + local_web_path(to_abs(href))

    for tag in soup.find_all(src=True):
        src = tag["src"]
        if src.startswith("/_next/"):
            download_asset(src)
            tag["src"] = GH_BASE + local_web_path(to_abs(src))


def fix_page_links(soup):
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        p = urllib.parse.urlparse(href)
        if p.netloc in ("", "openai.com", "www.openai.com"):
            path = p.path.rstrip("/") or "/"
            tag["href"] = GH_BASE + ("/" if path == "/" else path + "/")


def uwuify_tree(soup):
    for node in soup.find_all(string=True):
        if node.parent and node.parent.name in SKIP_TAGS:
            continue
        if not node.strip():
            continue
        node.replace_with(uwuify(str(node)))


def page_path(url_path):
    clean = url_path.strip("/")
    if not clean:
        return docs / "index.html"
    dest = docs / clean / "index.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest


def build_page(path):
    print(f"fetching {path}")
    html = fetch(BASE + path)
    if not html:
        return

    soup = BeautifulSoup(html, "lxml")

    for tag in soup.find_all("script"):
        tag.decompose()

    fix_asset_links(soup)
    fix_page_links(soup)
    uwuify_tree(soup)

    page_path(path).write_text(str(soup), encoding="utf-8")


for path in PAGES:
    build_page(path)
    time.sleep(0.5)

print("done.")
