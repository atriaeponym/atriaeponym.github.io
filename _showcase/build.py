#!/usr/bin/env python3
"""Builds the site's home page (index.html): a showcase of every Atria.Eponym app.

The list lives in _showcase/apps.json (Jekyll does not publish folders starting with "_").
Each app has a name, an icon, a one-line description in French and English, its stores with a
real status (live / soon), and its privacy pages. When an app is published or changes status,
edit apps.json, run this script from the repository root, commit and push.

    python3 _showcase/build.py
"""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TEXT = {
    "fr": {
        "kicker": "Applications mobiles",
        "lead": "Des applications simples et soignées pour Android, iPhone et Mac. Sans publicité, avec le moins de données possible.",
        "more": "En savoir plus",
        "privacy": "Confidentialité",
        "publisher": "Atria.Eponym, développeur individuel établi en France",
        "play": "Google Play", "appstore": "App Store", "mac": "Mac",
        "soon_play": "Bientôt sur Google Play", "soon_appstore": "Bientôt sur iPhone", "soon_mac": "Bientôt sur Mac",
        "android": "Android", "iphone": "iPhone",
    },
    "en": {
        "kicker": "Mobile apps",
        "lead": "Simple, carefully made apps for Android, iPhone and Mac. No ads, as little data as possible.",
        "more": "Learn more",
        "privacy": "Privacy",
        "publisher": "Atria.Eponym, individual developer based in France",
        "play": "Google Play", "appstore": "App Store", "mac": "Mac",
        "soon_play": "Coming to Google Play", "soon_appstore": "Coming to iPhone", "soon_mac": "Coming to Mac",
        "android": "Android", "iphone": "iPhone",
    },
}

CHECK = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12l5 5L20 7"/></svg>'
CLOCK = '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></svg>'

CSS = """
:root{--bg:#F6F7FA;--card:#FFFFFF;--ink:#141A24;--dim:#5D6878;--line:#E2E6EE;--amber:#B87500;--ok:#1E7F47;--soon:#7A8496}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0B1119;--card:#141C28;--ink:#E9EDF5;--dim:#8E9BB0;--line:#26313F;--amber:#F5A623;--ok:#4CC38A;--soon:#7B879B}}
:root[data-theme="dark"]{--bg:#0B1119;--card:#141C28;--ink:#E9EDF5;--dim:#8E9BB0;--line:#26313F;--amber:#F5A623;--ok:#4CC38A;--soon:#7B879B}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:400 16px/1.55 -apple-system,"Segoe UI",Roboto,system-ui,sans-serif;-webkit-font-smoothing:antialiased}
.w{max-width:760px;margin:0 auto;padding:56px 16px 40px}
.top{display:flex;justify-content:flex-end;margin:-32px 0 24px}
.lang{display:flex;gap:4px}
.lang button{font:600 13px/1 inherit;color:var(--dim);background:none;border:1px solid var(--line);border-radius:999px;padding:6px 10px;cursor:pointer}
.lang button[aria-pressed="true"]{color:var(--ink);border-color:var(--ink)}
.kicker{color:var(--amber);font:600 12px/1 inherit;letter-spacing:.14em;text-transform:uppercase;margin:0 0 12px}
h1{font:650 34px/1.15 inherit;margin:0 0 10px;letter-spacing:-.015em}
.lead{color:var(--dim);margin:0 0 32px;max-width:560px}
.grid{display:grid;gap:16px}
.app{display:flex;gap:18px;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px}
.app img{width:72px;height:72px;border-radius:17px;flex:none;box-shadow:0 1px 3px rgba(0,0,0,.18)}
.tx{min-width:0}
.app h2{font:650 19px/1.2 inherit;margin:2px 0 6px}
.app p{color:var(--dim);margin:0 0 12px;font-size:15px}
.stores{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:10px}
.st{display:inline-flex;align-items:center;gap:6px;font:600 13px/1 inherit;padding:8px 11px;border-radius:999px;border:1px solid var(--line);text-decoration:none}
.st svg{width:15px;height:15px;fill:none;stroke:currentColor;stroke-width:2.2;stroke-linecap:round;stroke-linejoin:round}
.st.live{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 45%,transparent)}
.st.soon{color:var(--soon)}
.links{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:14px}
.links a{color:var(--amber);font-weight:600;text-decoration:none}
footer{border-top:1px solid var(--line);margin-top:36px;padding-top:18px;color:var(--dim);font-size:14px}
footer a{color:var(--amber)}
[data-l]{display:none}
html[lang="fr"] [data-l="fr"],html[lang="en"] [data-l="en"]{display:revert}
@media (max-width:480px){.app{flex-direction:column;gap:12px}h1{font-size:28px}}
"""

