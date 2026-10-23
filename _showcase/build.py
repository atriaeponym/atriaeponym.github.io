#!/usr/bin/env python3
"""Builds the site's home page (index.html): a showcase of every Atria.Eponym app.

The list lives in _showcase/apps.json (Jekyll does not publish folders starting with "_").
Each app has a name, an icon, a tagline and feature chips in French and English, and one row per
platform (Android, iPhone, Mac/PC) with its channel (Google Play, App Store, direct download, Microsoft Store) and a
real status (live / soon). When an app is published or changes status, edit apps.json, run this
script from the repository root, commit and push.

    python3 _showcase/build.py              # writes index.html
    python3 _showcase/build.py --standalone out.html   # same page with icons inlined (mockups)
"""
import base64
import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLATFORMS = ("android", "iphone", "mac")

TEXT = {
    "fr": {
        "kicker": "Éditeur d'applications",
        "lead": "Des applications simples et soignées pour Android, iPhone, Mac et PC. Sans publicité, sans compte obligatoire, avec le moins de données possible.",
        "apps": "applications", "platforms_n": "plateformes", "languages": "langues", "upto": "jusqu’à ", "ads": "publicité",
        "all": "Toutes",
        "android": "Android", "iphone": "iPhone", "mac": "Mac/PC",
        "play": "Google Play", "appstore": "App Store", "direct": "Téléchargement direct", "msstore": "Microsoft Store (Windows)",
        "live": "Disponible", "soon": "Bientôt",
        "more_features": "et plus…",
        "more": "En savoir plus", "privacy": "Confidentialité",
        "example": "Vidéo avec des données d'exemple",
        "publisher": "Atria.Eponym, développeur individuel établi en France",
    },
    "en": {
        "kicker": "App publisher",
        "lead": "Simple, carefully made apps for Android, iPhone, Mac and PC. No ads, no mandatory account, as little data as possible.",
        "apps": "apps", "platforms_n": "platforms", "languages": "languages", "upto": "up to ", "ads": "ads",
        "all": "All",
        "android": "Android", "iphone": "iPhone", "mac": "Mac/PC",
        "play": "Google Play", "appstore": "App Store", "direct": "Direct download", "msstore": "Microsoft Store (Windows)",
        "live": "Available", "soon": "Coming soon",
        "more_features": "and more…",
        "more": "Learn more", "privacy": "Privacy",
        "example": "Video with example data",
        "publisher": "Atria.Eponym, individual developer based in France",
    },
}

# Generic line icons (no brand logos).
ICON = {
    "android": '<svg viewBox="0 0 24 24"><rect x="6" y="2.5" width="12" height="19" rx="2.5"/><path d="M10.5 18.5h3"/></svg>',
    "iphone": '<svg viewBox="0 0 24 24"><rect x="6.5" y="2.5" width="11" height="19" rx="3"/><path d="M10.5 4.8h3"/></svg>',
    "mac": '<svg viewBox="0 0 24 24"><rect x="4" y="4.5" width="16" height="11" rx="1.6"/><path d="M2 19.5h20"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg>',
    "check": '<svg viewBox="0 0 24 24"><path d="M5 12l5 5L20 7"/></svg>',
    "clock": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/></svg>',
}

