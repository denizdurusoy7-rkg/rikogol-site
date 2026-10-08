#!/usr/bin/env python3
"""Generate rikogol.com from tools/content/*.py (stdlib only).

  python3 tools/build.py

Writes the language pages, the press pages, 404.html, sitemap.xml, robots.txt,
site.webmanifest, the fact sheets and press/files/rikogol-presskit.zip.
Images, fonts and the trailer come from tools/make_assets.py.
"""
import html
import importlib
import json
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

SITE = "https://rikogol.com"
STORE = "https://store.steampowered.com/app/4492690/Rikogol/"
DEV = "https://store.steampowered.com/developer/denizdurusoy"
ANN = "https://steamcommunity.com/games/4492690/announcements/detail/"
WIDGET = "https://store.steampowered.com/widget/4492690/"
EMAIL = "steam@rikogol.com"
YOUTUBE = "https://www.youtube.com/@rikogolgame"
INSTAGRAM = "https://www.instagram.com/rikogolgame/"
HOME_LASTMOD = "2026-10-08"   # sitemap lastmod of the language pages
PRESS_LASTMOD = "2026-10-08"  # sitemap lastmod of the press pages
MP4 = "/assets/video/rikogol-trailer.mp4"
POSTER = "/assets/video/rikogol-trailer-poster.webp"
OG_IMAGE = "/press/files/rikogol-main-capsule.jpg"

HOME_ORDER = ["en", "tr", "de", "ru", "ptbr", "es", "fr"]
PRESS_ORDER = ["en", "tr", "ptbr", "es"]
GALLERY = [1, 2, 12, 7, 10, 6, 11, 9, 5, 4, 14, 15, 3, 13, 8, 16]
# the game's languages (Steam store, 8 since v1.5); the site itself has the 7 of HOME_ORDER
LANG_NAMES = [("en", "English"), ("tr", "Türkçe"), ("de", "Deutsch"), ("ru", "Русский"),
              ("pt-BR", "Português (Brasil)"), ("es-419", "Español (Latinoamérica)"), ("fr", "Français"),
              ("zh-CN", "简体中文")]

# Press-page news, newest first: key -> (ISO date, Steam announcement, id of the h3 that labels the article).
# Each content module's P["news"] holds the copy of every entry, under the same keys and in this order.
NEWS = {
    # go-live day: fill 08 / 8 here and in tools/content/*.py; the link can become the announcement
    "v170": ("2026-10-08", "https://store.steampowered.com/news/app/4492690", "release-v170-title"),
    "v161": ("2026-10-05", ANN + "687518426922485684", "release-v161-title"),
    "v160": ("2026-10-04", ANN + "687518426922485607", "release-v160-title"),
    "v150": ("2026-10-02", ANN + "687518426922484737", "release-v150-title"),
    "v14": ("2026-09-30", ANN + "687518426922483728", "release-title"),
}
LATEST = "v170"  # the update the home pages' "latest update" band names and links to

CSP = ("default-src 'self'; img-src 'self' data:; media-src 'self'; font-src 'self'; style-src 'self'; "
       "script-src 'self'; frame-src https://store.steampowered.com; connect-src 'self'; object-src 'none'; "
       "base-uri 'self'; form-action 'self'")

PARTIAL = "--partial" in sys.argv  # dev only: build with whichever content modules exist
MODS = {}
for _code in list(HOME_ORDER):
    try:
        MODS[_code] = importlib.import_module("content." + _code)
    except ModuleNotFoundError:
        if not PARTIAL:
            raise
        HOME_ORDER.remove(_code)
PRESS_ORDER = [k for k in PRESS_ORDER if k in MODS and hasattr(MODS[k], "P")]
for _code in PRESS_ORDER:
    _keys = [e["key"] for e in MODS[_code].P["news"]]
    if _keys != list(NEWS):
        sys.exit(f"tools/content/{_code}.py: news keys {_keys} differ from NEWS {list(NEWS)}")


def esc(s):
    return html.escape(s, quote=True)


def fill(text, **links):
    """Escape plain copy, then swap {placeholders} for trusted HTML snippets."""
    out = esc(text)
    for key, val in links.items():
        out = out.replace("{" + key + "}", val)
    return out


BRAND_WORDS = re.compile(r"\b(Rikogol|Windows|macOS|Steam)\b")


def brandify(escaped):
    """Mark product names as English so uppercase text keeps them intact (Turkish casing turns i into İ)."""
    return BRAND_WORDS.sub(r'<span lang="en">\1</span>', escaped)


def mailto(subject=None):
    href = "mailto:" + EMAIL + (("?subject=" + subject.replace(" ", "%20")) if subject else "")
    return f'<a href="{esc(href)}">{EMAIL}</a>'


def fmt_size(path):
    n = os.path.getsize(os.path.join(ROOT, path.lstrip("/")))
    return f"{n / 1000000:.1f} MB" if n >= 1000000 else f"{max(1, round(n / 1000))} KB"


