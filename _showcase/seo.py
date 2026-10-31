"""Search-engine pass over the app pages, run by build.py after the home pages.

App pages (/<app>/ and /<app>/<lang>/) are written by hand or by their own scripts (diapo_page.py,
parfumpocket_page.py, an app's repository). This pass adds only what a page lacks, so it is safe to run
again: the canonical address on atriaeponym.com (github.io serves the same files), a meta description,
and schema.org data for an app of the showcase. It never touches legal pages (privacy, terms, delete),
invitation pages (join) or a page marked noindex. It also lists every indexable app page for the
sitemap and writes llms.txt, a plain-text summary of the publisher and its apps for AI assistants.
"""
import html
import json
import re

LEGAL = {"privacy", "terms", "delete", "join"}
# Listed in the sitemap but never edited here (Romain, 31/10/2026: Diapo is left untouched for now)
FROZEN = {"diapo"}


def app_pages(root, langs):
    """(path relative to root, app folder, language folder or None) of every indexable app landing page."""
    out = []
    for f in sorted(root.glob("*/index.html")) + sorted(root.glob("*/*/index.html")):
        parts = f.relative_to(root).parts[:-1]
        if parts[0] in langs or parts[0] in LEGAL or parts[0].startswith((".", "_")):
            continue
        if len(parts) == 2 and parts[1] not in langs:
            continue
        head = f.read_text(encoding="utf-8").split("</head>", 1)[0]
        if "noindex" in head or 'http-equiv="refresh"' in head.lower():
            continue
        out.append((f, parts[0], parts[1] if len(parts) == 2 else None))
    return out


def description(page):
    """The page's own words: Open Graph description, else its first paragraph, cut near 160 signs."""
    m = re.search(r'<meta property="og:description" content="([^"]*)"', page)
    text = html.unescape(m.group(1)) if m else ""
    if not text:
        body = page.split("</head>", 1)[-1]
        for p in re.findall(r"<p[^>]*>(.*?)</p>", body, re.S):
            text = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", p))).strip()
            if len(text) > 40:
                break
    if len(text) > 160:
        text = text[:157].rsplit(" ", 1)[0] + "…"
    return text


def app_data(a, lang, texts, site, category, name):
    """schema.org SoftwareApplication of one app, in the page's language, from the showcase data."""
    systems = {"android": "Android", "iphone": "iOS", "mac": "macOS, Windows"}
    live = [p for p in a["platforms"] if p["status"] == "live"]
    T = texts.get(lang) or texts["en"]
    app = {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": name(a, lang),
           "description": T["_apps"][a["id"]]["tagline"], "applicationCategory": category[a["id"]],
           "image": f"{site}/{a['icon']}",
           "operatingSystem": ", ".join(dict.fromkeys(systems[p["platform"]] for p in live)) or None,
           "offers": None if a.get("paid") else {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
           "author": {"@type": "Organization", "@id": f"{site}/#publisher", "name": "Atria.Eponym", "url": f"{site}/"},
           "sameAs": [p["url"] for p in live if p["url"].startswith("http")] or None}
    data = {k: v for k, v in app.items() if v}
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def run(root, site, langs, apps, texts, category, name):
    """Completes the app pages in place; returns their public URLs for the sitemap."""
    by_id = {a["id"]: a for a in apps}
    urls, changed = [], 0
    for f, folder, lang in app_pages(root, langs):
        urls.append(site + f"/{folder}/" + (f"{lang}/" if lang else ""))
        if folder in FROZEN:
            continue
        page = f.read_text(encoding="utf-8")
        head, rest = page.split("</head>", 1)
        path = f"/{folder}/" + (f"{lang}/" if lang else "")
        add = []
        if 'rel="canonical"' not in head:
            add.append(f'<link rel="canonical" href="{site}{path}">')
        if 'name="description"' not in head:
            d = description(page)
            if d:
                add.append(f'<meta name="description" content="{html.escape(d)}">')
        if "application/ld+json" not in head and folder in by_id:
            m = re.search(r'<html[^>]*\blang="([^"]+)"', page)
            page_lang = lang or (m.group(1).lower() if m else "fr")
            page_lang = {"pt-pt": "pt", "zh-hans": "zh"}.get(page_lang, page_lang)
            add.append('<script type="application/ld+json">'
                       + app_data(by_id[folder], page_lang, texts, site, category, name) + "</script>")
        if add:
            f.write_text(head + "\n".join(add) + "\n</head>" + rest, encoding="utf-8")
            changed += 1
    return urls, changed


def llms_txt(site, apps, texts, name, urls):
    """llms.txt (llmstxt.org): who publishes, each app with its store links and page, in English and French."""
    lines = ["# Atria.Eponym", "",
             "> Atria.Eponym is an independent developer based in France. Simple, polished apps for Android, "
             "iPhone, Mac and PC: no ads, no mandatory account, as little data as possible. "
             "Apps are translated into 28 languages.", "",
             "Contact: atria.eponym@gmail.com. Showcase in 28 languages: " + f"{site}/ (English), {site}/fr/ (French).", "",
             "## Apps", ""]
    for a in apps:
        live = [p for p in a["platforms"] if p["status"] == "live" and p["url"].startswith("http")]
        lines.append(f"### {name(a, 'en')}" + (f" (French: {name(a, 'fr')})" if name(a, "fr") != name(a, "en") else ""))
        lines.append(f"- {texts['en']['_apps'][a['id']]['tagline']}")
        lines.append(f"- FR : {texts['fr']['_apps'][a['id']]['tagline']}")
        for p in live:
            store = {"play": "Google Play", "appstore": "App Store", "msstore": "Microsoft Store"}.get(p["channel"], p["channel"])
            device = "Windows" if p["channel"] == "msstore" else {"android": "Android", "iphone": "iPhone", "mac": "Mac"}[p["platform"]]
            lines.append(f"- {store} ({device}): {p['url']}")
        if f"{site}/{a['id']}/" in urls:
            lines.append(f"- Page: {site}/{a['id']}/")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
