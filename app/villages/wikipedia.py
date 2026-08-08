"""Fetch and cache village facts/photos from Wikipedia.

Called server-side only -- visitors never talk to Wikipedia directly, they
just see the cached result rendered on the village's own amigoans.co.uk page.
"""

import os
import re
import uuid
from io import BytesIO

import requests
from PIL import Image

WIKI_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "AmiGoansBot/1.0 (https://amigoans.co.uk; amigoans2026@gmail.com)"

# Goa's approximate bounding box, used to reject same-named places elsewhere
# in the world (e.g. a "Canca" in France) that would otherwise look like a
# text match.
GOA_LAT_RANGE = (14.85, 15.85)
GOA_LON_RANGE = (73.60, 74.40)

HISTORY_SECTION_NAMES = {"history", "history and etymology", "etymology and history"}

MAX_SUMMARY_CHARS = 1500
MAX_HISTORY_CHARS = 6000
IMAGE_MAX_DIMENSION = 1200


def clean_name(village_name):
    """Strip parenthetical suffixes like '(Ct)' from a village name."""
    return re.sub(r"\s*\([^)]*\)\s*", "", village_name).strip()


def _candidate_titles(village_name):
    clean = clean_name(village_name)
    candidates = []
    for title in (clean, f"{clean}, Goa", f"{clean} (village)"):
        if title not in candidates:
            candidates.append(title)
    return candidates


def _within_goa(coordinates):
    if not coordinates:
        return False
    lat = coordinates[0].get("lat")
    lon = coordinates[0].get("lon")
    if lat is None or lon is None:
        return False
    lat_ok = GOA_LAT_RANGE[0] <= lat <= GOA_LAT_RANGE[1]
    lon_ok = GOA_LON_RANGE[0] <= lon <= GOA_LON_RANGE[1]
    return lat_ok and lon_ok


def _split_sections(extract):
    """Split a wiki-section-formatted plain-text extract into (intro, sections)."""
    parts = re.split(r"\n==\s*([^=\n]+?)\s*==\n", extract)
    intro = parts[0].strip()
    sections = {}
    for i in range(1, len(parts) - 1, 2):
        sections[parts[i].strip().lower()] = parts[i + 1].strip()
    return intro, sections


def _truncate(text, limit):
    if not text or len(text) <= limit:
        return text or None
    cut = text.rfind(". ", 0, limit)
    if cut == -1:
        cut = limit
    return text[: cut + 1].strip()


def _fetch_page(title):
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "extracts|pageimages|coordinates|info|pageprops",
        "explaintext": 1,
        "exsectionformat": "wiki",
        "piprop": "name|thumbnail",
        "pithumbsize": IMAGE_MAX_DIMENSION,
        "inprop": "url",
        "ppprop": "disambiguation",
        "redirects": 1,
        "titles": title,
    }
    resp = requests.get(WIKI_API, params=params, headers={"User-Agent": USER_AGENT}, timeout=15)
    resp.raise_for_status()
    pages = resp.json().get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        return None
    page = pages[0]
    if "disambiguation" in page.get("pageprops", {}):
        return None
    return page


def _query_imageinfo(api_url, filename):
    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "prop": "imageinfo",
        "iiprop": "extmetadata",
        "titles": f"File:{filename}",
    }
    resp = requests.get(api_url, params=params, headers={"User-Agent": USER_AGENT}, timeout=15)
    resp.raise_for_status()
    pages = resp.json().get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing"):
        return None
    imageinfo = pages[0].get("imageinfo")
    return imageinfo[0].get("extmetadata", {}) if imageinfo else None


def _fetch_image_attribution(filename):
    """Look up licence/credit for a file, checking Commons then local Wikipedia.

    Most infobox photos live on Wikimedia Commons, but some are uploaded
    directly to English Wikipedia and never mirrored -- Commons reports those
    as missing, so we fall back to asking Wikipedia's own API about the file.
    """
    if not filename:
        return None, None

    meta = _query_imageinfo(COMMONS_API, filename)
    source_url = f"https://commons.wikimedia.org/wiki/File:{filename.replace(' ', '_')}"
    if meta is None:
        meta = _query_imageinfo(WIKI_API, filename)
        source_url = f"https://en.wikipedia.org/wiki/File:{filename.replace(' ', '_')}"
    if meta is None:
        return None, None

    artist = re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")).strip()
    license_name = meta.get("LicenseShortName", {}).get("value", "").strip()
    credit_bits = [b for b in (artist, license_name) if b]
    if not credit_bits:
        return None, None
    return " — ".join(credit_bits), source_url


def _download_image(thumbnail_url, slug):
    resp = requests.get(thumbnail_url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    image = Image.open(BytesIO(resp.content)).convert("RGB")
    width, height = image.size
    if max(width, height) > IMAGE_MAX_DIMENSION:
        scale = IMAGE_MAX_DIMENSION / max(width, height)
        image = image.resize((int(width * scale), int(height * scale)), Image.LANCZOS)

    filename = f"{slug}-{uuid.uuid4().hex[:8]}.jpg"
    return image, filename


def fetch_village_wikipedia(
    village_name, taluka=None, require_taluka_match=False, images_dir=None, slug=None
):
    """Look up a village on Wikipedia and return cached-field data, or None.

    Only returns a result when confident the matched article is actually
    about this Goan village (coordinates inside Goa, or an explicit mention
    of Goa near the top of the article) -- never attaches a same-named place
    from elsewhere. When ``require_taluka_match`` is set (several villages in
    Goa share the same name across different talukas, e.g. three "Navelim"s),
    the taluka name must also appear in the article text, otherwise the
    match is rejected rather than risk attaching the wrong village's info.
    """
    for title in _candidate_titles(village_name):
        page = _fetch_page(title)
        if page is None:
            continue

        extract = page.get("extract", "")
        if not extract:
            continue

        confirmed_goa = _within_goa(page.get("coordinates"))
        if not confirmed_goa and "goa" not in extract[:600].lower():
            continue

        if require_taluka_match and taluka and taluka.lower() not in extract.lower():
            continue

        intro, sections = _split_sections(extract)
        history = None
        for name in HISTORY_SECTION_NAMES:
            if name in sections:
                history = sections[name]
                break

        result = {
            "wiki_summary": _truncate(intro, MAX_SUMMARY_CHARS),
            "wiki_history": _truncate(history, MAX_HISTORY_CHARS),
            "wiki_url": page.get("fullurl"),
            "wiki_image": None,
            "wiki_image_attribution": None,
            "wiki_image_source_url": None,
        }

        thumbnail = page.get("thumbnail")
        if thumbnail and images_dir and slug:
            try:
                attribution, source_url = _fetch_image_attribution(page.get("pageimage"))
                # Never show a photo we can't credit -- required by its licence.
                if attribution:
                    image, filename = _download_image(thumbnail["source"], slug)
                    os.makedirs(images_dir, exist_ok=True)
                    image.save(os.path.join(images_dir, filename), "JPEG", quality=88)
                    result["wiki_image"] = filename
                    result["wiki_image_attribution"] = attribution
                    result["wiki_image_source_url"] = source_url
            except (requests.RequestException, OSError):
                pass

        return result

    return None