def srcset(pattern, widths):
    return ", ".join(f"{pattern.format(w=w)} {w}w" for w in widths)


def shot(n, w):
    return f"/assets/img/screens/rikogol-screenshot-{n:02d}-{w}.webp"


def shot_full(n):
    return f"/press/files/rikogol-screenshot-{n:02d}.jpg"


ICONS = {
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "play": '<path d="M8 5.5v13l11-6.5z" fill="currentColor" stroke="none"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.8 3 2.8 15 0 18M12 3c-2.8 3-2.8 15 0 18"/>',
    "access": '<circle cx="12" cy="4.5" r="1.8"/><path d="M4.5 8.5 12 10l7.5-1.5M12 10v4.5M8.5 21l3.5-6.5 3.5 6.5"/>',
    "trophy": '<path d="M8 4h8v5a4 4 0 0 1-8 0zM8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8.5 20h7M10 17h4"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/>',
    "download": '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    "prev": '<path d="M15 5l-7 7 7 7"/>',
    "next": '<path d="M9 5l7 7-7 7"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "external": '<path d="M14 5h5v5M19 5l-8 8M18 14v5H5V6h5"/>',
    "chevron": '<path d="M7 10l5 5 5-5"/>',
}


def icon(name, cls="icon"):
    return (f'<svg class="{cls}" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" '
            f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'
            f'{ICONS[name]}</svg>')


# ---------------------------------------------------------------- head / chrome


def head(c, title, description, canonical, alternates, ld=None, noindex=False, preload_hero=True):
    lines = [
        "<!doctype html>",
        f'<html lang="{c["lang"]}" dir="ltr">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<meta http-equiv="Content-Security-Policy" content="{CSP}">',
        f"<title>{esc(title)}</title>",
        f'<meta name="description" content="{esc(description)}">',
    ]
    if noindex:
        lines.append('<meta name="robots" content="noindex">')
    if canonical:
        lines.append(f'<link rel="canonical" href="{SITE}{canonical}">')
    for hl, path in alternates:
        lines.append(f'<link rel="alternate" hreflang="{hl}" href="{SITE}{path}">')
    lines += [
        '<meta name="theme-color" content="#070a12">',
        '<meta name="color-scheme" content="dark">',
        '<link rel="preload" href="/assets/fonts/oswald-bold.woff2" as="font" type="font/woff2" crossorigin>',
        '<link rel="preload" href="/assets/fonts/manrope-regular.woff2" as="font" type="font/woff2" crossorigin>',
    ]
    if preload_hero:
        lines.append('<link rel="preload" as="image" href="/assets/img/hero/rikogol-hero-1920.webp" imagesrcset="'
                     + srcset("/assets/img/hero/rikogol-hero-{w}.webp", (960, 1440, 1920, 2560))
                     + '" imagesizes="100vw" fetchpriority="high">')
    lines += [
        '<link rel="stylesheet" href="/assets/css/site.min.css">',
        '<link rel="icon" href="/favicon.ico" sizes="16x16 32x32 48x48">',
        '<link rel="icon" href="/assets/img/icons/icon-192.png" type="image/png" sizes="192x192">',
        '<link rel="apple-touch-icon" href="/assets/img/icons/apple-touch-icon.png">',
        '<link rel="manifest" href="/site.webmanifest">',
    ]
    if canonical:
        lines += [
            '<meta property="og:type" content="website">',
            '<meta property="og:site_name" content="Rikogol">',
            f'<meta property="og:title" content="{esc(title)}">',
            f'<meta property="og:description" content="{esc(description)}">',
            f'<meta property="og:url" content="{SITE}{canonical}">',
            f'<meta property="og:locale" content="{c["og_locale"]}">',
        ]
        for code in HOME_ORDER:
            loc = MODS[code].C["og_locale"]
            if loc != c["og_locale"]:
                lines.append(f'<meta property="og:locale:alternate" content="{loc}">')
        lines += [
            f'<meta property="og:image" content="{SITE}{OG_IMAGE}">',
            '<meta property="og:image:type" content="image/jpeg">',
            '<meta property="og:image:width" content="1232">',
            '<meta property="og:image:height" content="706">',
            f'<meta property="og:image:alt" content="{esc(c["og_image_alt"])}">',
            '<meta name="twitter:card" content="summary_large_image">',
            f'<meta name="twitter:title" content="{esc(title)}">',
            f'<meta name="twitter:description" content="{esc(description)}">',
            f'<meta name="twitter:image" content="{SITE}{OG_IMAGE}">',
            f'<meta name="twitter:image:alt" content="{esc(c["og_image_alt"])}">',
        ]
    if ld:
        lines.append('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False, indent=1)
                     .replace("</", "<\\/") + "</script>")
    lines += ['<script src="/assets/js/site.js" defer></script>', "</head>"]
    return "\n".join(lines)


