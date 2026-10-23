#!/usr/bin/env python3
"""Builds the site's home page (index.html): a showcase of every Atria.Eponym app.

The list lives in _showcase/apps.json (Jekyll does not publish folders starting with "_").
Each app has a name, an icon, a tagline and feature chips in French and English, and one row per
platform (Android, iPhone, Mac/PC) with its channel (Google Play, App Store, direct download, Microsoft Store) and a
real status (live / soon). When an app is published or changes status, edit apps.json, run this
script from the repository root, commit and push.

One page per language: English at the root (also the default for search engines), the 27 others in
/<lang>/. Texts in French and English live here and in apps.json; the other languages in
_showcase/i18n/<lang>.json (interface and feature chips) and _showcase/i18n/_store_taglines.json (the
short description of the app's own store listing, when it exists in that language). The script also
writes sitemap.xml and robots.txt.

    python3 _showcase/build.py              # writes index.html, <lang>/index.html, sitemap.xml, robots.txt
    python3 _showcase/build.py --standalone out.html [lang]   # one page with icons inlined (mockups)
"""
import base64
import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://atriaeponym.com"  # canonical address; atriaeponym.github.io serves the same files
# Site language code: (native name, BCP 47 tag for hreflang and Open Graph, right-to-left)
LANGS = {
    "en": ("English", "en", False), "fr": ("Français", "fr", False), "de": ("Deutsch", "de", False),
    "es": ("Español", "es", False), "it": ("Italiano", "it", False), "pt": ("Português", "pt-PT", False),
    "pt-br": ("Português (Brasil)", "pt-BR", False), "nl": ("Nederlands", "nl", False),
    "sv": ("Svenska", "sv", False), "nb": ("Norsk bokmål", "nb", False), "fi": ("Suomi", "fi", False),
    "pl": ("Polski", "pl", False), "ru": ("Русский", "ru", False), "uk": ("Українська", "uk", False),
    "el": ("Ελληνικά", "el", False), "tr": ("Türkçe", "tr", False), "ar": ("العربية", "ar", True),
    "fa": ("فارسی", "fa", True), "he": ("עברית", "he", True), "ur": ("اردو", "ur", True),
    "hi": ("हिन्दी", "hi", False), "bn": ("বাংলা", "bn", False), "th": ("ไทย", "th", False),
    "vi": ("Tiếng Việt", "vi", False), "id": ("Bahasa Indonesia", "id", False), "ja": ("日本語", "ja", False),
    "ko": ("한국어", "ko", False), "zh": ("简体中文", "zh-Hans", False),
}
# schema.org category of each app, for search engines
CATEGORY = {"familypocket": "FinanceApplication", "speedgps": "TravelApplication", "maclive": "UtilitiesApplication",
            "dicteednb": "EducationalApplication", "parfumpocket": "ShoppingApplication",
            "stockcockpit": "FinanceApplication", "soundcatch": "MultimediaApplication"}
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
        "title": "Applications pour Android, iPhone, Mac et PC", "developed_by": "Développé par", "language": "Langue",
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
        "title": "Apps for Android, iPhone, Mac and PC", "developed_by": "Developed by", "language": "Language",
    },
}

