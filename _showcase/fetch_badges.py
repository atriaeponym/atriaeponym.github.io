"""Download the official store badges (Apple, Google, Microsoft) for every language of the site.

    python3 _showcase/fetch_badges.py     # writes badges/<lang>/{appstore.svg,play.png,msstore.svg}

The badges are used as published: the only change is trimming the transparent margin around the Google
PNG. A language a store does not translate gets its English badge (listed at the end of the run).
"""
import io
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent

# site language -> (Apple, Google, Microsoft) locale codes
CODES = {
    "en": ("en-us", "en", "en-us"), "fr": ("fr-fr", "fr", "fr"), "de": ("de-de", "de", "de"),
    "es": ("es-es", "es", "es"), "it": ("it-it", "it", "it"), "pt": ("pt-pt", "pt", "pt-pt"),
    "pt-br": ("pt-br", "pt-br", "pt-br"), "nl": ("nl-nl", "nl", "nl"), "sv": ("sv-se", "sv", "sv"),
    "nb": ("no-no", "no", "nb"), "fi": ("fi-fi", "fi", "fi"), "pl": ("pl-pl", "pl", "pl"),
    "ru": ("ru-ru", "ru", "ru"), "uk": ("uk-ua", "ua", "uk"), "el": ("el-gr", "el", "el"),
    "tr": ("tr-tr", "tr", "tr"), "ar": ("ar-sa", "ar", "ar"), "fa": ("fa-ir", "fa", "fa"),
    "he": ("he-il", "iw", "he"), "ur": ("ur-pk", "ur", "ur"), "hi": ("hi-in", "hi", "hi"),
    "bn": ("bn-bd", "bn", "bn"), "th": ("th-th", "th", "th"), "vi": ("vi-vn", "vi", "vi"),
    "id": ("id-id", "id", "id"), "ja": ("ja-jp", "ja", "ja"), "ko": ("ko-kr", "ko", "ko"),
    "zh": ("zh-cn", "zh-cn", "zh-cn"),
}
URL = {
    "appstore.svg": "https://toolbox.marketingtools.apple.com/api/v2/badges/download-on-the-app-store/black/{}",
    "play.png": "https://play.google.com/intl/en_us/badges/static/images/badges/{}_badge_web_generic.png",
    "msstore.svg": "https://get.microsoft.com/images/{}%20dark.svg",
}


def get(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
            data = r.read()
            kind = r.headers.get("Content-Type", "")
    except OSError:
        return None
    return data if kind.startswith("image/") else None


def trim(png: bytes) -> bytes:
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    box = im.split()[3].point(lambda v: 255 if v > 10 else 0).getbbox()
    out = io.BytesIO()
    im.crop(box).save(out, "PNG", optimize=True)
    return out.getvalue()


def main() -> None:
    english = {f: get(URL[f].format(CODES["en"][i])) for i, f in enumerate(URL)}
    assert all(english.values()), "English badges unavailable"
    fallback = []
    for lang, codes in CODES.items():
        folder = ROOT / "badges" / lang
        folder.mkdir(parents=True, exist_ok=True)
        for i, f in enumerate(URL):
            data = get(URL[f].format(codes[i]))
            if data is None or (lang != "en" and data == english[f]):
                data = english[f]
                if lang != "en":
                    fallback.append(f"{lang}/{f}")
            (folder / f).write_bytes(trim(data) if f.endswith(".png") else data)
    print(f"{len(CODES)} languages; English badge used for: {', '.join(fallback) or 'none'}")


if __name__ == "__main__":
    main()