def lang_menu(c, items):
    """items: list of (content dict, href) for the switcher."""
    cur = c["native"]
    lis = []
    for other, href in items:
        current = ' aria-current="page"' if other["code"] == c["code"] else ""
        lis.append(f'<li><a href="{href}" hreflang="{other["hreflang"]}" lang="{other["hreflang"]}"{current}>'
                   f'<span>{esc(other["native"])}</span><span class="lang-code">{other["short"]}</span></a></li>')
    return (f'<details class="lang" data-lang-menu>\n<summary aria-label="{esc(c["ui"]["lang_label"])}: {esc(cur)}">'
            f'{icon("globe")}<span>{c["short"]}</span>{icon("chevron", "icon chev")}</summary>\n'
            f'<ul class="lang-list">\n' + "\n".join(lis) + "\n</ul>\n</details>")


def site_header(c, nav_items, lang_items, home_href):
    nav = "\n".join(f'<li><a href="{href}">{esc(label)}</a></li>' for label, href in nav_items)
    return f"""<a class="skip-link" href="#main">{esc(c["ui"]["skip"])}</a>
<header class="site-header">
<div class="wrap header-inner">
<a class="brand" href="{home_href}"><img src="/assets/img/icons/icon-64.png" width="32" height="32" alt=""><span lang="en">Rikogol</span></a>
<nav class="main-nav" aria-label="{esc(c["ui"]["nav_label"])}">
<ul>
{nav}
</ul>
</nav>
{lang_menu(c, lang_items)}
</div>
</header>"""


def site_footer(c, press_href, lang_items, affiliation_note=False):
    """affiliation_note: only pages whose body mentions the other game carry the disclaimer."""
    u = c["ui"]
    note = f'<p>{esc(u["not_affiliated"])}</p>\n' if affiliation_note else ""
    lis = []
    for o, href in lang_items:
        current = ' aria-current="page"' if o["code"] == c["code"] else ""
        lis.append(f'<li><a href="{href}" hreflang="{o["hreflang"]}" lang="{o["hreflang"]}"{current}>'
                   f'{esc(o["native"])}</a></li>')
    langs = "\n".join(lis)
    return f"""<footer class="site-footer">
<div class="wrap footer-grid">
<div class="footer-brand">
<img src="/assets/img/icons/icon-64.png" width="40" height="40" alt="" loading="lazy">
<p><span class="footer-name" lang="en">Rikogol</span><br>{esc(u["made_by"])}</p>
</div>
<nav class="footer-links" aria-label="{esc(u["footer_nav"])}">
<ul>
<li><span class="footer-label">{esc(u["contact"])}</span> <a href="mailto:{EMAIL}">{EMAIL}</a></li>
<li><a href="{press_href}">{esc(u["press"])}</a></li>
<li><a href="{STORE}">{esc(u["store_link"])}</a></li>
<li><a href="{DEV}">{esc(u["dev_link"])}</a></li>
<li><a href="{YOUTUBE}" rel="me" lang="en">YouTube</a></li>
<li><a href="{INSTAGRAM}" rel="me" lang="en">Instagram</a></li>
</ul>
</nav>
<nav class="footer-langs" aria-label="{esc(u["lang_label"])}">
<ul>
{langs}
</ul>
</nav>
</div>
<div class="wrap footer-legal">
{note}<p>© 2026 Deniz Durusoy</p>
</div>
</footer>"""


def lightbox(c):
    u = c["ui"]
    return f"""<dialog class="lightbox" data-lightbox aria-label="{esc(u["viewer"])}">
<button type="button" class="lb-btn lb-close" data-lb="close" aria-label="{esc(u["close"])}">{icon("close")}</button>
<div class="lb-stage"></div>
<div class="lb-bar">
<p class="lb-caption" aria-live="polite"></p>
<div class="lb-controls">
<button type="button" class="lb-btn" data-lb="prev" aria-label="{esc(u["prev"])}">{icon("prev")}</button>
<span class="lb-count"></span>
<button type="button" class="lb-btn" data-lb="next" aria-label="{esc(u["next"])}">{icon("next")}</button>
<a class="lb-full" href="#" target="_blank" rel="noopener">{esc(u["full"])}</a>
</div>
</div>
</dialog>"""


# ---------------------------------------------------------------- home page


def home_alternates():
    alts = [(MODS[k].C["hreflang"], MODS[k].C["path"]) for k in HOME_ORDER]
    return alts + [("x-default", "/")]


def press_alternates():
    alts = [(MODS[k].C["hreflang"], MODS[k].P["path"]) for k in PRESS_ORDER]
    return alts + [("x-default", "/press/")]


def press_href(c):
    mod = MODS[c["code"]]
    return mod.P["path"] if hasattr(mod, "P") else "/press/"


