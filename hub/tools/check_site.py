#!/usr/bin/env python3
"""Check the live hub the way a visitor reaches it: crawl every internal page from the start URL, and for each one
check the status code, the security headers, exactly one <h1>, a meta description, a canonical URL and Open Graph
tags; then check every internal link and asset resolves. Standard library only.
Usage: check_site.py [https://captcharena.org/]   (exit 1 on any failure)"""
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

START = sys.argv[1] if len(sys.argv) > 1 else "https://captcharena.org/"
HOST = urllib.parse.urlsplit(START).netloc
UA = "captcharena-site-check/1 (+https://captcharena.org/about/)"
NEED_HEADERS = ["content-security-policy", "x-content-type-options", "referrer-policy", "strict-transport-security"]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.h1, self.meta, self.canonical, self.scripts_inline, self.ids = set(), 0, {}, None, 0, set()
        self._in_script = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "a" and a.get("href"):
            self.links.add(a["href"])
        if tag in ("link", "script", "img") and (a.get("href") or a.get("src")):
            if tag == "link" and a.get("rel") == "canonical":
                self.canonical = a["href"]
            else:
                self.links.add(a.get("href") or a.get("src"))
        if tag == "script" and not a.get("src"):
            self.scripts_inline += 1
        if tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        for k in a:
            if k.startswith("on"):
                self.scripts_inline += 1


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, {k.lower(): v for k, v in r.headers.items()}, r.read(), r.url
    except urllib.error.HTTPError as e:
        return e.code, {k.lower(): v for k, v in e.headers.items()}, e.read(), url


def main():
    fails, seen, queue, anchors, checked_links = [], set(), [START], [], set()
    while queue:
        url = queue.pop()
        if url in seen:
            continue
        seen.add(url)
        status, headers, body, final = fetch(url)
        ctype = headers.get("content-type", "")
        if status != 200:
            fails.append(f"{status} {url}")
            continue
        if "text/html" not in ctype:
            continue
        missing = [h for h in NEED_HEADERS if h not in headers]
        if missing:
            fails.append(f"missing headers {missing} on {url}")
        if "script-src 'self'" not in headers.get("content-security-policy", ""):
            fails.append(f"CSP lacks script-src 'self' on {url}")
        p = Page()
        p.feed(body.decode("utf-8", "replace"))
        if p.h1 != 1:
            fails.append(f"{p.h1} <h1> on {url}")
        if not p.meta.get("description"):
            fails.append(f"no meta description on {url}")
        if not p.meta.get("og:title") or not p.meta.get("og:image"):
            fails.append(f"no Open Graph tags on {url}")
        if p.canonical != final.split("#")[0]:
            fails.append(f"canonical {p.canonical} != {final} on {url}")
        if p.scripts_inline:
            fails.append(f"{p.scripts_inline} inline script(s) or on* handler(s) on {url}")
        for href in p.links:
            absu = urllib.parse.urljoin(final, href)
            parts = urllib.parse.urlsplit(absu)
            if parts.netloc != HOST or parts.scheme not in ("http", "https"):
                continue
            base = absu.split("#")[0]
            if parts.fragment:
                anchors.append((base, parts.fragment, url))
            if base.endswith("/") or base.endswith(".html"):
                queue.append(base)
            elif base not in checked_links:
                checked_links.add(base)
                s, _, _, _ = fetch(base)
                if s != 200:
                    fails.append(f"{s} {base} (linked from {url})")
    # Fragment links must point at an id on the target page.
    idcache = {}
    for base, frag, src in anchors:
        if base not in idcache:
            s, _, b, _ = fetch(base)
            q = Page()
            q.feed(b.decode("utf-8", "replace"))
            idcache[base] = q.ids
        if urllib.parse.unquote(frag) not in idcache[base]:
            fails.append(f"missing anchor #{frag} on {base} (linked from {src})")
    pages = len([u for u in seen])
    print(f"pages crawled: {pages}; other internal files checked: {len(checked_links)}; anchors checked: {len(anchors)}")
    for f in sorted(set(fails)):
        print("FAIL", f)
    print("OK" if not fails else f"{len(set(fails))} failure(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