CSS = """
:root{--bg:#F4F6FA;--card:#FFFFFF;--soft:#F1F3F8;--ink:#121822;--dim:#5B6577;--line:#E1E5EE;--tile:rgba(184,117,0,.38);--accent:#B87500;--ok:#1E7F47;--okbg:#E5F4EC;--soon:#6E788A;--soonbg:#EEF0F4;--glow:rgba(245,166,35,.16)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#090E15;--card:#111823;--soft:#18212E;--ink:#E9EDF5;--dim:#8E9BB0;--line:#243041;--tile:rgba(245,166,35,.42);--accent:#F5A623;--ok:#4CC38A;--okbg:rgba(76,195,138,.12);--soon:#8D98AB;--soonbg:rgba(141,152,171,.12);--glow:rgba(245,166,35,.10)}}
:root[data-theme="dark"]{--bg:#090E15;--card:#111823;--soft:#18212E;--ink:#E9EDF5;--dim:#8E9BB0;--line:#243041;--tile:rgba(245,166,35,.42);--accent:#F5A623;--ok:#4CC38A;--okbg:rgba(76,195,138,.12);--soon:#8D98AB;--soonbg:rgba(141,152,171,.12);--glow:rgba(245,166,35,.10)}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:radial-gradient(1200px 500px at 85% -10%,var(--glow),transparent 60%),var(--bg);color:var(--ink);font:400 16px/1.55 -apple-system,"Segoe UI",Roboto,system-ui,sans-serif;-webkit-font-smoothing:antialiased;min-height:100vh}
svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round;flex:none}
.w{max-width:1080px;margin:0 auto;padding:28px 16px 40px}
.bar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:44px}
.brand{font-weight:700;font-size:15px;line-height:1;letter-spacing:.02em}
.brand span{color:var(--accent)}
.lang{display:flex;gap:4px}
.lang button{font-weight:600;font-size:12px;line-height:1;color:var(--dim);background:var(--card);border:1px solid var(--line);border-radius:999px;padding:7px 11px;cursor:pointer}
.lang button[aria-pressed="true"]{color:var(--ink);border-color:var(--ink)}
.kicker{color:var(--accent);font-weight:650;font-size:12px;line-height:1;letter-spacing:.16em;text-transform:uppercase;margin:0 0 12px}
h1{font-weight:700;font-size:clamp(30px,5vw,44px);line-height:1.08;margin:0 0 12px;letter-spacing:-.02em}
.lead{color:var(--dim);margin:0 0 28px;max-width:620px;font-size:17px}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:0 0 30px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.stat b{display:block;font-weight:700;font-size:24px;line-height:1.1;letter-spacing:-.01em}
.stat span{color:var(--dim);font-size:13px}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}
.filters button{display:inline-flex;align-items:center;gap:7px;font-weight:600;font-size:14px;line-height:1;color:var(--dim);background:var(--card);border:1px solid var(--line);border-radius:999px;padding:9px 14px;cursor:pointer;transition:all .15s}
.filters button:hover{color:var(--ink)}
.filters button[aria-pressed="true"]{color:var(--bg);background:var(--ink);border-color:var(--ink)}
.filters em{font-style:normal;opacity:.65;font-size:12px}
.grid{display:grid;gap:18px}
.app.has-media{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:28px;align-items:center}
.body{display:flex;flex-direction:column;min-width:0}
.media{justify-self:center;width:230px}
.phone{position:relative;border-radius:34px;padding:7px;background:linear-gradient(160deg,#2a3242,#0d1118);box-shadow:0 18px 40px rgba(0,0,0,.28),inset 0 0 0 1px rgba(255,255,255,.08)}
.phone video{display:block;width:100%;aspect-ratio:540/1174;border-radius:28px;background:var(--soft);object-fit:cover}
.example{display:block;text-align:center;color:var(--dim);font-size:12px;margin-top:8px}
.app{display:flex;flex-direction:column;background:var(--card);border:1px solid var(--tile);border-radius:18px;padding:20px;transition:transform .18s,box-shadow .18s,border-color .18s}
.app:hover{transform:translateY(-2px);box-shadow:0 10px 30px rgba(0,0,0,.10);border-color:var(--accent)}
.app[hidden]{display:none}
.head{display:flex;gap:14px;align-items:center;margin-bottom:12px}
.head img{width:60px;height:60px;border-radius:14px;flex:none;box-shadow:0 1px 3px rgba(0,0,0,.2)}
.head h2{font-weight:700;font-size:20px;line-height:1.2;margin:0}
.tag{color:var(--dim);margin:0 0 14px;font-size:15px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 16px}
.chips span{font-weight:500;font-size:12.5px;line-height:1;padding:7px 10px;border-radius:8px;background:var(--soft);color:var(--ink)}
.chips .more{background:none;color:var(--accent);font-weight:650;padding-left:2px}
.rows{display:grid;gap:8px;margin-top:auto}
.row{display:flex;align-items:center;gap:12px;padding:11px 12px;border:1px solid var(--line);border-radius:12px;text-decoration:none;color:inherit;transition:background .15s,border-color .15s}
a.row:hover{background:var(--soft);border-color:color-mix(in srgb,var(--ok) 40%,var(--line))}
.row .pf{display:flex;align-items:center;gap:8px;min-width:0;flex:1}
.row .pf b{font-weight:650;font-size:14.5px;line-height:1.2;display:block}
.row .pf small{color:var(--dim);font-size:12.5px;display:block}
.badge{display:inline-flex;align-items:center;gap:5px;font-weight:650;font-size:12px;line-height:1;padding:6px 9px;border-radius:999px;white-space:nowrap}
.badge svg{width:13px;height:13px;stroke-width:2.4}
.live .badge{color:var(--ok);background:var(--okbg)}
.soon .badge{color:var(--soon);background:var(--soonbg)}
.row .go{color:var(--dim)}
.links{display:flex;flex-wrap:wrap;gap:4px 16px;font-size:14px;margin-top:14px}
.links a{color:var(--accent);font-weight:600;text-decoration:none}
.links a:hover{text-decoration:underline}
footer{border-top:1px solid var(--line);margin-top:40px;padding-top:18px;color:var(--dim);font-size:14px;display:flex;flex-wrap:wrap;justify-content:space-between;gap:8px}
footer a{color:var(--accent)}
[data-l]{display:none}
html[lang="fr"] [data-l="fr"],html[lang="en"] [data-l="en"]{display:revert}
html[lang="fr"] .chips>[data-l="fr"],html[lang="en"] .chips>[data-l="en"]{display:contents}
@media (max-width:760px){.app.has-media{grid-template-columns:1fr;gap:20px}.media{width:min(230px,70vw);order:-1}}
@media (max-width:640px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.bar{margin-bottom:32px}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""

SCRIPT = """<script>
(function(){
  var still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var vids = document.querySelectorAll('video[data-fr]');
  function source(v){
    var l = document.documentElement.lang, src = v.dataset[l];
    v.poster = v.dataset[l + 'Poster'];
    if (v.dataset.live && v.getAttribute('src') !== src) { v.src = src; if (!still) v.play().catch(function(){}); }
  }
  function pick(l){
    document.documentElement.lang = l;
    document.querySelectorAll('.lang button').forEach(function(b){ b.setAttribute('aria-pressed', b.dataset.set === l); });
    vids.forEach(source);
  }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function(es){ es.forEach(function(e){
      var v = e.target;
      if (e.isIntersecting) { v.dataset.live = '1'; source(v); if (!still) v.play().catch(function(){}); }
      else v.pause();
    }); }, {rootMargin: '200px'});
    vids.forEach(function(v){ io.observe(v); });
  } else vids.forEach(function(v){ v.dataset.live = '1'; });
  var q = new URLSearchParams(location.search).get('lang');
  var nav = (navigator.language || 'en').toLowerCase();
  pick(q === 'fr' || q === 'en' ? q : (nav.indexOf('fr') === 0 ? 'fr' : 'en'));
  document.querySelectorAll('.lang button').forEach(function(b){ b.onclick = function(){ pick(b.dataset.set); }; });
  var fs = document.querySelectorAll('.filters button');
  fs.forEach(function(b){ b.onclick = function(){
    fs.forEach(function(x){ x.setAttribute('aria-pressed', x === b); });
    document.querySelectorAll('.app').forEach(function(a){
      a.hidden = b.dataset.f !== 'all' && a.dataset.p.split(' ').indexOf(b.dataset.f) < 0;
    });
  }; });
})();
</script>"""


def both(fn) -> str:
    """The same piece of markup in both languages, shown according to <html lang>."""
    return "".join(f'<span data-l="{l}">{fn(l)}</span>' for l in TEXT)


def t(key: str) -> str:
    return both(lambda l: html.escape(TEXT[l][key]))


def icon_src(path: str, standalone: bool) -> str:
    data = (ROOT / path).read_bytes()
    if standalone:
        return "data:image/png;base64," + base64.b64encode(data).decode()
    # A content hash in the URL, so a changed icon is never served from a browser's cache.
    return f"{path}?v={hashlib.sha256(data).hexdigest()[:10]}"


def row(p: dict) -> str:
    status = p["status"]
    badge = f'<span class="badge">{ICON["check"] if status == "live" else ICON["clock"]}{t(status)}</span>'
    inner = (f'<span class="pf">{ICON[p["platform"]]}<span><b>{t(p["platform"])}</b>'
             f'<small>{t(p["channel"])}{" · " + html.escape(p["name"]) if p.get("name") else ""}</small></span></span>{badge}')
    if status == "live":
        return f'<a class="row live" href="{html.escape(p["url"])}">{inner}<span class="go">{ICON["arrow"]}</span></a>'
    return f'<div class="row soon">{inner}</div>'


def privacy(p: dict) -> str:
    def label(l):
        s = TEXT[l]["privacy"]
        return html.escape(s + (f" {TEXT[l][p['platform']]}" if p.get("platform") else ""))
    return f'<a href="{html.escape(p["url"])}">{both(label)}</a>'


def name(a: dict, l: str = "en") -> str:
    """The app's name: one string, or {"fr": ..., "en": ...} when it differs by language."""
    return a["name"][l] if isinstance(a["name"], dict) else a["name"]