def ld_game(c):
    dev = {"@type": "Person", "name": "Deniz Durusoy", "url": DEV}
    return {
        "@context": "https://schema.org",
        "@type": "VideoGame",
        "name": "Rikogol",
        "url": SITE + c["path"],
        "sameAs": [STORE, YOUTUBE, INSTAGRAM],
        "description": MODS[c["code"]].C["description"],
        "image": SITE + OG_IMAGE,
        "gamePlatform": ["PC", "Mac"],
        "operatingSystem": "Windows, macOS",
        "applicationCategory": "Game",
        "genre": ["Sports", "Arcade"],
        "playMode": ["SinglePlayer", "MultiPlayer"],
        "numberOfPlayers": {"@type": "QuantitativeValue", "minValue": 1, "maxValue": 24},
        "datePublished": "2026-09-14",
        "inLanguage": [hl for hl, _ in LANG_NAMES],
        "author": dev,
        "publisher": dev,
    }


def feature_block(c, f, i):
    body = "".join(f"<p>{fill(p)}</p>\n" for p in f.get("body", []))
    if f.get("list"):
        body += "<ul class=\"ticks\">\n" + "".join(f"<li>{fill(x)}</li>\n" for x in f["list"]) + "</ul>\n"
    if f.get("stat"):
        body += (f'<p class="stat"><span class="stat-num">{esc(f["stat"][0])}</span>'
                 f'<span class="stat-text">{esc(f["stat"][1])}</span></p>\n')
    n = f["img"]
    side = "feature-flip" if i % 2 else ""
    return f"""<section class="feature {side}" id="{f["id"]}" aria-labelledby="{f["id"]}-title">
<div class="feature-media">
<img src="{shot(n, 1280)}" srcset="{shot(n, 640)} 640w, {shot(n, 960)} 960w, {shot(n, 1280)} 1280w" sizes="(min-width: 960px) 620px, 92vw" width="1280" height="720" loading="lazy" decoding="async" alt="{esc(c["alts"][n])}">
</div>
<div class="feature-text">
<p class="kicker">{brandify(esc(f["kicker"]))}</p>
<h2 id="{f["id"]}-title">{brandify(esc(f["title"]))}</h2>
{body}</div>
</section>"""