SCRIPT = """<script>
(function(){
  function pick(l){
    document.documentElement.lang = l;
    document.querySelectorAll('.lang button').forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.set === l); });
  }
  var q = new URLSearchParams(location.search).get('lang');
  var nav = (navigator.language || 'en').toLowerCase();
  pick(q === 'fr' || q === 'en' ? q : (nav.indexOf('fr') === 0 ? 'fr' : 'en'));
  document.querySelectorAll('.lang button').forEach(function(b){ b.onclick = function(){ pick(b.dataset.set); }; });
})();
</script>"""


def both(fn) -> str:
    """The same piece of markup in both languages, shown according to <html lang>."""
    return "".join(f'<span data-l="{l}">{fn(l)}</span>' for l in TEXT)


def store(s: dict) -> str:
    kind, status = s["kind"], s["status"]
    if status == "live":
        label = both(lambda l: html.escape(TEXT[l][kind]))
        return f'<a class="st live" href="{html.escape(s["url"])}">{CHECK}{label}</a>'
    label = both(lambda l: html.escape(TEXT[l]["soon_" + kind]))
    return f'<span class="st soon">{CLOCK}{label}</span>'


def privacy(p: dict) -> str:
    def label(l):
        t = TEXT[l]["privacy"]
        return html.escape(t + (f" ({TEXT[l][p['platform']]})" if p.get("platform") else ""))
    return f'<a href="{html.escape(p["url"])}">{both(label)}</a>'


def card(a: dict) -> str:
    links = []
    if a.get("more"):
        links.append(f'<a href="{html.escape(a["more"])}">{both(lambda l: html.escape(TEXT[l]["more"]))}</a>')
    links += [privacy(p) for p in a.get("privacy", [])]
    desc = both(lambda l: html.escape(a["description"][l]))
    return (f'<article class="app"><img src="{html.escape(a["icon"])}" alt="" width="72" height="72">'
            f'<div class="tx"><h2>{html.escape(a["name"])}</h2><p>{desc}</p>'
            f'<div class="stores">{"".join(store(s) for s in a["stores"])}</div>'
            f'<div class="links">{"".join(links)}</div></div></article>')


def main() -> None:
    apps = json.loads((ROOT / "_showcase" / "apps.json").read_text(encoding="utf-8"))["apps"]
    for a in apps:
        assert (ROOT / a["icon"]).is_file(), a["icon"]
        for s in a["stores"]:
            assert s["status"] in ("live", "soon") and (s["status"] == "soon" or s.get("url")), (a["id"], s)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Atria Eponym</title>
<meta name="description" content="Family Pocket, Speed GPS, Mac Live: apps by Atria.Eponym.">
<link rel="icon" href="icons/familypocket.png">
<style>{CSS}</style>
</head>
<body>
<div class="w">
<div class="top"><div class="lang"><button data-set="fr">FR</button><button data-set="en">EN</button></div></div>
<p class="kicker">{both(lambda l: html.escape(TEXT[l]["kicker"]))}</p>
<h1>Atria Eponym</h1>
<p class="lead">{both(lambda l: html.escape(TEXT[l]["lead"]))}</p>
<div class="grid">
{chr(10).join(card(a) for a in apps)}
</div>
<footer>{both(lambda l: html.escape(TEXT[l]["publisher"]))} · <a href="mailto:atria.eponym@gmail.com">atria.eponym@gmail.com</a><br>© 2026 Atria.Eponym</footer>
</div>
{SCRIPT}
</body>
</html>
"""
    (ROOT / "index.html").write_text(page, encoding="utf-8")
    print(f"index.html: {len(apps)} apps")


if __name__ == "__main__":
    main()