def media(a: dict, standalone: bool) -> str:
    """Looping teaser in a phone frame: muted, loaded only when visible, poster only under reduced motion."""
    tz = a.get("teaser")
    if not tz:
        return ""
    def src(path):
        if standalone:
            kind = "video/mp4" if path.endswith(".mp4") else "image/jpeg"
            return f"data:{kind};base64," + base64.b64encode((ROOT / path).read_bytes()).decode()
        return f"{path}?v={hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:10]}"
    attrs = " ".join(f'data-{l}="{src(tz[l]["video"])}" data-{l}-poster="{src(tz[l]["poster"])}"' for l in TEXT)
    return (f'<div class="media"><div class="phone"><video {attrs} muted loop playsinline preload="none" '
            f'aria-label="{html.escape(name(a))}"></video></div>'
            f'<span class="example">{both(lambda l: html.escape(TEXT[l]["example"]))}</span></div>')


def card(a: dict, standalone: bool) -> str:
    chips = both(lambda l: "".join(f"<span>{html.escape(f)}</span>" for f in a["features"][l])
                 + (f'<span class="more">{html.escape(TEXT[l]["more_features"])}</span>' if a.get("more_features") else ""))
    links = []
    if a.get("more"):
        links.append(f'<a href="{html.escape(a["more"])}">{t("more")}</a>')
    links += [privacy(p) for p in a.get("privacy", [])]
    platforms = " ".join(p["platform"] for p in a["platforms"])
    m = media(a, standalone)
    return (f'<article class="app{" has-media" if m else ""}" data-p="{platforms}"><div class="body">'
            f'<div class="head"><img src="{html.escape(icon_src(a["icon"], standalone))}" alt="" width="60" height="60">'
            f'<h2>{both(lambda l: html.escape(name(a, l)))}</h2></div>'
            f'<p class="tag">{both(lambda l: html.escape(a["tagline"][l]))}</p>'
            f'<div class="chips">{chips}</div>'
            f'<div class="rows">{"".join(row(p) for p in sorted(a["platforms"], key=lambda p: PLATFORMS.index(p["platform"])))}</div>'
            f'<div class="links">{"".join(links)}</div></div>{m}</article>')