# Generic line icons (no brand logos).
ICON = {
    "android": '<svg viewBox="0 0 24 24"><rect x="6" y="2.5" width="12" height="19" rx="2.5"/><path d="M10.5 18.5h3"/></svg>',
    "iphone": '<svg viewBox="0 0 24 24"><rect x="6.5" y="2.5" width="11" height="19" rx="3"/><path d="M10.5 4.8h3"/></svg>',
    "mac": '<svg viewBox="0 0 24 24"><rect x="4" y="4.5" width="16" height="11" rx="1.6"/><path d="M2 19.5h20"/></svg>',
    "arrow": '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg>',
    "check": '<svg viewBox="0 0 24 24"><path d="M5 12l5 5L20 7"/></svg>',
    "globe": '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.5 2.6 3.8 5.6 3.8 9s-1.3 6.4-3.8 9c-2.5-2.6-3.8-5.6-3.8-9S9.5 5.6 12 3z"/></svg>',
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
.lang{position:relative}
.lang summary{list-style:none;display:flex;align-items:center;gap:7px;font-weight:650;font-size:13px;line-height:1;color:#1A1206;background:var(--accent);border-radius:999px;padding:8px 12px;cursor:pointer}
.lang summary::-webkit-details-marker{display:none}
.lang summary svg{width:15px;height:15px}
.lang ul{position:absolute;z-index:5;inset-inline-end:0;top:calc(100% + 8px);margin:0;padding:6px;list-style:none;display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2px;width:min(360px,calc(100vw - 32px));background:#111823;border:1px solid var(--tile);border-radius:14px;box-shadow:0 18px 50px rgba(0,0,0,.6)}
.lang a{display:block;padding:8px 10px;border-radius:8px;color:var(--ink);text-decoration:none;font-size:14px}
.lang a:hover{background:var(--soft)}
.lang a[aria-current]{color:var(--accent);font-weight:650}
.hero{position:relative;display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:24px;align-items:center;margin-bottom:34px}
.hero>div{position:relative;z-index:1}
.orbit{position:absolute;right:-60px;top:-70px;width:520px;height:520px;pointer-events:none;overflow:visible}
.orbit path{fill:none;stroke:url(#og);stroke-width:1;opacity:.55}
.orbit circle{fill:var(--accent2)}
.orbit .glow{filter:drop-shadow(0 0 6px #F5A623) drop-shadow(0 0 14px rgba(245,166,35,.7))}
.sky{position:fixed;inset:0;pointer-events:none;overflow:hidden;z-index:0}
.sky i{position:absolute;width:2px;height:2px;border-radius:50%;background:#fff;box-shadow:0 0 6px #fff;animation:twinkle 4s ease-in-out infinite}
@keyframes twinkle{0%,100%{opacity:.15}50%{opacity:.95}}
.sky b{position:absolute;top:var(--y);left:var(--x);width:140px;height:1.5px;border-radius:2px;background:linear-gradient(90deg,rgba(255,215,140,0),#FFE3A8);transform:rotate(-24deg);opacity:0;animation:shoot var(--t) linear infinite;animation-delay:var(--d)}
@keyframes shoot{0%{opacity:0;translate:0 0}2%{opacity:1}9%{opacity:0;translate:-420px 190px}100%{opacity:0;translate:-420px 190px}}
.w{z-index:1}
.kicker{color:var(--accent);font-weight:650;font-size:12px;line-height:1;letter-spacing:.2em;text-transform:uppercase;margin:0 0 14px}
h1{font-weight:800;font-size:clamp(38px,7vw,64px);line-height:1;margin:0 0 16px;letter-spacing:-.03em;background:linear-gradient(100deg,#FFE3A8 0%,#F5A623 45%,#E2721B 100%);-webkit-background-clip:text;background-clip:text;color:transparent;filter:drop-shadow(0 4px 24px rgba(245,166,35,.25))}
.lead{color:var(--dim);margin:0;max-width:560px;font-size:17.5px}
.cloud{position:relative;height:300px}
.cloud .tile{position:absolute;width:calc(var(--s) * var(--k, 1));height:calc(var(--s) * var(--k, 1));transform:rotate(var(--r));filter:drop-shadow(0 0 6px rgba(245,166,35,.45))}
.cloud .tile canvas{display:block;width:100%;height:100%}
.cloud img{position:absolute;width:calc(var(--s) * var(--k, 1));height:calc(var(--s) * var(--k, 1));border-radius:22%;box-shadow:0 12px 34px rgba(0,0,0,.55),0 0 0 1px rgba(255,255,255,.08),0 0 30px rgba(245,166,35,.18);transform:rotate(var(--r))}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:0 0 30px}
.stat{background:var(--card);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border:1px solid var(--line);border-radius:16px;padding:16px 18px;position:relative;overflow:hidden}
.stat:after{content:"";position:absolute;left:0;right:0;top:0;height:1px;background:linear-gradient(90deg,transparent,rgba(245,166,35,.7),transparent)}
.stat b{display:block;font-weight:800;font-size:28px;line-height:1.1;letter-spacing:-.01em;color:var(--accent2)}
.stat b small{font-size:15px;font-weight:600;color:var(--dim)}
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
@media (max-width:860px){.hero{grid-template-columns:1fr}.cloud{height:280px;max-width:300px;width:calc(100% - 40px);margin:0 auto;--k:.86}.cloud .tile{left:-11%!important}.orbit{width:380px;height:380px;right:-120px;top:-40px}}
@media (max-width:760px){.app.has-media{grid-template-columns:1fr;gap:20px}.media{width:min(230px,70vw);order:-1}}
@media (max-width:640px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}.orbit .moving,.sky{display:none}}
"""

SCRIPT = """<script>
(function(){
  var still = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var vids = document.querySelectorAll('video[data-src]');
  function start(v){ if (!v.getAttribute('src')) v.src = v.dataset.src; if (!still) v.play().catch(function(){}); }
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function(es){ es.forEach(function(e){
      if (e.isIntersecting) start(e.target); else e.target.pause();
    }); }, {rootMargin: '200px'});
    vids.forEach(function(v){ io.observe(v); });
  } else vids.forEach(start);
  document.querySelectorAll('.lang a').forEach(function(a){ a.onclick = function(){
    try { localStorage.setItem('lang', a.dataset.lang); } catch (e) {}
  }; });
  // Aizawa attractor in its tile among the icons: one trajectory drawn as a fading trail, turning slowly
  // (Romain's equation-03 animation, in gold).
  var cv = document.querySelector('.aizawa');
  if (cv && cv.getContext) {
    var g = cv.getContext('2d'), dpr = Math.min(devicePixelRatio || 1, 2), W, H, on = true;
    var a = .95, b = .7, c = .6, d = 3.5, e = .25, f = .1, st = [.1, 0, 0], pts = [], MAX = 1500, last = 0, t0 = 0;
    function size() { W = cv.clientWidth; H = cv.clientHeight; cv.width = W * dpr; cv.height = H * dpr; g.setTransform(dpr, 0, 0, dpr, 0, 0); }
    function project(x, y, z, t) {
      var ang = t * .2, ca = Math.cos(ang), sa = Math.sin(ang), xr = x * ca - y * sa, yr = x * sa + y * ca, sc = Math.min(W, H) * .3;
      return [W / 2 + xr * sc, H / 2 + (z - .5) * sc * .6 - yr * sc * .2];
    }
    function advance(t, dt) {
      var h = dt * .5 / 4;
      for (var k = 0; k < 4; k++) {
        var x = st[0], y = st[1], z = st[2];
        st[0] += ((z - b) * x - d * y) * h;
        st[1] += (d * x + (z - b) * y) * h;
        st[2] += (c + a * z - z * z * z / 3 - (x * x + y * y) * (1 + e * z) + f * z * x * x * x) * h;
      }
      pts.push(project(st[0], st[1], st[2], t));
      if (pts.length > MAX) pts.shift();
    }
    function frame(t, dt) {
      g.globalCompositeOperation = 'destination-out'; g.fillStyle = 'rgba(0,0,0,.1)'; g.fillRect(0, 0, W, H);
      g.globalCompositeOperation = 'source-over';
      advance(t, dt);
      g.lineWidth = 1.1;
      for (var i = 1; i < pts.length; i++) {
        g.strokeStyle = 'hsla(' + (38 + Math.sin(i * .01) * 10) + ',95%,' + (58 + Math.sin(i * .013) * 12) + '%,' + (i / pts.length * .95) + ')';  // gold, like the page
        g.beginPath(); g.moveTo(pts[i - 1][0], pts[i - 1][1]); g.lineTo(pts[i][0], pts[i][1]); g.stroke();
      }
    }
    function loop(ms) {
      var t = ms / 1000, dt = Math.min(.05, t - (last || t)); last = t;
      if (on && !document.hidden) frame(t, dt);
      requestAnimationFrame(loop);
    }
    size(); addEventListener('resize', size);
    // start with the trail already drawn: 40 s of trajectory computed before the first frame
    for (var r = -2400; r < 0; r++) advance(performance.now() / 1000 + r / 60, 1 / 60);
    if (still) frame(performance.now() / 1000, 0);  // reduced motion: one still drawing
    else {
      if ('IntersectionObserver' in window) new IntersectionObserver(function(es){ on = es[0].isIntersecting; }).observe(cv);
      requestAnimationFrame(loop);
    }
  }
  var fs = document.querySelectorAll('.filters button');
  fs.forEach(function(b){ b.onclick = function(){
    fs.forEach(function(x){ x.setAttribute('aria-pressed', x === b); });
    document.querySelectorAll('.app').forEach(function(a){
      a.hidden = b.dataset.f !== 'all' && a.dataset.p.split(' ').indexOf(b.dataset.f) < 0;
    });
  }; });
})();
</script>"""

# On the English root only: a visitor whose browser asks for another language of the site, and who has
# not picked one in the menu, is sent to that language's page. ?lang=xx forces a page.
ROOT_REDIRECT = """<script>
(function(){
  var langs = %s, pick = null;
  try { pick = localStorage.getItem('lang'); } catch (e) {}
  var q = new URLSearchParams(location.search).get('lang');
  if (q) pick = q;
  if (!pick) {
    var navs = navigator.languages || [navigator.language || 'en'];
    for (var i = 0; i < navs.length && !pick; i++) {
      var n = navs[i].toLowerCase();
      if (n === 'pt-br') pick = 'pt-br';
      else if (n === 'no' || n.indexOf('no-') === 0 || n.indexOf('nn') === 0) pick = 'nb';
      else if (n.indexOf('iw') === 0) pick = 'he';
      else if (langs.indexOf(n.split('-')[0]) >= 0) pick = n.split('-')[0];
    }
  }
  if (pick && pick !== 'en' && langs.indexOf(pick) >= 0) location.replace('/' + pick + '/' + location.hash);
})();
</script>"""


def load_texts() -> dict:
    """Interface texts per language, with the per-app texts under "_apps"."""
    apps = json.loads((ROOT / "_showcase" / "apps.json").read_text(encoding="utf-8"))["apps"]
    store = json.loads((ROOT / "_showcase" / "i18n" / "_store_taglines.json").read_text(encoding="utf-8"))["apps"]
    out = {}
    for lang in LANGS:
        if lang in TEXT:
            ui = dict(TEXT[lang])
            ui["_apps"] = {a["id"]: {"tagline": a["tagline"][lang], "features": a["features"][lang]} for a in apps}
        else:
            ui = json.loads((ROOT / "_showcase" / "i18n" / f"{lang}.json").read_text(encoding="utf-8"))
            ui = {**ui["ui"], "_apps": ui["apps"]}
            for a in apps:
                own = ui["_apps"].setdefault(a["id"], {})
                if lang in store.get(a["id"], {}):
                    own["tagline"] = store[a["id"]][lang]
                assert own.get("tagline") and own.get("features"), (lang, a["id"])
        missing = set(TEXT["en"]) - set(ui)
        assert not missing, (lang, missing)
        out[lang] = ui
    return out


def url(lang: str) -> str:
    return f"{SITE}/" if lang == "en" else f"{SITE}/{lang}/"


def asset(path: str, standalone: bool) -> str:
    data = (ROOT / path).read_bytes()
    if standalone:
        kind = {"png": "image/png", "jpg": "image/jpeg", "mp4": "video/mp4"}[path.rsplit(".", 1)[1]]
        return f"data:{kind};base64," + base64.b64encode(data).decode()
    # Root-relative, so it works from every language folder and on both domains; a content hash in the
    # URL, so a changed file is never served from a browser's cache.
    return f"/{path}?v={hashlib.sha256(data).hexdigest()[:10]}"


def local(path: str, lang: str) -> str:
    """A page of the site, in the visitor's language when that version exists."""
    path = path.strip("/")
    if lang != "fr" and (ROOT / path / lang / "index.html").is_file():
        return f"/{path}/{lang}/"
    return f"/{path}/"


def name(a: dict, lang: str) -> str:
    """The app's name: one string, or {"fr": ..., "en": ...}; other languages use the English one."""
    return a["name"] if isinstance(a["name"], str) else a["name"].get(lang, a["name"]["en"])


def row(p: dict, T: dict) -> str:
    status = p["status"]
    badge = f'<span class="badge">{ICON["check"] if status == "live" else ICON["clock"]}{html.escape(T[status])}</span>'
    inner = (f'<span class="pf">{ICON[p["platform"]]}<span><b>{html.escape(T[p["platform"]])}</b>'
             f'<small>{html.escape(T[p["channel"]])}{" · " + html.escape(p["name"]) if p.get("name") else ""}</small></span></span>{badge}')
    if status == "live":
        href = p["url"] if p["url"].startswith("http") else "/" + p["url"].lstrip("/")
        return f'<a class="row live" href="{html.escape(href)}">{inner}<span class="go">{ICON["arrow"]}</span></a>'
    return f'<div class="row soon">{inner}</div>'


def media(a: dict, lang: str, standalone: bool) -> str:
    """Looping teaser in a phone frame: muted, loaded only when visible, poster only under reduced motion."""
    tz = a.get("teaser")
    if not tz:
        return ""
    tz = tz.get(lang) or tz.get("en") or next(iter(tz.values()))
    return (f'<div class="media"><div class="phone"><video data-src="{asset(tz["video"], standalone)}" '
            f'poster="{asset(tz["poster"], standalone)}" muted loop playsinline preload="none" '
            f'aria-label="{html.escape(name(a, lang))}"></video></div><span class="example">{{example}}</span></div>')


def card(a: dict, lang: str, T: dict, standalone: bool) -> str:
    own = T["_apps"][a["id"]]
    chips = "".join(f"<span>{html.escape(f)}</span>" for f in own["features"])
    if a.get("more_features"):
        chips += f'<span class="more">{html.escape(T["more_features"])}</span>'
    links = []
    if a.get("more"):
        links.append(f'<a href="{local(a["more"], lang)}">{html.escape(T["more"])}</a>')
    for p in a.get("privacy", []):
        label = T["privacy"] + (f' {T[p["platform"]]}' if p.get("platform") else "")
        links.append(f'<a href="{local(p["url"], lang)}">{html.escape(label)}</a>')
    platforms = " ".join(p["platform"] for p in a["platforms"])
    m = media(a, lang, standalone).replace("{example}", html.escape(T["example"]))
    return (f'<article class="app{" has-media" if m else ""}" id="{a["id"]}" data-p="{platforms}"><div class="body">'
            f'<div class="head"><img src="{html.escape(asset(a["icon"], standalone))}" alt="" width="66" height="66">'
            f'<h2>{html.escape(name(a, lang))}</h2></div>'
            f'<p class="tag">{html.escape(own["tagline"])}</p>'
            f'<div class="chips">{chips}</div>'
            f'<div class="rows">{"".join(row(p, T) for p in sorted(a["platforms"], key=lambda p: PLATFORMS.index(p["platform"])))}</div>'
            f'<div class="links">{"".join(links)}</div></div>{m}</article>')


def check(apps: list) -> None:
    for a in apps:
        assert (ROOT / a["icon"]).is_file(), a["icon"]
        assert a["id"] in CATEGORY, a["id"]
        for l, tz in a.get("teaser", {}).items():
            assert l in TEXT and (ROOT / tz["video"]).is_file() and (ROOT / tz["poster"]).is_file(), (a["id"], l)
        for p in a["platforms"]:
            assert p["platform"] in PLATFORMS and p["channel"] in ("play", "appstore", "direct", "msstore"), (a["id"], p)
            assert p["status"] in ("live", "soon") and (p["status"] == "soon" or p.get("url")), (a["id"], p)


def structured(apps: list, lang: str, T: dict) -> str:
    """schema.org data: the publisher and each app, with only what the page itself shows."""
    systems = {"android": "Android", "iphone": "iOS", "mac": "macOS, Windows"}
    items = []
    for i, a in enumerate(apps, 1):
        live = [p for p in a["platforms"] if p["status"] == "live"]
        app = {"@type": "SoftwareApplication", "name": name(a, lang), "description": T["_apps"][a["id"]]["tagline"],
               "applicationCategory": CATEGORY[a["id"]], "image": f"{SITE}/{a['icon']}",
               "operatingSystem": ", ".join(dict.fromkeys(systems[p["platform"]] for p in live)) or None,
               "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"},
               "author": {"@id": f"{SITE}/#publisher"},
               "sameAs": [p["url"] for p in live if p["url"].startswith("http")] or None}
        items.append({"@type": "ListItem", "position": i, "item": {k: v for k, v in app.items() if v}})
    data = {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": f"{SITE}/#publisher", "name": "Atria.Eponym", "url": f"{SITE}/",
         "logo": f"{SITE}/icons/gecko.png", "email": "atria.eponym@gmail.com"},
        {"@type": "WebSite", "name": "Atria.Eponym", "url": f"{SITE}/", "inLanguage": LANGS[lang][1]},
        {"@type": "ItemList", "name": T["title"], "itemListElement": items}]}
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def page(apps: list, lang: str, texts: dict, standalone: bool) -> str:
    T = texts[lang]
    native, tag, rtl = LANGS[lang]
    used = [pf for pf in PLATFORMS if any(p["platform"] == pf for a in apps for p in a["platforms"])]
    filters = [f'<button data-f="all" aria-pressed="true">{html.escape(T["all"])} <em>{len(apps)}</em></button>']
    for pf in used:
        n = sum(any(p["platform"] == pf for p in a["platforms"]) for a in apps)
        filters.append(f'<button data-f="{pf}" aria-pressed="false">{ICON[pf]}{html.escape(T[pf])} <em>{n}</em></button>')
    # Most apps ship in 28 languages, some in fewer (SoundCatch: French only); none shows ads.
    upto = f'<small>{html.escape(T["upto"])}</small>' if T["upto"].strip() else ""
    stats = [(str(len(apps)), "apps"), (str(len(used)), "platforms_n"), (upto + "28", "languages"), ("0", "ads")]
    stats_html = "".join(f'<div class="stat"><b>{v}</b><span>{html.escape(T[k])}</span></div>' for v, k in stats)
    gecko = asset("icons/gecko.png", standalone)
    # Icons beside the title, in three staggered columns of a 340 x 300 box: (x, y, size, tilt), in px.
    # The Aizawa attractor has its own place between the piggy bank and the perfume bottle, out on the
    # outer orbit, drawn alone (no tile).
    spots = {"familypocket": (6, 0, 88, -6), "aizawa": (-96, 96, 110, -4), "parfumpocket": (10, 212, 80, 5),
             "speedgps": (124, 6, 82, 4), "dicteednb": (114, 100, 104, 2), "stockcockpit": (124, 214, 82, -5),
             "soundcatch": (244, 48, 82, 7), "maclive": (236, 148, 96, -3)}
    def place(key):
        x, y, sz, r = spots[key]
        return f'style="left:{x / 3.4:.1f}%;top:{y / 3:.1f}%;--s:{sz}px;--r:{r}deg"'
    cloud = "".join(f'<img src="{html.escape(asset(a["icon"], standalone))}" alt="" {place(a["id"])}>'
                    for a in apps if a["id"] in spots)
    cloud += f'<div class="tile" {place("aizawa")}><canvas class="aizawa"></canvas></div>'
    names = ", ".join(name(a, lang) for a in apps)
    title = f"Atria.Eponym – {T['title']}"
    desc = f"{T['lead']} {names}."
    alternates = "".join(f'<link rel="alternate" hreflang="{LANGS[l][1]}" href="{url(l)}">' for l in LANGS)
    alternates += f'<link rel="alternate" hreflang="x-default" href="{url("en")}">'
    menu = "".join(f'<li><a href="{"/" if l == "en" else "/" + l + "/"}" hreflang="{LANGS[l][1]}" lang="{LANGS[l][1]}" '
                   f'data-lang="{l}"{" aria-current=\"page\"" if l == lang else ""}>{html.escape(LANGS[l][0])}</a></li>'
                   for l in LANGS)
    og_locales = "".join(f'<meta property="og:locale:alternate" content="{LANGS[l][1].replace("-", "_")}">'
                         for l in LANGS if l != lang)
    redirect = ROOT_REDIRECT % json.dumps(list(LANGS)) if lang == "en" and not standalone else ""
    return f"""<!doctype html>
<html lang="{tag}"{' dir="rtl"' if rtl else ""}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{url(lang)}">
{alternates}
<link rel="icon" href="/icons/gecko.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Atria.Eponym">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{url(lang)}">
<meta property="og:image" content="{SITE}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="{tag.replace("-", "_")}">
{og_locales}
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">{structured(apps, lang, T)}</script>
{redirect}
<style>{CSS}</style>
</head>
<body>
<div class="sky" aria-hidden="true"><i style="left:14%;top:18%;animation-delay:-0s;animation-duration:4s"></i><i style="left:38%;top:9%;animation-delay:-1.3s;animation-duration:5s"></i><i style="left:63%;top:26%;animation-delay:-2.1s;animation-duration:3.6s"></i><i style="left:82%;top:58%;animation-delay:-0.7s;animation-duration:4.4s"></i><i style="left:24%;top:72%;animation-delay:-2.8s;animation-duration:5.2s"></i><i style="left:51%;top:44%;animation-delay:-1.9s;animation-duration:3.8s"></i><i style="left:91%;top:12%;animation-delay:-3.1s;animation-duration:4.6s"></i><i style="left:7%;top:47%;animation-delay:-0.4s;animation-duration:4.1s"></i><i style="left:72%;top:84%;animation-delay:-2.4s;animation-duration:5s"></i><b style="--x:78%;--y:6%;--t:11s;--d:2s"></b><b style="--x:96%;--y:30%;--t:17s;--d:9s"></b></div>
<div class="w">
<div class="bar"><div class="brand"><img src="{gecko}" alt=""><span class="nm">Atria<span>.</span>Eponym</span></div><details class="lang"><summary aria-label="{html.escape(T["language"])}">{ICON["globe"]}{html.escape(native)}</summary><ul>{menu}</ul></details></div>
<div class="hero">
<svg class="orbit" viewBox="0 0 520 520" aria-hidden="true"><defs><linearGradient id="og" x1="0" x2="1"><stop offset="0" stop-color="#F5A623" stop-opacity="0"/><stop offset=".5" stop-color="#F5A623" stop-opacity=".8"/><stop offset="1" stop-color="#F5A623" stop-opacity="0"/></linearGradient></defs><g transform="rotate(-18 260 260)"><path id="o1" d="M-15,260 a275,138 0 1,1 550,0 a275,138 0 1,1 -550,0"/><path id="o2" d="M50,260 a210,96 0 1,1 420,0 a210,96 0 1,1 -420,0"/><g class="moving"><circle r="4" opacity="1" class="glow"><animateMotion dur="84s" begin="-3.60s" repeatCount="indefinite" rotate="auto"><mpath href="#o1"/></animateMotion></circle><circle r="3.2" opacity="0.55"><animateMotion dur="84s" begin="-2.88s" repeatCount="indefinite" rotate="auto"><mpath href="#o1"/></animateMotion></circle><circle r="2.6" opacity="0.32"><animateMotion dur="84s" begin="-2.16s" repeatCount="indefinite" rotate="auto"><mpath href="#o1"/></animateMotion></circle><circle r="2" opacity="0.18"><animateMotion dur="84s" begin="-1.44s" repeatCount="indefinite" rotate="auto"><mpath href="#o1"/></animateMotion></circle><circle r="1.6" opacity="0.09"><animateMotion dur="84s" begin="-0.72s" repeatCount="indefinite" rotate="auto"><mpath href="#o1"/></animateMotion></circle><circle r="3" opacity="1" class="glow"><animateMotion dur="36s" begin="-17.60s" repeatCount="indefinite" rotate="auto"><mpath href="#o2"/></animateMotion></circle><circle r="2.4" opacity="0.55"><animateMotion dur="36s" begin="-17.28s" repeatCount="indefinite" rotate="auto"><mpath href="#o2"/></animateMotion></circle><circle r="1.95" opacity="0.32"><animateMotion dur="36s" begin="-16.96s" repeatCount="indefinite" rotate="auto"><mpath href="#o2"/></animateMotion></circle><circle r="1.5" opacity="0.18"><animateMotion dur="36s" begin="-16.64s" repeatCount="indefinite" rotate="auto"><mpath href="#o2"/></animateMotion></circle><circle r="1.2" opacity="0.09"><animateMotion dur="36s" begin="-16.32s" repeatCount="indefinite" rotate="auto"><mpath href="#o2"/></animateMotion></circle></g></g></svg>
<div><p class="kicker">{html.escape(T["kicker"])}</p>
<h1>Atria.Eponym</h1>
<p class="lead">{html.escape(T["lead"])}</p></div>
<div class="cloud" aria-hidden="true">{cloud}</div>
</div>
<div class="stats">{stats_html}</div>
<div class="filters">{"".join(filters)}</div>
<div class="grid">
{chr(10).join(card(a, lang, T, standalone) for a in apps)}
</div>
<footer><p class="by">{html.escape(T["developed_by"])}</p><img class="gecko" src="{gecko}" alt="" width="84" height="84"><p class="sig">Atria<span>.</span>Eponym</p><p>{html.escape(T["publisher"])} · <a href="mailto:atria.eponym@gmail.com">atria.eponym@gmail.com</a><br>© 2026 Atria.Eponym</p></footer>
</div>
{SCRIPT}
</body>
</html>
"""


def sitemap() -> str:
    alternates = "".join(f'<xhtml:link rel="alternate" hreflang="{LANGS[l][1]}" href="{url(l)}"/>' for l in LANGS)
    alternates += f'<xhtml:link rel="alternate" hreflang="x-default" href="{url("en")}"/>'
    urls = "".join(f"<url><loc>{url(l)}</loc>{alternates}</url>\n" for l in LANGS)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            f'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n{urls}</urlset>\n')


def main() -> None:
    apps = json.loads((ROOT / "_showcase" / "apps.json").read_text(encoding="utf-8"))["apps"]
    check(apps)
    texts = load_texts()
    if len(sys.argv) >= 3 and sys.argv[1] == "--standalone":
        lang = sys.argv[3] if len(sys.argv) > 3 else "fr"
        Path(sys.argv[2]).write_text(page(apps, lang, texts, True), encoding="utf-8")
        print(f"{sys.argv[2]}: {len(apps)} apps, {lang}, icons inlined")
        return
    for lang in LANGS:
        out = ROOT / "index.html" if lang == "en" else ROOT / lang / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(page(apps, lang, texts, False), encoding="utf-8")
    (ROOT / "sitemap.xml").write_text(sitemap(), encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")
    print(f"index.html + {len(LANGS) - 1} language pages, sitemap.xml, robots.txt: {len(apps)} apps")


if __name__ == "__main__":
    main()
