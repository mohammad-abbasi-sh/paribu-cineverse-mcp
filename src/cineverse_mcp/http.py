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


_PROFILES = ("chrome120", "chrome131", "safari17_0")
_MAX_ATTEMPTS = 2  # one retry with the next profile
_RETRY_BACKOFF = 1.0  # seconds between attempts
_profile_idx = 0  # sticky: profile that last succeeded


def _request(url: str, headers: dict, timeout: float = TIMEOUT):
    """GET with fingerprint rotation.

    Starts at the sticky profile (chrome120 on a fresh process), retries
    once with the next profile on HTTP 403/429 or a transport error, then
    returns the last response (so the caller raises the specific 403/429
    error) or raises a network error if every attempt failed at the
    transport. Added 2026-11-10 (fleet audit fix).
    """
    global _profile_idx
    last_exc: Exception | None = None
    for k in range(_MAX_ATTEMPTS):
        profile = _PROFILES[(_profile_idx + k) % len(_PROFILES)]
        try:
            resp = _r.get(url, impersonate=profile, headers=headers, timeout=timeout)
        except Exception as e:
            last_exc = e
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            raise CineverseError(f"network error fetching {url}: {e}") from e
        if resp.status_code in (403, 429):
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            return resp
        _profile_idx = (_profile_idx + k) % len(_PROFILES)
        return resp
    raise CineverseError(f"network error fetching {url}: {last_exc}") from last_exc


def _get(path: str) -> str:
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    url = path if path.startswith("http") else f"{BASE}{path}"
    try:
        resp = _request(url, _HEADERS)
    except CineverseError:
        raise
    except Exception as e:
        raise CineverseError(f"network error fetching {url}: {e}") from e
    finally:
        _last_fetch = time.monotonic()
    if resp.status_code == 403:
        raise CineverseError(
            "paribucineverse.com refused the request (HTTP 403, bot wall) — try again later"
        )
    if resp.status_code == 429:
        raise CineverseError(
            "paribucineverse.com rate-limited the request (HTTP 429) — try again later"
        )
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


def fetch_home_html() -> str:
    """Homepage HTML (used by health_check)."""
    return _get(f"{BASE}/")


def health_check() -> dict:
    """One polite probe of the source site.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `cineverse_health` tool
    and the daily smoke CI. Added 2026-11-10 (fleet audit fix).
    """
    url = "https://www.paribucineverse.com/"
    try:
        fetch_home_html()
    except CineverseError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
