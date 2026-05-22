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
GH_DOMAIN = "https://lulinretrograde.github.io"
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
    "/news",
    "/enterprise",
    "/product",
    "/stories",
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


def to_abs(url, base=None):
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


def local_abs(path):
    return GH_DOMAIN + GH_BASE + path


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
            return f'url({local_abs(local_web_path(to_abs(ref, this_base)))})'

        css_text = re.sub(r'url\(["\']?([^"\')\s]+)["\']?\)', rewrite_ref, css_text)
        dest.write_text(css_text, encoding="utf-8")


LOCAL_PAGES = set(PAGES)


def unwrap_nextjs_image(src):
    if "/_next/image" in src:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(src).query)
        if "url" in qs:
            return qs["url"][0]
    return src


def fix_srcset(srcset):
    out = []
    for part in srcset.split(","):
        part = part.strip()
        pieces = part.split()
        if pieces:
            pieces[0] = unwrap_nextjs_image(pieces[0])
        out.append(" ".join(pieces))
    return ", ".join(out)


def fix_asset_links(soup):
    for tag in soup.find_all("link", href=True):
        href = tag["href"]
        if href.startswith("/_next/"):
            clean = href.split("?")[0]
            download_asset(clean)
            tag["href"] = local_abs(local_web_path(to_abs(clean)))

    for tag in soup.find_all(src=True):
        src = tag["src"]
        if "/_next/image" in src:
            tag["src"] = unwrap_nextjs_image(src)
        elif src.startswith("/_next/"):
            clean = src.split("?")[0]
            download_asset(clean)
            tag["src"] = local_abs(local_web_path(to_abs(clean)))

    for tag in soup.find_all(srcset=True):
        tag["srcset"] = fix_srcset(tag["srcset"])

    for tag in soup.find_all(imagesrcset=True):
        tag["imagesrcset"] = fix_srcset(tag["imagesrcset"])

    for tag in soup.find_all(True, {"data-src": True}):
        tag["data-src"] = unwrap_nextjs_image(tag["data-src"])


def fix_inline_styles(soup):
    for tag in soup.find_all(style=True):
        style = tag["style"]
        if "/_next/" not in style:
            continue

        def rewrite(m):
            url = m.group(1).split("?")[0]
            if url.startswith("/_next/"):
                download_asset(url)
                return f'url({local_abs(local_web_path(to_abs(url)))})'
            return m.group(0)

        tag["style"] = re.sub(r'url\(["\']?(/_next/[^"\')\s?]+)["\']?\)', rewrite, style)


def fix_page_links(soup):
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        p = urllib.parse.urlparse(href)
        if p.netloc in ("", "openai.com", "www.openai.com"):
            path = p.path.rstrip("/") or "/"
            if path in LOCAL_PAGES:
                tag["href"] = local_abs("/" if path == "/" else path + "/")


def add_base_tag(soup):
    head = soup.find("head")
    if not head:
        return
    base = soup.new_tag("base")
    base["href"] = BASE + "/"
    head.insert(0, base)

    for tag in soup.find_all("link", rel=lambda r: r and any(x in r for x in ["icon", "shortcut"])):
        tag.decompose()
    favicon = soup.new_tag("link")
    favicon["rel"] = "icon"
    favicon["href"] = BASE + "/favicon.ico"
    head.append(favicon)


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
    fix_inline_styles(soup)
    fix_page_links(soup)
    add_base_tag(soup)
    uwuify_tree(soup)

    page_path(path).write_text(str(soup), encoding="utf-8")


for path in PAGES:
    build_page(path)
    time.sleep(0.5)

print("done.")