def home_page(code):
    c = MODS[code].C
    u = c["ui"]
    lang_items = [(MODS[k].C, MODS[k].C["path"]) for k in HOME_ORDER]
    phref = press_href(c)
    nav = [(u["nav"][0], "#features"), (u["nav"][1], "#screenshots"), (u["nav"][2], "#community"),
           (u["nav"][3], phref)]
    ann = f"{NEWS[LATEST][1]}?l={c['steam_l']}"
    facts = "\n".join(f"<li>{brandify(esc(x))}</li>" for x in c["hero"]["facts"])
    features = "\n".join(feature_block(c, f, i) for i, f in enumerate(c["features"]))
    extras = []
    for x in c["extras"]:
        if x.get("langs"):
            text = ", ".join(f'<span lang="{hl}">{esc(name)}</span>' for hl, name in LANG_NAMES)
        else:
            text = fill(x["text"])
        extras.append(f'<li class="extra">{icon(x["icon"], "extra-icon")}<h3>{brandify(esc(x["title"]))}</h3><p>{text}</p></li>')
    tiles = []
    for n in GALLERY:
        tiles.append(
            f'<li><a class="shot" href="{shot_full(n)}" data-large="{shot(n, 1280)}">'
            f'<img src="{shot(n, 640)}" srcset="{shot(n, 640)} 640w, {shot(n, 1280)} 1280w" '
            f'sizes="(min-width: 1180px) 276px, (min-width: 720px) 23vw, 46vw" width="640" height="360" '
            f'loading="lazy" decoding="async" alt="{esc(c["alts"][n])}"></a></li>')
    com = c["community"]
    fin = c["finale"]
    widget = f"{WIDGET}?l={c['steam_l']}"
    dev_line = fill(fin["dev"], dev=f'<a href="{DEV}">Deniz Durusoy</a>')
    body = f"""<body>
{site_header(c, nav, lang_items, c["path"])}
<main id="main">
<section class="hero" aria-labelledby="hero-title">
<div class="hero-art">
<img class="hero-bg" src="/assets/img/hero/rikogol-hero-1920.webp" srcset="{srcset("/assets/img/hero/rikogol-hero-{w}.webp", (960, 1440, 1920, 2560))}" sizes="100vw" width="1920" height="620" alt="" fetchpriority="high">
<h1 class="hero-logo" id="hero-title"><img src="/assets/img/logo/rikogol-logo-1280.webp" srcset="{srcset("/assets/img/logo/rikogol-logo-{w}.webp", (480, 720, 960, 1280))}" sizes="(min-width: 720px) 600px, 84vw" width="1280" height="362" alt="Rikogol"></h1>
</div>
<div class="wrap hero-text">
<p class="tagline">{brandify(esc(c["hero"]["tagline"]))}</p>
<p class="lede">{esc(c["hero"]["sub"])}</p>
<div class="cta-row">
<a class="btn btn-primary" href="{STORE}"><span>{brandify(esc(u["cta"]))}</span>{icon("arrow")}</a>
<a class="btn btn-ghost" href="#trailer" data-play-trailer>{icon("play")}<span>{esc(u["watch"])}</span></a>
</div>
<ul class="facts">
{facts}
</ul>
</div>
<div class="wrap">
<figure class="trailer" id="trailer">
<div class="video-shell" data-video>
<video controls preload="none" playsinline poster="{POSTER}" width="1280" height="720" aria-label="{esc(u["trailer_title"])}">
<source src="{MP4}" type="video/mp4">
<p>{esc(u["video_fallback"])} <a href="{MP4}">{esc(u["download_mp4"])}</a></p>
</video>
<button type="button" class="video-play" hidden><span class="video-play-disc">{icon("play")}</span><span class="video-play-label">{esc(u["play"])}</span></button>
</div>
<figcaption>{esc(u["trailer_caption"])}</figcaption>
</figure>
</div>
</section>

<section class="band" aria-labelledby="band-title">
<div class="wrap band-inner">
<div class="band-text">
<p class="kicker">{brandify(esc(c["band"]["kicker"]))}</p>
<h2 id="band-title">{brandify(esc(c["band"]["title"]))}</h2>
<p>{esc(c["band"]["text"])}</p>
<p><a class="text-link" href="{esc(ann)}">{esc(c["band"]["link"])}{icon("external", "icon icon-sm")}</a></p>
</div>
<div class="widget-shell" data-widget-src="{esc(widget)}" data-widget-title="{esc(u["widget_title"])}">
<noscript><iframe src="{esc(widget)}" title="{esc(u["widget_title"])}" width="646" height="190" loading="lazy"></iframe></noscript>
</div>
</div>
</section>

<section class="pitch" aria-labelledby="pitch-title">
<div class="wrap pitch-inner">
<p class="kicker">{esc(c["pitch"]["kicker"])}</p>
<h2 id="pitch-title" class="display">{esc(c["pitch"]["title"])}</h2>
{"".join(f"<p>{esc(p)}</p>" for p in c["pitch"]["paras"])}
<p class="fans">{esc(c["pitch"]["fans"])}</p>
</div>
</section>

<div class="features wrap" id="features">
{features}
</div>

<section class="extras-section" aria-labelledby="extras-title">
<div class="wrap">
<h2 id="extras-title" class="section-title">{esc(c["extras_title"])}</h2>
<ul class="extras">
{chr(10).join(extras)}
</ul>
</div>
</section>

<section class="gallery-section" id="screenshots" aria-labelledby="gallery-title">
<div class="wrap">
<div class="section-head">
<p class="kicker">{esc(c["gallery"]["kicker"])}</p>
<h2 id="gallery-title" class="section-title">{esc(c["gallery"]["title"])}</h2>
<p class="hint">{esc(c["gallery"]["hint"])}</p>
</div>
<ul class="gallery" data-gallery>
{chr(10).join(tiles)}
</ul>
</div>
</section>

<section class="community" id="community" aria-labelledby="community-title">
<div class="wrap">
<div class="community-card">
<p class="kicker">{esc(com["kicker"])}</p>
<h2 id="community-title" class="display">{brandify(esc(com["title"]))}</h2>
<p>{fill(com["text"], email=mailto(com["subject"]))}</p>
<a class="btn btn-primary" href="mailto:{EMAIL}?subject={com["subject"].replace(" ", "%20")}">{icon("mail")}<span>{esc(com["button"])}</span></a>
</div>
</div>
</section>

<section class="finale" aria-labelledby="finale-title">
<div class="wrap finale-inner">
<img class="finale-icon" src="/assets/img/icons/icon-192.png" width="96" height="96" alt="" loading="lazy">
<h2 id="finale-title" class="display">{esc(fin["title"])}</h2>
<p>{esc(fin["text"])}</p>
<a class="btn btn-primary btn-lg" href="{STORE}"><span>{brandify(esc(u["cta"]))}</span>{icon("arrow")}</a>
<p class="dev-line">{dev_line}</p>
</div>
</section>
</main>
{site_footer(c, phref, lang_items, affiliation_note=True)}
{lightbox(c)}
</body>
</html>
"""
    doc = head(c, c["title"], c["description"], c["path"], home_alternates(), ld=ld_game(c)) + "\n" + body
    write(c["path"] + "index.html", doc)


# ---------------------------------------------------------------- press page

