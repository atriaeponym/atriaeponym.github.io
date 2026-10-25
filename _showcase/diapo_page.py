"""Builds atriaeponym.com/diapo/ (fr) and /diapo/en/ from one template.

Texts are those of Diapo's store listings (32-photo-viewer/store/src/fr.json and en.json); screenshots are
the App Store ones, made from synthetic photos. Usage: python3 _showcase/diapo_page.py .
"""
import html
import pathlib
import sys

site = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")

# Same layout as the publisher's other app pages; colours of Diapo (dark and gold), as its privacy page.
CSS = """*{margin:0;padding:0;box-sizing:border-box}
:root{--page:#F7F5F0;--card:#FFFFFF;--ink:#17150F;--muted:#5F5A50;--line:#E6E1D6;--accent:#A87A1E;--ok:#0B9A69}
@media (prefers-color-scheme:dark){:root{--page:#141416;--card:#1D1D20;--ink:#EEEEEE;--muted:#9A9AA0;--line:#2A2A2E;--accent:#E9C46A;--ok:#3BD69B}}
body{background:var(--page);color:var(--ink);line-height:1.7;padding:24px 16px 90px;
     font-family:-apple-system,'Segoe UI',Roboto,'Noto Sans',Helvetica,sans-serif;
     max-width:860px;margin:0 auto;font-size:16px}
html,body{overflow-x:hidden}
h1{font-size:28px;margin-bottom:4px;font-weight:700}
h2{font-size:19px;margin:36px 0 10px;font-weight:700}
p{margin-bottom:14px;color:var(--muted)}
b,strong{color:var(--ink)}
ul{margin:0 0 16px 22px}
li{margin-bottom:9px;color:var(--muted)}
a{color:var(--accent)}
bdi{white-space:nowrap}
.top{display:flex;justify-content:flex-end;font-size:14px;margin-bottom:16px}
.hero{display:flex;gap:16px;align-items:center;margin-bottom:12px}
.hero img{width:76px;height:76px;border-radius:18px}
.tag{color:var(--muted);font-size:16px}
.box{background:var(--card);border:1px solid var(--line);border-inline-start:3px solid var(--ok);
     border-radius:12px;padding:16px 18px;margin:20px 0}
.box p:last-child{margin-bottom:0}
.btn{display:inline-block;font-weight:700;padding:14px 24px;border-radius:14px;margin:6px 0 8px;
     background:var(--line);color:var(--muted)}
.btn small{display:block;font-weight:400;font-size:12.5px}
.meta{font-size:13.5px;color:var(--muted)}
.stores{display:grid;gap:0 16px;grid-template-columns:repeat(auto-fit,minmax(200px,1fr))}
.platform{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;margin:16px 0}
.platform h2{margin-top:0}
.shots{display:grid;gap:14px;margin:20px 0 6px}
.shots img{width:100%;height:auto;border-radius:14px;border:1px solid var(--line)}
.phones{display:flex;gap:14px;overflow-x:auto;margin:6px 0 6px;padding-bottom:6px}
.phones img{width:220px;height:auto;flex:0 0 auto;border-radius:22px;border:1px solid var(--line)}
footer{margin-top:44px;padding-top:18px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
footer a{color:var(--muted)}
"""

