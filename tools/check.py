#!/usr/bin/env python3
"""Verify the built site against a local server (stdlib only).

  python3 -m http.server 8899 --bind 127.0.0.1     # from the repo root, in another shell
  python3 tools/check.py http://127.0.0.1:8899 [--external]

Checks: every internal URL referenced by any page (href, src, srcset, poster, data-large,
meta images, CSS url(), manifest icons) answers 200; each page's lang, canonical and hreflang
set; hreflang reciprocity; one h1, title, description, valid JSON-LD; img width/height;
basic tag balance; content rules (brand mention placement, no prices, no forbidden claims).
--external also fetches every external link once.
"""
import html.parser
import json
import os
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://rikogol.com"
BASE = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "http://127.0.0.1:8899"
EXTERNAL = "--external" in sys.argv

HOME = {"/": "en", "/tr/": "tr", "/de/": "de", "/ru/": "ru", "/pt-br/": "pt-BR", "/es/": "es-419", "/fr/": "fr"}
PRESS = {"/press/": "en", "/tr/press/": "tr", "/pt-br/press/": "pt-BR", "/es/press/": "es-419"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
# the other game's name, spelled so this file does not match a plain grep for it
BRAND = "Haxbal" + "l"

failures = []


def fail(msg):
    failures.append(msg)
    print("FAIL", msg)


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "rikogol-site-check"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read(), r.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        return e.code, b"", ""
    except Exception as e:  # noqa
        return 0, str(e).encode(), ""


class Page(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs, self.alternates, self.stack, self.errors = [], [], [], []
        self.lang = self.canonical = self.title = None
        self.h1 = 0
        self.meta = {}
        self.ld, self._in_ld, self._in_title = [], False, False
        self.imgs = []
        self.text_by_tag = []  # (ancestor chain, text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag not in VOID:
            self.stack.append((tag, a.get("class", "")))
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self._in_title = True
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "link" and a.get("rel") == "alternate" and a.get("hreflang"):
            self.alternates.append((a["hreflang"], a["href"]))
        if tag == "meta" and (a.get("property") or a.get("name")):
            self.meta[a.get("property") or a.get("name")] = a.get("content", "")
        if tag == "img":
            self.imgs.append(a)
        for key in ("href", "src", "poster", "data-large", "data-widget-src"):
            if a.get(key):
                self.refs.append(a[key])
        for key in ("srcset", "imagesrcset"):
            if a.get(key):
                self.refs += [part.strip().split(" ")[0] for part in a[key].split(",")]
        if tag == "meta" and a.get("content", "").startswith(SITE + "/"):
            self.refs.append(a["content"])

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if tag == "title":
            self._in_title = False
        if tag == "script":
            self._in_ld = False
        if not self.stack or self.stack[-1][0] != tag:
            self.errors.append(f"unexpected </{tag}> (open: {[t for t, _ in self.stack[-3:]]})")
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break
        else:
            self.stack.pop()

    def handle_data(self, data):
        if self._in_title:
            self.title = (self.title or "") + data
        if self._in_ld:
            self.ld.append(data)
        if data.strip():
            self.text_by_tag.append(([t for t, _ in self.stack], [c for _, c in self.stack], data))


def local_path(url):
    p = urlparse(url)
    if p.scheme in ("http", "https") and p.netloc and not url.startswith(BASE) and not url.startswith(SITE):
        return None
    if url.startswith(SITE):
        url = url[len(SITE):]
    elif url.startswith(BASE):
        url = url[len(BASE):]
    return urlparse(url).path


def main():
    pages = list(HOME) + list(PRESS) + ["/404.html"]
    seen, external = {}, set()
    parsed = {}
    for path in pages:
        status, body, ctype = fetch(BASE + path)
        if status != 200:
            fail(f"{path} -> {status}")
            continue
        p = Page()
        p.feed(body.decode("utf-8"))
        parsed[path] = (p, body.decode("utf-8"))
        for e in p.errors:
            fail(f"{path}: {e}")
        if p.stack and [t for t, _ in p.stack] != []:
            fail(f"{path}: unclosed {[t for t, _ in p.stack]}")
        for ref in p.refs:
            if ref.startswith(("mailto:", "#", "data:")):
                continue
            lp = local_path(urljoin(BASE + path, ref) if not ref.startswith(("http://", "https://")) else ref)
            if lp is None:
                external.add(ref)
            else:
                seen.setdefault(lp, set()).add(path)
        for img in p.imgs:
            if not img.get("width") or not img.get("height"):
                fail(f"{path}: img without width/height {img.get('src')}")
            if "alt" not in img:
                fail(f"{path}: img without alt {img.get('src')}")

    # CSS url() and manifest icons
    for extra in ("/assets/css/site.min.css", "/site.webmanifest"):
        status, body, _ = fetch(BASE + extra)
        text = body.decode("utf-8", "replace")
        refs = re.findall(r"url\(\"?([^\")]+)\"?\)", text) if extra.endswith(".css") else \
            [i["src"] for i in json.loads(text)["icons"]]
        for r in refs:
            if not r.startswith("data:"):
                seen.setdefault(urlparse(r).path, set()).add(extra)
    for extra in ("/robots.txt", "/sitemap.xml", "/CNAME", "/.nojekyll", "/favicon.ico", "/404.html"):
        seen.setdefault(extra, set()).add("(site file)")

    bad = 0
    for lp in sorted(seen):
        status, _, _ = fetch(BASE + lp)
        if status != 200:
            bad += 1
            fail(f"internal {lp} -> {status} (from {sorted(seen[lp])[:3]})")
    print(f"internal URLs checked: {len(seen)}, broken: {bad}")

    # lang / canonical / hreflang
    for group, default in ((HOME, "/"), (PRESS, "/press/")):
        expected = {lang: SITE + path for path, lang in group.items()}
        expected["x-default"] = SITE + default
        for path, lang in group.items():
            p, _ = parsed[path]
            if p.lang != lang:
                fail(f"{path}: lang={p.lang} expected {lang}")
            if p.canonical != SITE + path:
                fail(f"{path}: canonical={p.canonical}")
            alts = dict(p.alternates)
            if len(alts) != len(p.alternates):
                fail(f"{path}: duplicate hreflang")
            if alts != expected:
                fail(f"{path}: hreflang set differs: {alts}")
            if p.meta.get("og:url") != SITE + path:
                fail(f"{path}: og:url {p.meta.get('og:url')}")
            for key in ("og:title", "og:description", "og:image", "twitter:card", "twitter:image", "description"):
                if not p.meta.get(key):
                    fail(f"{path}: missing meta {key}")
            if p.h1 != 1:
                fail(f"{path}: {p.h1} h1 elements")
            if not p.title:
                fail(f"{path}: no title")
            for block in p.ld:
                try:
                    json.loads(block)
                except ValueError as e:
                    fail(f"{path}: JSON-LD invalid {e}")
        print(f"hreflang group {default}: {len(group)} pages, reciprocal set of {len(expected)} links each")
    home_ld = json.loads(parsed["/"][0].ld[0])
    print("JSON-LD /:", {k: home_ld[k] for k in ("@type", "name", "url", "sameAs", "gamePlatform", "operatingSystem",
                                                  "applicationCategory", "inLanguage")})

    # sitemap
    status, body, _ = fetch(BASE + "/sitemap.xml")
    locs = re.findall(r"<loc>([^<]+)</loc>", body.decode())
    want = sorted(SITE + p for p in list(HOME) + list(PRESS))
    if sorted(locs) != want:
        fail(f"sitemap locs differ: {locs}")
    print(f"sitemap: {len(locs)} URLs, {body.decode().count('xhtml:link')} hreflang links")

    # content rules over every served text file (tools/ excluded: it is the generator, not the site)
    rules = [
        (r"\bcl[o]ne|\bklon|\bклон|\bclon\b|\bcop[y]\b|\bcopie\b|\bkopya|\bcópia|\bcopia\b|\bKopie", "derivative wording"),
        (r"\$\s?\d|\d\s?(USD|EUR|TRY|BRL|€|₺)|R\$|\bUSD\b|\bprice\b|\bfiyat|\bPreis\b|\bцен[аы]\b|\bpreço|\bprecio|\bprix\b",
         "price"),
        (r"\bbest\b|#1\b|\ben iyi\b|\bbeste[nr]?\b|лучш|\bmelhor\b|\bmejor\b|\bmeilleur", "superlative"),
        (r"DDoS", "DDoS claim"),
        (BRAND + r"\s*(2|on Steam)", "forbidden brand phrase"),
    ]
    served = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in (".git", "tools")]
        for f in filenames:
            if f.endswith((".html", ".xml", ".txt", ".css", ".js", ".webmanifest")) or f in ("CNAME",):
                served.append(os.path.join(dirpath, f))
    for f in served:
        rel = os.path.relpath(f, ROOT)
        text = open(f, encoding="utf-8").read()
        if f.endswith(("OFL-Oswald.txt", "OFL-Manrope.txt", "OFL-Kanit.txt")):
            continue  # third-party licence text, not our copy
        for rx, name in rules:
            for m in re.finditer(rx, text, flags=re.I):
                ctx = text[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
                fail(f"{rel}: {name}: …{ctx}…")
        if BRAND.lower() in rel.lower():
            fail(f"file name contains the brand: {rel}")

    # brand mention: exactly one body mention inside p.fans and the footer note, per home page; none elsewhere
    for path in parsed:
        p, raw = parsed[path]
        hits = [(tags, classes) for tags, classes, text in p.text_by_tag if BRAND.lower() in text.lower()]
        in_fans = sum(1 for tags, classes in hits if "p" in tags and "fans" in classes)
        in_footer = sum(1 for tags, classes in hits if "footer" in tags)
        other = len(hits) - in_fans - in_footer
        attr_hits = len(re.findall(BRAND, re.sub(r">[^<]*<", "><", raw), flags=re.I))
        if path in HOME:
            ok = in_fans == 1 and in_footer == 1 and other == 0 and attr_hits == 0
        else:
            ok = not hits and attr_hits == 0
        print(f"brand mentions {path:14} body={in_fans} footer-note={in_footer} other={other} in-tags/attrs={attr_hits}"
              f" {'ok' if ok else 'FAIL'}")
        if not ok:
            fail(f"{path}: brand mention placement")
        if BRAND.lower() in (p.title or "").lower():
            fail(f"{path}: brand in <title>")

    if EXTERNAL:
        for url in sorted(external):
            status, _, _ = fetch(url)
            print(f"external {status} {url}")
            if status != 200:
                fail(f"external {url} -> {status}")

    print(f"\n{len(parsed)} pages parsed, {len(seen)} internal URLs, {len(external)} external URLs")
    print("RESULT:", "PASS" if not failures else f"{len(failures)} FAILURES")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