PRESS_ASSETS = [
    # key, file, preview, width, height
    ("logo", "rikogol-logo.png", "/assets/img/press/rikogol-logo-480.webp", 1280, 362),
    ("icon", "rikogol-icon-1024.png", "/assets/img/press/rikogol-icon-256.webp", 1024, 1024),
    ("header", "rikogol-header-capsule.jpg", "/assets/img/press/rikogol-header-capsule-460.webp", 920, 430),
    ("main", "rikogol-main-capsule.jpg", "/assets/img/press/rikogol-main-capsule-616.webp", 1232, 706),
    ("vertical", "rikogol-vertical-capsule.jpg", "/assets/img/press/rikogol-vertical-capsule-374.webp", 748, 896),
    ("keyart", "rikogol-key-art.jpg", "/assets/img/press/rikogol-key-art-960.webp", 3840, 1240),
]
PREVIEW_DIMS = {"logo": (480, 136), "icon": (256, 256), "header": (460, 215), "main": (616, 353),
                "vertical": (374, 448), "keyart": (960, 310)}


def news_article(c, p, e):
    """One news entry; "dateline" (bold lead-in of the first paragraph) and "about" are optional."""
    date, url, anchor = NEWS[e["key"]]
    paras = [esc(x) for x in e["paras"]]
    if e.get("dateline"):
        paras[0] = f"<strong>{esc(e['dateline'])}</strong> — {paras[0]}"
    lines = [f'<article class="release" aria-labelledby="{anchor}">',
             f'<p class="release-date"><time datetime="{date}">{esc(e["date"])}</time></p>',
             f'<h3 id="{anchor}">{esc(e["headline"])}</h3>',
             f'<p class="standfirst">{esc(e["standfirst"])}</p>']
    lines += [f"<p>{x}</p>" for x in paras]
    if e.get("about"):
        lines += [f'<h4>{brandify(esc(e["about_title"]))}</h4>', f'<p>{esc(e["about"])}</p>']
    lines += [f'<p><a class="text-link" href="{esc(url + "?l=" + c["steam_l"])}">{esc(p["news_read"])}'
              f'{icon("external", "icon icon-sm")}</a></p>', "</article>"]
    return "\n".join(lines)


