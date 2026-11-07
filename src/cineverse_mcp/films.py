"""Domain logic: parse Paribu Cineverse server-rendered pages + JSON-LD (stdlib only).

The site's pages each carry one schema.org JSON-LD block:
- /vizyondakiler, /gelecek-filmler: WebPage with mainEntity ItemList of Movie
- /sinemalar: WebPage with mainEntity ItemList of MovieTheater
- film detail: WebPage with mainEntity Movie
- cinema detail: MovieTheater with mainEntity WebPage whose mainEntity is
  an ItemList of Movie; the visible page adds per-film user scores
  ("Golden Egg" 0-100) and showtime links (cinema-list-item anchors).
"""
from __future__ import annotations

import html
import json
import re

BASE = "https://www.paribucineverse.com"


def _ld_json(html_text: str) -> dict:
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html_text, re.S)
    if not m:
        raise ValueError("no JSON-LD block found on this Paribu Cineverse page")
    raw = html.unescape(m.group(1)).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Some pages (e.g. /sinemalar) emit trailing data after the first
        # JSON value — parse just the first complete value.
        try:
            value, _ = json.JSONDecoder().raw_decode(raw)
            return value
        except json.JSONDecodeError as e:
            raise ValueError(f"invalid JSON-LD on Paribu Cineverse page: {e}") from e


def _duration_min(iso: str | None) -> int | None:
    """ISO 8601 duration (PT107M, PT1H47M) -> minutes."""
    if not iso:
        return None
    m = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?", iso.strip())
    if not m:
        return None
    h, mins = m.groups()
    return (int(h) * 60 if h else 0) + (int(mins) if mins else 0)


def _names(people) -> list[str]:
    if not people:
        return []
    if isinstance(people, dict):
        people = [people]
    return [p.get("name") for p in people if isinstance(p, dict) and p.get("name")]


def _genre(g) -> str | None:
    if isinstance(g, list):
        g = ", ".join(str(x) for x in g if x)
        return g or None
    return g or None


def _norm_date(value: str | None) -> str | None:
    """Normalize datePublished: ISO stays, 'M/D/YYYY h:mm:ss AM' -> ISO."""
    if not value:
        return None
    value = value.strip()
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})(?:\s+\d{1,2}:\d{2}:\d{2}\s*[AP]M)?", value)
    if m:
        mo, d, y = m.groups()
        return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
    return value


def _movie(item: dict) -> dict:
    return {
        "name": item.get("name"),
        "genre": _genre(item.get("genre")),
        "url": item.get("url"),
        "slug": (item.get("url") or "").rstrip("/").rsplit("/", 1)[-1] or None,
        "release_date": _norm_date(item.get("datePublished")),
        "directors": _names(item.get("director")),
        "actors": _names(item.get("actor")),
        "duration_min": _duration_min(item.get("duration")),
        "poster_url": item.get("image"),
        "description": (item.get("description") or "")[:500],
    }


def parse_movie_list(html_text: str) -> dict:
    """Parse /vizyondakiler or /gelecek-filmler (ItemList of Movie)."""
    d = _ld_json(html_text)
    main = d.get("mainEntity") or {}
    items = main.get("itemListElement") or []
    movies = [_movie(it.get("item") or {}) for it in items if it.get("item")]
    return {"count": len(movies), "movies": movies}


def parse_film_detail(html_text: str) -> dict:
    """Parse a film detail page: Movie JSON-LD + HTML labels."""
    d = _ld_json(html_text)
    movie = d.get("mainEntity") or {}
    out = _movie(movie)
    out["description"] = (movie.get("description") or "")[:1000]
    # HTML labels the JSON-LD lacks: release date as shown, runtime text
    m = re.search(r"Vizyon Tarihi:</b>\s*<small>([^<]+)</small>", html_text)
    if m:
        out["release_date_text"] = html.unescape(m.group(1)).strip()
    m = re.search(r'data-movie-formatted-runtime="([^"]+)"', html_text)
    if m:
        out["runtime_text"] = html.unescape(m.group(1)).strip()
    m = re.search(r'data-movie-genre="([^"]+)"', html_text)
    if m and not out.get("genre"):
        out["genre"] = html.unescape(m.group(1)).strip()
    # NOTE: no user score here — the detail page shows several "Golden Egg"
    # scores (this film + similar films) and they cannot be told apart
    # reliably from the markup; per-film scores come from showtimes pages.
    return out