T = {
    "fr": dict(
        up="", other=("en/", "English"), privacy="privacy/",
        title="Diapo — visionneuse photo pour Mac, Windows, iPhone et Android",
        desc="Les photos d'un dossier ou d'un disque entier, en grand, sous-dossiers compris. Vos photos ne sont jamais modifiées.",
        tag="Vos photos en grand",
        intro="<bdi>Diapo</bdi> affiche en grand les photos d'un dossier ou d'un disque entier, sous-dossiers compris. "
              "Vous passez d'une photo à l'autre avec les flèches du clavier, et vos photos ne sont jamais modifiées.",
        alt_mac=["Diapo sur Mac : l'accueil, avec les dossiers à reprendre",
                 "Diapo sur Mac : le mode Pellicule, la photo et une bande de miniatures",
                 "Diapo sur Mac : le mode Planche, une grille de miniatures"],
        alt_phone=["Diapo sur iPhone : le mode Pellicule", "Diapo sur iPhone : une photo en plein écran"],
        on="Sur", soon="Bientôt disponible",
        req={"mac": "macOS 14 ou plus récent", "windows": "Windows 10 (1809) ou plus récent",
             "iphone": "iOS 17 ou plus récent", "android": "Android 8 ou plus récent"},
        box="<strong>Essai gratuit de 14 jours (15 jours sous Windows), puis un achat unique pour continuer. Pas d'abonnement.</strong> "
            "Pas de publicité, pas de pistage, pas de compte.",
        sections=[
            ("Regarder", [
                "Trois modes : <strong>Plein écran</strong>, <strong>Pellicule</strong> (la photo et une bande verticale de miniatures) et <strong>Planche</strong> (une grille de miniatures).",
                "Flèches ← →, clic, molette ou pavé tactile pour avancer. La barre d'espace lance le diaporama automatique.",
                "Sur téléphone : balayez pour passer d'une photo à l'autre, pincez pour zoomer, touchez deux fois pour le plein écran.",
                "Les photos s'affichent dans le bon sens, d'après leur orientation EXIF.",
                "Diapo reprend à la dernière photo vue dans chaque dossier."]),
            ("Formats", ["JPEG, HEIC, PNG, TIFF, WebP, GIF, BMP et RAW (Canon CR2/CR3, Nikon NEF, Sony ARW, DNG…)."]),
            ("Favoris et sélections", [
                "Un cœur, ou la touche F, ajoute une photo à vos Favoris.",
                "Sélections : en parcourant vos disques, marquez des photos d'un clic, puis copiez-les dans un dossier pour les partager. Les doublons sont écartés d'après leur contenu."]),
            ("Vos photos restent intactes", [
                "Diapo ne modifie, ne déplace, ne renomme et ne supprime jamais une photo. Il ne crée que des copies, quand vous le demandez."]),
        ],
        info="Informations", privacy_label="Politique de confidentialité", languages="Disponible en 28 langues.",
        publisher="Atria.Eponym, développeur individuel établi en France",
    ),
    "en": dict(
        up="../", other=("../?lang=fr", "Français"), privacy="../privacy/en/",
        title="Diapo — photo viewer for Mac, Windows, iPhone and Android",
        desc="The photos of a folder or a whole disk, big, subfolders included. Your photos are never modified.",
        tag="Your photos, big",
        intro="<bdi>Diapo</bdi> shows the photos of a folder or a whole disk big on screen, subfolders included. "
              "You go from one photo to the next with the arrow keys, and your photos are never modified.",
        alt_mac=["Diapo on Mac: the home screen, with the folders to resume",
                 "Diapo on Mac: Filmstrip mode, the photo and a strip of thumbnails",
                 "Diapo on Mac: Contact Sheet mode, a grid of thumbnails"],
        alt_phone=["Diapo on iPhone: Filmstrip mode", "Diapo on iPhone: a photo in full screen"],
        on="On", soon="Coming soon",
        req={"mac": "macOS 14 or later", "windows": "Windows 10 (1809) or later",
             "iphone": "iOS 17 or later", "android": "Android 8 or later"},
        box="<strong>14-day free trial (15 days on Windows), then a one-time purchase to keep using it. No subscription.</strong> "
            "No ads, no tracking, no account.",
        sections=[
            ("View", [
                "Three modes: <strong>Full Screen</strong>, <strong>Filmstrip</strong> (the photo and a vertical strip of thumbnails) and <strong>Contact Sheet</strong> (a grid of thumbnails).",
                "Arrow keys ← →, click, wheel or touchpad to move on. The space bar starts the automatic slideshow.",
                "On a phone: swipe to go from one photo to the next, pinch to zoom, double tap for full screen.",
                "Photos are shown the right way up, from their EXIF orientation.",
                "Diapo resumes at the last photo seen in each folder."]),
            ("Formats", ["JPEG, HEIC, PNG, TIFF, WebP, GIF, BMP and RAW (Canon CR2/CR3, Nikon NEF, Sony ARW, DNG…)."]),
            ("Favorites and selections", [
                "A heart, or the F key, adds a photo to your Favorites.",
                "Selections: while browsing your disks, mark photos with a click, then copy them into a folder to share them. Duplicates are skipped by their content."]),
            ("Your photos stay untouched", [
                "Diapo never modifies, moves, renames or deletes a photo. It only makes copies, when you ask for them."]),
        ],
        info="Information", privacy_label="Privacy policy", languages="Available in 28 languages.",
        publisher="Atria.Eponym, independent developer based in France",
    ),
}