def press_page(code):
    c = MODS[code].C
    p = MODS[code].P
    u = c["ui"]
    lang_items = [(MODS[k].C, MODS[k].P["path"]) for k in PRESS_ORDER]
    nav = [(p["nav"][0], c["path"]), (p["nav"][1], "#facts"), (p["nav"][2], "#news"),
           (p["nav"][3], "#downloads"), (p["nav"][4], "#contact")]
    links = {"email": mailto(), "store": f'<a href="{STORE}">{STORE}</a>'}
    facts = []
    for k, v in p["facts"]:
        if v == "https://rikogol.com":
            val = '<a href="https://rikogol.com/">rikogol.com</a>'
        else:
            val = fill(v, **links)
        facts.append(f"<div><dt>{brandify(esc(k))}</dt><dd>{val}</dd></div>")
    news = "\n".join(news_article(c, p, e) for e in p["news"])
    cards = []
    for key, fname, prev, w, h in PRESS_ASSETS:
        pw, ph = PREVIEW_DIMS[key]
        href = f"/press/files/{fname}"
        kind = fname.rsplit(".", 1)[1].upper()
        cards.append(
            f'<li class="asset asset-{key}"><a href="{href}" download>'
            f'<span class="asset-thumb"><img src="{prev}" width="{pw}" height="{ph}" loading="lazy" decoding="async" alt=""></span>'
            f'<span class="asset-name">{brandify(esc(p["assets"][key]))}</span>'
            f'<span class="asset-meta">{kind} · {w}×{h} · {fmt_size(href)}</span></a></li>')
    shots = []
    for n in range(1, 17):
        shots.append(
            f'<li><a href="{shot_full(n)}" target="_blank" rel="noopener">'
            f'<img src="{shot(n, 640)}" width="640" height="360" loading="lazy" decoding="async" '
            f'alt="{esc(c["alts"][n])}"></a></li>')
    zip_href = "/press/files/rikogol-presskit.zip"
    body = f"""<body class="press">
{site_header(c, nav, lang_items, c["path"])}
<main id="main">
<section class="press-hero" aria-labelledby="press-title">
<div class="press-hero-art" aria-hidden="true"><img src="/assets/img/hero/rikogol-hero-1440.webp" srcset="{srcset("/assets/img/hero/rikogol-hero-{w}.webp", (960, 1440, 1920, 2560))}" sizes="100vw" width="1440" height="465" alt="" fetchpriority="high"></div>
<div class="wrap press-hero-text">
<img class="press-logo" src="/assets/img/logo/rikogol-logo-720.webp" srcset="{srcset("/assets/img/logo/rikogol-logo-{w}.webp", (480, 720, 960))}" sizes="360px" width="720" height="204" alt="Rikogol">
<h1 id="press-title" class="display">{esc(p["h1"])}</h1>
<p class="lede">{fill(p["intro"], email=mailto())}</p>
<div class="cta-row">
<a class="btn btn-primary" href="{zip_href}" download>{icon("download")}<span>{esc(p["zip"].format(size=fmt_size(zip_href)))}</span></a>
<a class="btn btn-ghost" href="{STORE}"><span>{brandify(esc(u["store_link"]))}</span>{icon("external")}</a>
</div>
</div>
</section>

<section class="press-section" id="facts" aria-labelledby="facts-title">
<div class="wrap narrow">
<h2 id="facts-title" class="section-title">{esc(p["facts_title"])}</h2>
<dl class="facts-table">
{chr(10).join(facts)}
</dl>
</div>
</section>

<section class="press-section" id="description" aria-labelledby="desc-title">
<div class="wrap narrow">
<h2 id="desc-title" class="section-title">{esc(p["desc_title"])}</h2>
<p class="lead">{esc(p["desc_short"])}</p>
{"".join(f"<p>{esc(x)}</p>" for x in p["desc_long"])}
<h3>{esc(p["features_title"])}</h3>
<ul class="ticks">
{"".join(f"<li>{esc(x)}</li>" for x in p["features"])}
</ul>
</div>
</section>

<section class="press-section" id="news" aria-labelledby="news-title">
<div class="wrap narrow">
<h2 id="news-title" class="section-title">{esc(p["news_title"])}</h2>
{news}
</div>
</section>

<section class="press-section" id="downloads" aria-labelledby="downloads-title">
<div class="wrap">
<h2 id="downloads-title" class="section-title">{esc(p["assets_title"])}</h2>
<p class="section-sub">{esc(p["assets_intro"])}</p>
<ul class="asset-grid">
{chr(10).join(cards)}
</ul>
<h3 class="sub-title">{esc(p["screens_title"])}</h3>
<p class="section-sub">{esc(p["screens_note"])}</p>
<ul class="press-shots">
{chr(10).join(shots)}
</ul>
<h3 class="sub-title">{esc(p["trailer_title"])}</h3>
<div class="press-trailer">
<a class="press-trailer-thumb" href="{MP4}"><img src="{POSTER}" width="1280" height="720" loading="lazy" decoding="async" alt="{esc(u["trailer_caption"])}"><span class="video-play-disc">{icon("play")}</span></a>
<div class="press-trailer-text">
<p>{esc(p["trailer_text"])}</p>
<p><a class="btn btn-ghost" href="{MP4}" download>{icon("download")}<span>{esc(p["trailer_mp4"].format(size=fmt_size(MP4)))}</span></a></p>
<p><a class="text-link" href="{STORE}">{esc(p["trailer_steam"])}{icon("external", "icon icon-sm")}</a></p>
</div>
</div>
</div>
</section>

<section class="press-section" id="developer" aria-labelledby="dev-title">
<div class="wrap narrow">
<h2 id="dev-title" class="section-title">{esc(p["dev_title"])}</h2>
{"".join(f"<p>{esc(x)}</p>" for x in p["dev_text"])}
<p><a class="text-link" href="{DEV}">{esc(p["dev_link"])}{icon("external", "icon icon-sm")}</a></p>
</div>
</section>

<section class="press-section" id="contact" aria-labelledby="contact-title">
<div class="wrap narrow">
<h2 id="contact-title" class="section-title">{esc(p["contact_title"])}</h2>
<p class="lead">{fill(p["contact_text"], email=mailto())}</p>
</div>
</section>
</main>
{site_footer(c, p["path"], lang_items)}
</body>
</html>
"""
    doc = head(c, p["title"], p["description"], p["path"], press_alternates(), preload_hero=False) + "\n" + body
    write(p["path"] + "index.html", doc)


# ---------------------------------------------------------------- 404 + files


def page_404():
    c = MODS["en"].C
    lang_items = [(MODS[k].C, MODS[k].C["path"]) for k in HOME_ORDER]
    links = "\n".join(f'<li><a href="{MODS[k].C["path"]}" hreflang="{MODS[k].C["hreflang"]}" '
                      f'lang="{MODS[k].C["hreflang"]}">{esc(MODS[k].C["native"])}</a></li>' for k in HOME_ORDER)
    body = f"""<body class="notfound">
<main id="main" class="nf-main">
<a class="nf-logo" href="/"><img src="/assets/img/logo/rikogol-logo-720.webp" width="720" height="204" alt="Rikogol"></a>
<h1 class="display">Offside!</h1>
<p class="lede">There is no offside in Rikogol, but there is no page here either.</p>
<div class="cta-row">
<a class="btn btn-primary" href="/"><span>Back to the home page</span>{icon("arrow")}</a>
<a class="btn btn-ghost" href="{STORE}"><span>Rikogol on Steam</span>{icon("external")}</a>
</div>
<ul class="nf-langs">
{links}
</ul>
</main>
</body>
</html>
"""
    doc = head(c, "Page not found — Rikogol", "This page does not exist on rikogol.com.", None, [],
               noindex=True, preload_hero=False) + "\n" + body
    write("/404.html", doc)


