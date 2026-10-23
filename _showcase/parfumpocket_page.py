"""Builds atriaeponym.com/parfumpocket/ (fr) and /en/ from one template. Usage: python3 _showcase/parfumpocket_page.py ."""
import sys, pathlib
site = pathlib.Path(sys.argv[1])
CSS = (site / "parfumpocket/terms/index.html").read_text().split("<style>")[1].split("</style>")[0]
CSS += """.hero{display:flex;gap:16px;align-items:center;margin-bottom:10px}
.hero img{width:72px;height:72px;border-radius:18px}
.stores{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0 6px}
.stores .btn{margin:0}
@media (prefers-color-scheme:dark){.btn{color:#0B0F19}}
html,body{overflow-x:hidden}
.soon{display:inline-block;border:1px solid var(--line);background:var(--card);color:var(--muted);
      font-weight:600;padding:12px 18px;border-radius:14px;font-size:15px}
.soon b{color:var(--ink)}
.shots{display:flex;gap:12px;overflow-x:auto;margin:18px 0 6px;padding-bottom:6px}
.shots img{width:200px;height:auto;flex:0 0 auto;border-radius:16px;border:1px solid var(--line)}
"""
T = {
 "fr": dict(lang="fr", up="", title="Perfume Price Tracker — comparateur de prix parfum",
  sub="Comparateur de prix parfum : prix livré, prix au ml, alerte quand il baisse.",
  intro="<bdi>Perfume Price Tracker</bdi> suit le prix de tes parfums dans plusieurs boutiques en ligne et te dit où les acheter au meilleur prix, <strong>livraison comprise</strong>.",
  play="Télécharger sur Google Play", ios="Télécharger sur l'App Store", hl="",
  box="<strong>Gratuit, sans publicité, sans compte.</strong> Tes alertes et ta collection restent sur ton téléphone.",
  sections=[("Le bon prix, au bon endroit",[
    "Chaque offre est comparée au prix total livré : prix + livraison la moins chère à domicile.",
    "Prix au millilitre et disponibilité de chaque boutique.",
    "Chaque prix indique sa boutique, sa taille exacte et l'heure du relevé ; un prix trop ancien est grisé, jamais présenté comme actuel.",
    "Uniquement les prix publics : ni code promo, ni prix réservé aux membres."]),
   ("L'évolution des prix",[
    "Une courbe par boutique, sur 30 jours, 90 jours ou depuis le début.",
    "Le prix le plus bas de chaque période ; les jours sans relevé restent visibles."]),
   ("Tes alertes",[
    "Prix maximum, baisse minimale en %, nouveau prix le plus bas jamais relevé.",
    "Ton téléphone vérifie chaque matin, après le relevé des prix, et te prévient une seule fois par offre."]),
   ("Tes boutiques",[
    "Suivies aujourd'hui : MyOrigines, Sabina et Parfumdo.",
    "Colle le lien d'une page de parfum : l'application vérifie tout de suite qu'elle peut être suivie, ou te dit pourquoi.",
    "Les boutiques sont des tiers : elles ne dépendent pas d'Atria.Eponym. Une boutique qui refuse la lecture automatique n'est jamais contournée."])],
  info="Informations", privacy="Politique de confidentialité", other="English", other_href="en/",
  langs="Disponible en 28 langues.", alt="Capture d'écran"),
 "en": dict(lang="en", up="../", title="Perfume Price Tracker — compare perfume prices",
  sub="Compare perfume and fragrance prices across shops: price per ml, drop alerts.",
  intro="<bdi>Perfume Price Tracker</bdi> follows the price of your perfumes in several online shops and tells you where to buy them at the best price, <strong>delivery included</strong>.",
  play="Get it on Google Play", ios="Download on the App Store", hl="&hl=en",
  box="<strong>Free, no ads, no account.</strong> Your alerts and your collection stay on your phone.",
  sections=[("The right price, in the right place",[
    "Every offer is compared on its total delivered price: price + cheapest home delivery.",
    "Price per millilitre and availability in each shop.",
    "Every price shows its shop, its exact size and when it was read; an old price is greyed out, never shown as current.",
    "Public prices only: no promo codes, no members-only prices."]),
   ("How prices move",[
    "One line per shop, over 30 days, 90 days or since the start.",
    "The lowest price of each period; days without a reading stay visible."]),
   ("Your alerts",[
    "Maximum price, minimum drop in %, new lowest price ever read.",
    "Your phone checks every morning, after the prices are read, and tells you once per offer."]),
   ("Your shops",[
    "Followed today: MyOrigines, Sabina and Parfumdo.",
    "Paste the link of a perfume page: the app checks at once whether it can be followed, or tells you why.",
    "Shops are third parties: they do not depend on Atria.Eponym. A shop that refuses automatic reading is never worked around."])],
  info="Information", privacy="Privacy policy", other="Français", other_href="../",
  langs="Available in 28 languages.", alt="Screenshot"),
}
for key, t in T.items():
    secs = "\n".join(f"<h2>{h}</h2>\n<ul>\n" + "\n".join(f"  <li>{i}</li>" for i in items) + "\n</ul>" for h, items in t["sections"])
    shots = "\n".join(f'  <img src="{t["up"]}img/{key}-{n}.jpg" alt="{t["alt"]} {n}" width="540" height="1173" loading="lazy">' for n in (1, 2, 3))
    priv = "privacy/" if key == "fr" else "../privacy/en/"
    html = f"""<!DOCTYPE html>
<html lang="{t['lang']}" dir="ltr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="index">
<title>{t['title']}</title>
<meta name="description" content="{t['sub']}">
<link rel="alternate" hreflang="fr" href="https://atriaeponym.com/parfumpocket/">
<link rel="alternate" hreflang="en" href="https://atriaeponym.com/parfumpocket/en/">
<style>{CSS}</style>
</head>
<body>
<div class="sub"><a href="{t['other_href']}">{t['other']}</a></div>
<div class="hero"><img src="{t['up']}../icons/parfumpocket.png" alt="" width="72" height="72">
<div><h1><bdi>Perfume Price Tracker</bdi></h1><div class="sub" style="margin:0">{t['sub']}</div></div></div>

<p>{t['intro']}</p>

<div class="stores"><a class="btn" href="https://play.google.com/store/apps/details?id=com.atriaeponym.parfumpocket{t['hl']}">{t['play']}</a><a class="btn" href="https://apps.apple.com/app/id6824535728">{t['ios']}</a></div>

<div class="shots">
{shots}
</div>

<div class="box"><p>{t['box']}</p></div>

{secs}

<p>{t['langs']}</p>

<h2>{t['info']}</h2>
<ul>
  <li><a href="{priv}">{t['privacy']}</a></li>
  <li><a href="mailto:atria.eponym@gmail.com">atria.eponym@gmail.com</a></li>
</ul>

<footer>Perfume Price Tracker — Atria.Eponym · France · <a href="mailto:atria.eponym@gmail.com">atria.eponym@gmail.com</a></footer>
</body>
</html>
"""
    out = site / "parfumpocket" / ("index.html" if key == "fr" else "en/index.html")
    out.write_text(html)
    print(out, len(html))