def check(apps: list) -> None:
    for a in apps:
        assert (ROOT / a["icon"]).is_file(), a["icon"]
        for l, tz in a.get("teaser", {}).items():
            assert l in TEXT and (ROOT / tz["video"]).is_file() and (ROOT / tz["poster"]).is_file(), (a["id"], l)
        for p in a["platforms"]:
            assert p["platform"] in PLATFORMS and p["channel"] in ("play", "appstore", "direct", "msstore"), (a["id"], p)
            assert p["status"] in ("live", "soon") and (p["status"] == "soon" or p.get("url")), (a["id"], p)


def page(apps: list, standalone: bool) -> str:
    used = [pf for pf in PLATFORMS if any(p["platform"] == pf for a in apps for p in a["platforms"])]
    filters = [f'<button data-f="all" aria-pressed="true">{t("all")} <em>{len(apps)}</em></button>']
    for pf in used:
        n = sum(any(p["platform"] == pf for p in a["platforms"]) for a in apps)
        filters.append(f'<button data-f="{pf}" aria-pressed="false">{ICON[pf]}{t(pf)} <em>{n}</em></button>')
    # Most apps ship in 28 languages, some in fewer (SoundCatch: French only); none shows ads.
    stats = [(str(len(apps)), "apps"), (str(len(used)), "platforms_n"), (t("upto") + "28", "languages"), ("0", "ads")]
    stats_html = "".join(f'<div class="stat"><b>{v}</b><span>{t(k)}</span></div>' for v, k in stats)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Atria Eponym</title>
<meta name="description" content="MyLilBudget, Speed GPS, Mac Live: apps by Atria.Eponym for Android, iPhone, Mac and PC.">
<style>{CSS}</style>
</head>
<body>
<div class="w">
<div class="bar"><div class="brand">Atria<span>.</span>Eponym</div><div class="lang"><button data-set="fr">FR</button><button data-set="en">EN</button></div></div>
<p class="kicker">{t("kicker")}</p>
<h1>Atria Eponym</h1>
<p class="lead">{t("lead")}</p>
<div class="stats">{stats_html}</div>
<div class="filters">{"".join(filters)}</div>
<div class="grid">
{chr(10).join(card(a, standalone) for a in apps)}
</div>
<footer><span>{t("publisher")} · <a href="mailto:atria.eponym@gmail.com">atria.eponym@gmail.com</a></span><span>© 2026 Atria.Eponym</span></footer>
</div>
{SCRIPT}
</body>
</html>
"""


def main() -> None:
    apps = json.loads((ROOT / "_showcase" / "apps.json").read_text(encoding="utf-8"))["apps"]
    check(apps)
    if len(sys.argv) == 3 and sys.argv[1] == "--standalone":
        Path(sys.argv[2]).write_text(page(apps, True), encoding="utf-8")
        print(f"{sys.argv[2]}: {len(apps)} apps, icons inlined")
        return
    (ROOT / "index.html").write_text(page(apps, False), encoding="utf-8")
    print(f"index.html: {len(apps)} apps")


if __name__ == "__main__":
    main()