def sitemap():
    groups = [([(MODS[k].C["hreflang"], MODS[k].C["path"]) for k in HOME_ORDER], "/", HOME_LASTMOD),
              ([(MODS[k].C["hreflang"], MODS[k].P["path"]) for k in PRESS_ORDER], "/press/", PRESS_LASTMOD)]
    urls = []
    for alts, default, lastmod in groups:
        for _, path in alts:
            links = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{hl}" href="{SITE}{p}"/>' for hl, p in alts)
            links += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{SITE}{default}"/>'
            urls.append(f"  <url>\n    <loc>{SITE}{path}</loc>\n    <lastmod>{lastmod}</lastmod>{links}\n  </url>")
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
           + "\n".join(urls) + "\n</urlset>\n")
    write("/sitemap.xml", xml)


def minify_css():
    """Comments out, whitespace collapsed; the readable source stays in assets/css/site.css."""
    src = open(os.path.join(ROOT, "assets", "css", "site.css"), encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    css = re.sub(r"\s*([{};,>])\s*", r"\1", css)
    css = css.replace(";}", "}").strip() + "\n"
    write("/assets/css/site.min.css", css)
    print(f"  assets/css/site.min.css  {len(css.encode()) // 1024} KB (source {len(src.encode()) // 1024} KB)")


def small_files():
    write("/robots.txt", f"User-agent: *\nAllow: /\nDisallow: /tools/\n\nSitemap: {SITE}/sitemap.xml\n")
    write("/CNAME", "rikogol.com")
    write("/.nojekyll", "")
    manifest = {
        "name": "Rikogol",
        "short_name": "Rikogol",
        "start_url": "/",
        "display": "browser",
        "background_color": "#070a12",
        "theme_color": "#070a12",
        "icons": [
            {"src": "/assets/img/icons/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/img/icons/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    write("/site.webmanifest", json.dumps(manifest, indent=2) + "\n")


def upper(c, text):
    """str.upper() is not Turkish-aware (i must become İ); product names keep their Latin I."""
    if c["lang"] != "tr":
        return text.upper()
    parts = re.split(r"(Rikogol|Steam|Windows|macOS)", text)
    return "".join(x.upper() if BRAND_WORDS.fullmatch(x) else x.replace("i", "İ").replace("ı", "I").upper()
                   for x in parts)


def factsheet_text(code):
    c = MODS[code].C
    p = MODS[code].P
    rule = "=" * 60
    lines = [upper(c, p["factsheet_name"]), rule, ""]
    width = max(len(k) for k, _ in p["facts"]) + 2
    for k, v in p["facts"]:
        v = v.replace("{store}", STORE).replace("{email}", EMAIL)
        lines.append(f"{k + ':':<{width}}{v}")
    lines += ["", upper(c, p["desc_title"]), "-" * 60, p["desc_short"], ""]
    lines += [x for para in p["desc_long"] for x in (para, "")]
    lines += [upper(c, p["features_title"]), "-" * 60]
    lines += [f"- {x}" for x in p["features"]]
    lines += ["", upper(c, p["dev_title"]), "-" * 60]
    lines += [x for para in p["dev_text"] for x in (para, "")]
    lines += [f"{c['ui']['press']}: {SITE}{p['path']}", f"{c['ui']['dev_link']}: {DEV}", ""]
    return "\n".join(lines)


def presskit_zip():
    files = []
    for code in PRESS_ORDER:
        name = f"rikogol-factsheet-{MODS[code].C['hreflang'].lower().replace('-419', '')}.txt"
        write("/press/files/" + name, factsheet_text(code))
        files.append((name, "press/files/" + name))
    for _, fname, *_ in PRESS_ASSETS:
        folder = "logo" if fname in ("rikogol-logo.png", "rikogol-icon-1024.png") else "capsules"
        files.append((f"{folder}/{fname}", "press/files/" + fname))
    for n in range(1, 17):
        files.append((f"screenshots/rikogol-screenshot-{n:02d}.jpg", f"press/files/rikogol-screenshot-{n:02d}.jpg"))
    dst = os.path.join(ROOT, "press", "files", "rikogol-presskit.zip")
    with zipfile.ZipFile(dst, "w") as z:
        for arc, src in files:
            info = zipfile.ZipInfo("rikogol-presskit/" + arc, date_time=(2026, 9, 30, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED if arc.endswith(".txt") else zipfile.ZIP_STORED
            with open(os.path.join(ROOT, src), "rb") as fh:
                z.writestr(info, fh.read())
    print(f"  press/files/rikogol-presskit.zip  {fmt_size('/press/files/rikogol-presskit.zip')}")


def write(rel, text):
    path = os.path.join(ROOT, rel.lstrip("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def main():
    minify_css()
    presskit_zip()
    for code in HOME_ORDER:
        home_page(code)
    for code in PRESS_ORDER:
        press_page(code)
    page_404()
    sitemap()
    small_files()
    print("built", len(HOME_ORDER), "language pages,", len(PRESS_ORDER), "press pages, 404, sitemap")


if __name__ == "__main__":
    main()