def parse_cinemas(html_text: str, city: str | None = None) -> dict:
    """Parse /sinemalar (ItemList of MovieTheater). city filters by
    addressLocality or name substring (case-insensitive)."""
    d = _ld_json(html_text)
    main = d.get("mainEntity") or {}
    items = main.get("itemListElement") or []
    cinemas = []
    for it in items:
        item = it.get("item") or {}
        addr = item.get("address") or {}
        cinemas.append(
            {
                "name": item.get("name"),
                "city": addr.get("addressLocality"),
                "address": addr.get("streetAddress"),
                "phone": item.get("telephone"),
                "url": item.get("url"),
                "slug": (item.get("url") or "").rstrip("/").rsplit("/", 1)[-1] or None,
            }
        )
    if city:
        want = city.strip().lower()
        cinemas = [
            c
            for c in cinemas
            if (c.get("city") or "").lower() == want
            or want in (c.get("name") or "").lower()
            or want in (c.get("address") or "").lower()
        ]
    return {"count": len(cinemas), "cinemas": cinemas}


def parse_showtimes(html_text: str) -> dict:
    """Parse a cinema detail page: cinema info + per-film showtimes today.

    Each film lives in a `movieRow` block (data-movie-title); inside it the
    `time-row-list` holds the session links (title="HH:MM", data-url =
    booking link). Sessions are deduplicated by booking URL (the page
    renders mobile + desktop copies).
    """
    d = _ld_json(html_text)
    addr = d.get("address") or {}
    # The cinema page's address has no addressLocality — the city is the
    # last comma-separated part of the street address ("..., 14100, Bolu").
    city = None
    street = addr.get("streetAddress") or ""
    parts = [p.strip() for p in street.split(",") if p.strip()]
    if parts:
        city = re.sub(r"^\d+\s*", "", parts[-1]).strip() or None
    films = []
    seen_movies = {}
    for it in (d.get("mainEntity") or {}).get("mainEntity", {}).get("itemListElement") or []:
        item = it.get("item") or {}
        seen_movies[item.get("name")] = _movie(item)
    segments = re.split(r'id="movieRow" data-movie-title="([^"]+)"', html_text)
    # segments: [pre, title1, body1, title2, body2, ...]
    for i in range(1, len(segments) - 1, 2):
        title = html.unescape(segments[i]).strip()
        body = segments[i + 1]
        score = None
        sm = re.search(r"egg-icon-cinema[^>]*>.*?<span>(\d+)</span>", body, re.S)
        if sm:
            score = int(sm.group(1))
        times: dict[str, dict] = {}
        for tm in re.finditer(
            r'class="cinema-list-item"[^>]*title="(\d{2}:\d{2})"[^>]*data-url="([^"]+)"',
            body,
        ):
            t, url = tm.groups()
            fmts = re.findall(r"cinema-detail-tech-text\">([^<]+)</span>", body[: tm.start()])
            times.setdefault(
                url,
                {"time": t, "format": (fmts[-1].strip() if fmts else None),
                 "booking_url": BASE + url},
            )
        entry = dict(seen_movies.get(title, {"name": title}))
        entry["user_score_100"] = score
        entry["showtimes"] = sorted(times.values(), key=lambda x: x["time"])
        films.append(entry)
    return {
        "cinema": d.get("name"),
        "address": addr.get("streetAddress"),
        "city": city,
        "phone": d.get("telephone"),
        "film_count": len(films),
        "films": films,
    }
