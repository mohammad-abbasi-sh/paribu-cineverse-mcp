"""HTTP layer for cineverse_mcp.

Paribu Cineverse (paribucineverse.com), Türkiye's largest cinema chain,
serves its listing pages fully server-rendered with schema.org JSON-LD —
no login, no API key, no session cookies. Verified live 2026-11-07:
homepage, /vizyondakiler (now showing), /gelecek-filmler (coming soon),
/sinemalar (cinemas) and film/cinema detail pages all return 200 with a
plain browser UA (curl-cffi chrome120). Requests are kept gentle (one at
a time, ~0.8s apart) and read-only.
"""
from __future__ import annotations

import time

from curl_cffi import requests as _r

BASE = "https://www.paribucineverse.com"
TIMEOUT = 30.0
MIN_INTERVAL = 0.8  # seconds between requests — be polite

_HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

_last_fetch = 0.0


class CineverseError(RuntimeError):
    pass


def _get(path: str) -> str:
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    url = path if path.startswith("http") else f"{BASE}{path}"
    try:
        resp = _r.get(url, impersonate="chrome120", headers=_HEADERS, timeout=TIMEOUT)
    except Exception as e:
        raise CineverseError(f"network error fetching {url}: {e}") from e
    finally:
        _last_fetch = time.monotonic()
    if resp.status_code == 404:
        raise CineverseError(f"Paribu Cineverse returned HTTP 404 for {url}")
    if resp.status_code != 200:
        raise CineverseError(f"Paribu Cineverse returned HTTP {resp.status_code} for {url}")
    return resp.text


def fetch_now_showing() -> str:
    return _get("/vizyondakiler")


def fetch_coming_soon() -> str:
    return _get("/gelecek-filmler")


def fetch_cinemas() -> str:
    return _get("/sinemalar")


def fetch_film(path_or_url: str) -> str:
    """Film detail page. Accepts a full URL or a site path
    (/komedi-filmleri/...-filmi-izle)."""
    if path_or_url.startswith("http"):
        return _get(path_or_url)
    if not path_or_url.startswith("/"):
        path_or_url = "/" + path_or_url
    return _get(path_or_url)


def fetch_cinema(slug: str) -> str:
    """Cinema detail page + today's showtimes. slug: e.g. '14-burda' or 'akasya'."""
    slug = slug.strip().strip("/")
    if slug.startswith("sinemalar/"):
        slug = slug[len("sinemalar/"):]
    return _get(f"/sinemalar/{slug}")
