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
:root{color-scheme:dark;--bg:#070B12;--card:rgba(17,24,35,.72);--soft:rgba(255,255,255,.06);--ink:#EEF1F7;--dim:#93A0B5;--line:rgba(255,255,255,.09);--tile:rgba(245,166,35,.28);--accent:#F5A623;--accent2:#FFCF6E;--ok:#4CC38A;--okbg:rgba(76,195,138,.13);--soon:#A3ADBE;--soonbg:rgba(163,173,190,.12)}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;background:var(--bg);overflow-x:clip}
body{margin:0;color:var(--ink);font:400 16px/1.55 -apple-system,"Segoe UI",Roboto,system-ui,sans-serif;-webkit-font-smoothing:antialiased;min-height:100vh;position:relative;overflow-x:clip;
background:radial-gradient(900px 520px at 78% -6%,rgba(245,166,35,.22),transparent 62%),radial-gradient(700px 480px at -8% 18%,rgba(64,120,255,.13),transparent 60%),radial-gradient(800px 600px at 50% 110%,rgba(245,120,35,.10),transparent 60%),var(--bg)}
body:before{content:"";position:fixed;inset:0;pointer-events:none;opacity:.55;background-image:radial-gradient(1px 1px at 12% 22%,#fff8,transparent),radial-gradient(1px 1px at 32% 8%,#fff6,transparent),radial-gradient(1.5px 1.5px at 66% 30%,#ffd59a99,transparent),radial-gradient(1px 1px at 84% 62%,#fff6,transparent),radial-gradient(1px 1px at 22% 78%,#fff5,transparent),radial-gradient(1.5px 1.5px at 48% 52%,#fff4,transparent),radial-gradient(1px 1px at 92% 14%,#fff7,transparent),radial-gradient(1px 1px at 6% 52%,#fff5,transparent),radial-gradient(1px 1px at 58% 88%,#ffd59a88,transparent)}
svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round;flex:none}
.w{position:relative;max-width:1080px;margin:0 auto;padding:24px 16px 40px}
.bar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:28px}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:15px;line-height:1;letter-spacing:.02em}
.brand img{width:30px;height:30px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 1.5px var(--accent),0 0 14px rgba(245,166,35,.5)}
.brand .nm span{color:var(--accent)}
.lang{display:flex;gap:4px}
.lang button{font-weight:600;font-size:12px;line-height:1;color:var(--dim);background:var(--soft);border:1px solid var(--line);border-radius:999px;padding:7px 11px;cursor:pointer}
.lang button[aria-pressed="true"]{color:#1A1206;background:var(--accent);border-color:var(--accent)}
.hero{position:relative;display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:24px;align-items:center;margin-bottom:34px}
.orbit{position:absolute;right:-60px;top:-70px;width:520px;height:520px;pointer-events:none;opacity:.55}
.orbit ellipse{fill:none;stroke:url(#og);stroke-width:1}
.orbit circle{fill:var(--accent2);filter:drop-shadow(0 0 6px #F5A623)}
.kicker{color:var(--accent);font-weight:650;font-size:12px;line-height:1;letter-spacing:.2em;text-transform:uppercase;margin:0 0 14px}
h1{font-weight:800;font-size:clamp(38px,7vw,64px);line-height:1;margin:0 0 16px;letter-spacing:-.03em;background:linear-gradient(100deg,#FFE3A8 0%,#F5A623 45%,#E2721B 100%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 4px 24px rgba(245,166,35,.25))}
.lead{color:var(--dim);margin:0;max-width:560px;font-size:17.5px}
.cloud{position:relative;height:300px}
.cloud img{position:absolute;width:var(--s);height:var(--s);border-radius:22%;box-shadow:0 12px 34px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.08),0 0 30px rgba(245,166,35,.18);animation:float 7s ease-in-out infinite;animation-delay:var(--d)}
@keyframes float{0%,100%{transform:translateY(0) rotate(var(--r))}50%{transform:translateY(-10px) rotate(var(--r))}}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:0 0 30px}
.stat{background:var(--card);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border:1px solid var(--line);border-radius:16px;padding:16px 18px;position:relative;overflow:hidden}
.stat:after{content:"";position:absolute;left:0;right:0;top:0;height:1px;background:linear-gradient(90deg,transparent,rgba(245,166,35,.7),transparent)}
.stat b{display:block;font-weight:800;font-size:28px;line-height:1.1;letter-spacing:-.01em;color:var(--accent2)}
.stat b [data-l]{font-size:15px;font-weight:600;color:var(--dim)}
.stat span{color:var(--dim);font-size:13px}
.filters{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px}
.filters button{display:inline-flex;align-items:center;gap:7px;font-weight:600;font-size:14px;line-height:1;color:var(--dim);background:var(--soft);border:1px solid var(--line);border-radius:999px;padding:9px 14px;cursor:pointer;transition:all .15s}
.filters button:hover{color:var(--ink);border-color:var(--tile)}
.filters button[aria-pressed="true"]{color:#1A1206;background:linear-gradient(135deg,#FFCF6E,#F5A623);border-color:transparent;box-shadow:0 4px 18px rgba(245,166,35,.35)}
.filters em{font-style:normal;opacity:.7;font-size:12px}
.grid{display:grid;gap:18px}
.app.has-media{display:grid;grid-template-columns:minmax(0,1fr) 230px;gap:28px;align-items:center}
.body{display:flex;flex-direction:column;min-width:0}
.media{justify-self:center;width:230px}
.phone{position:relative;border-radius:34px;padding:7px;background:linear-gradient(160deg,#2a3242,#0d1118);box-shadow:0 22px 50px rgba(0,0,0,.6),0 0 40px rgba(245,166,35,.12),inset 0 0 0 1px rgba(255,255,255,.1)}
.phone video{display:block;width:100%;aspect-ratio:540/1174;border-radius:28px;background:#0d1118;object-fit:cover}
.example{display:block;text-align:center;color:var(--dim);font-size:12px;margin-top:8px}
.app{position:relative;display:flex;flex-direction:column;background:linear-gradient(160deg,rgba(26,34,48,.85),rgba(12,17,26,.85));backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border:1px solid var(--tile);border-radius:22px;padding:22px;overflow:hidden;transition:transform .2s,box-shadow .2s,border-color .2s}
.app:before{content:"";position:absolute;width:320px;height:320px;left:-120px;top:-160px;background:radial-gradient(closest-side,rgba(245,166,35,.16),transparent);pointer-events:none}
.app:hover{transform:translateY(-3px);box-shadow:0 18px 50px rgba(0,0,0,.5),0 0 0 1px var(--accent),0 0 40px rgba(245,166,35,.18);border-color:var(--accent)}
.app[hidden]{display:none}
.head{position:relative;display:flex;gap:16px;align-items:center;margin-bottom:12px}
.head img{width:66px;height:66px;border-radius:16px;flex:none;box-shadow:0 8px 22px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.08)}
.head h2{font-weight:750;font-size:21px;line-height:1.2;margin:0}
.tag{position:relative;color:var(--dim);margin:0 0 14px;font-size:15px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 16px}
.chips span{font-weight:500;font-size:12.5px;line-height:1;padding:7px 10px;border-radius:8px;background:var(--soft);border:1px solid var(--line);color:var(--ink)}
.chips .more{background:none;border:0;color:var(--accent);font-weight:650;padding-left:2px}
.rows{display:grid;gap:8px;margin-top:auto}
.row{display:flex;align-items:center;gap:12px;padding:11px 12px;border:1px solid var(--line);border-radius:12px;background:rgba(0,0,0,.18);text-decoration:none;color:inherit;transition:background .15s,border-color .15s}
a.row:hover{background:rgba(76,195,138,.08);border-color:rgba(76,195,138,.45)}
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
footer{border-top:1px solid var(--line);margin-top:44px;padding-top:26px;color:var(--dim);font-size:14px;text-align:center}
footer .by{font-size:11.5px;letter-spacing:.22em;text-transform:uppercase;color:var(--dim);margin:0 0 12px}
footer .gecko{display:block;width:84px;height:84px;margin:0 auto 10px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 2px var(--accent),0 0 30px rgba(245,166,35,.45);animation:fadein 2s ease-out both}
footer .sig{font-weight:750;font-size:18px;color:var(--ink);margin:0 0 14px}
footer .sig span{color:var(--accent)}
footer a{color:var(--accent)}
@keyframes fadein{from{opacity:0;transform:scale(.92)}to{opacity:1;transform:none}}
[data-l]{display:none}
html[lang="fr"] [data-l="fr"],html[lang="en"] [data-l="en"]{display:revert}
html[lang="fr"] .chips>[data-l="fr"],html[lang="en"] .chips>[data-l="en"]{display:contents}
@media (max-width:860px){.hero{grid-template-columns:1fr}.cloud{height:230px;max-width:300px;width:calc(100% - 60px);margin:0 auto}.orbit{width:380px;height:380px;right:-120px;top:-40px}}
@media (max-width:760px){.app.has-media{grid-template-columns:1fr;gap:20px}.media{width:min(230px,70vw);order:-1}}
@media (max-width:640px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
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
    gecko = icon_src("icons/gecko.png", standalone)
    # Floating app icons beside the title: position (left %, top %), size, tilt, animation delay.
    spots = [(8, 4, 92, -6, 0), (50, 0, 78, 5, 1.2), (70, 34, 96, -3, .6), (30, 34, 104, 3, 2.1),
             (2, 60, 76, 6, 1.6), (56, 70, 70, -5, .3), (82, 4, 58, 8, 2.6)]
    cloud = "".join(f'<img src="{html.escape(icon_src(a["icon"], standalone))}" alt="" '
                    f'style="left:{x}%;top:{y}%;--s:{sz}px;--r:{r}deg;--d:-{d}s">'
                    for a, (x, y, sz, r, d) in zip(apps, spots))
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
<div class="bar"><div class="brand"><img src="{gecko}" alt=""><span class="nm">Atria<span>.</span>Eponym</span></div><div class="lang"><button data-set="fr">FR</button><button data-set="en">EN</button></div></div>
<div class="hero">
<svg class="orbit" viewBox="0 0 520 520" aria-hidden="true"><defs><linearGradient id="og" x1="0" x2="1"><stop offset="0" stop-color="#F5A623" stop-opacity="0"/><stop offset=".5" stop-color="#F5A623" stop-opacity=".8"/><stop offset="1" stop-color="#F5A623" stop-opacity="0"/></linearGradient></defs><ellipse cx="260" cy="260" rx="240" ry="120" transform="rotate(-18 260 260)"/><ellipse cx="260" cy="260" rx="180" ry="80" transform="rotate(-18 260 260)"/><circle cx="470" cy="190" r="4"/></svg>
<div><p class="kicker">{t("kicker")}</p>
<h1>Atria.Eponym</h1>
<p class="lead">{t("lead")}</p></div>
<div class="cloud" aria-hidden="true">{cloud}</div>
</div>
<div class="stats">{stats_html}</div>
<div class="filters">{"".join(filters)}</div>
<div class="grid">
{chr(10).join(card(a, standalone) for a in apps)}
</div>
<footer><p class="by">{both(lambda l: "Développé par" if l == "fr" else "Developed by")}</p><img class="gecko" src="{gecko}" alt="" width="84" height="84"><p class="sig">Atria<span>.</span>Eponym</p><p>{t("publisher")} · <a href="mailto:atria.eponym@gmail.com">atria.eponym@gmail.com</a><br>© 2026 Atria.Eponym</p></footer>
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