# Every store is still reviewing the app (submitted 25/10/2026): no store link until its page answers.
STORES = [("mac", "Mac", "App Store"), ("windows", "Windows", "Microsoft Store"),
          ("iphone", "iPhone", "App Store"), ("android", "Android", "Google Play")]

REDIRECT = """<script>
(function(){
  // French page: a visitor whose browser does not ask for French first gets the English one; ?lang=fr stays.
  if (/[?&]lang=fr\\b/.test(location.search)) return;
  var l = (navigator.languages || [navigator.language || ''])[0] || '';
  if (l.toLowerCase().split('-')[0] !== 'fr') location.replace('en/');
})();
</script>"""


def page(lang: str) -> str:
    t = T[lang]
    k = "fr" if lang == "fr" else "en"
    img = lambda n: f"{t['up']}img/{n}"
    mac = "".join(f'<img src="{img(f"mac-{i}-{k}.jpg")}" alt="{html.escape(a)}" width="1600" height="1000" loading="lazy">'
                  for i, a in zip((1, 2, 3), t["alt_mac"]))
    phones = "".join(f'<img src="{img(n)}" alt="{html.escape(a)}" width="600" height="1304" loading="lazy">'
                     for n, a in zip((f"iphone-2-{k}.jpg", "iphone-4.jpg"), t["alt_phone"]))
    stores = "".join(f'<div class="platform" id="{pid}"><h2>{t["on"]} {name}</h2><span class="btn"><bdi>{store}</bdi>'
                     f'<small>{t["soon"]}</small></span><div class="meta">{t["req"][pid]}</div></div>'
                     for pid, name, store in STORES)
    sections = "".join(f"<h2>{h}</h2><ul>{''.join(f'<li>{x}</li>' for x in items)}</ul>" for h, items in t["sections"])
    base = "https://atriaeponym.com/diapo/"
    return f"""<!DOCTYPE html>
<html lang="{lang}" dir="ltr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="index">
<title>{html.escape(t['title'])}</title>
<meta name="description" content="{html.escape(t['desc'])}">
<link rel="canonical" href="{base}{'' if lang == 'fr' else 'en/'}">
<link rel="alternate" hreflang="fr" href="{base}">
<link rel="alternate" hreflang="en" href="{base}en/">
<link rel="alternate" hreflang="x-default" href="{base}en/">
<link rel="icon" href="/icons/diapo.png">
{REDIRECT if lang == 'fr' else ''}
<style>
{CSS}</style>
</head>
<body>
<div class="top"><a href="{t['other'][0]}" hreflang="{'en' if lang == 'fr' else 'fr'}">{t['other'][1]}</a></div>

<div class="hero"><img src="/icons/diapo.png" alt="" width="76" height="76">
<div><h1><bdi>Diapo</bdi></h1><div class="tag">{t['tag']}</div></div></div>

<p>{t['intro']}</p>

<div class="shots">{mac}</div>
<div class="phones">{phones}</div>

<div class="stores">{stores}</div>

<div class="box"><p>{t['box']}</p></div>

{sections}

<p>{t['languages']}</p>

<h2>{t['info']}</h2>
<ul>
  <li><a href="{t['privacy']}">{t['privacy_label']}</a></li>
  <li><a href="mailto:atria.eponym@gmail.com?subject=Diapo">atria.eponym@gmail.com</a></li>
</ul>

<footer><bdi>Diapo</bdi> — {t['publisher']} · <a href="mailto:atria.eponym@gmail.com">atria.eponym@gmail.com</a> · © 2026 Atria.Eponym</footer>
</body>
</html>
"""


for lang, out in (("fr", "diapo/index.html"), ("en", "diapo/en/index.html")):
    p = site / out
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(page(lang), encoding="utf-8")
    print(p)
