"""MCP server: unofficial read-only access to Paribu Cineverse cinemas (paribucineverse.com)."""
from __future__ import annotations

import json
import sys

from mcp.server.fastmcp import FastMCP

from . import films as _f
from . import http as _http

mcp = FastMCP("paribu-cineverse-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for Paribu Cineverse (paribucineverse.com), \
Türkiye's largest cinema chain — now-showing and coming-soon films, film \
detail, cinemas by city and today's showtimes per cinema, from the site's \
server-rendered pages and schema.org JSON-LD. No login, no API key, \
read-only. Showtimes are for today at the time of the request; booking \
links point at the site's own ticket flow (no purchase is made here). \
``user_score_100`` is the audience "Golden Egg" score (0-100). Built by \
Mohammad Abbasi (github.com/mohammad-abbasi-sh/paribu-cineverse-mcp).\
Built by Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir
"""


def _err(e: Exception) -> str:
    return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def cineverse_list_now_showing() -> str:
    """Films now showing at Paribu Cineverse (33 on 2026-11-07): title, genre, \
release date, directors, cast, runtime, poster, film URL."""
    try:
        return json.dumps(_f.parse_movie_list(_http.fetch_now_showing()), ensure_ascii=False)
    except (_http.CineverseError, ValueError) as e:
        return _err(e)


@mcp.tool()
def cineverse_list_coming_soon() -> str:
    """Films coming soon to Paribu Cineverse (26 on 2026-11-07): title, genre, \
release date, directors, cast, runtime, poster, film URL."""
    try:
        return json.dumps(_f.parse_movie_list(_http.fetch_coming_soon()), ensure_ascii=False)
    except (_http.CineverseError, ValueError) as e:
        return _err(e)


@mcp.tool()
def cineverse_get_movie(film_url: str) -> str:
    """Detail for one film. film_url: full film URL or site path, e.g. \
/komedi-filmleri/cakallarla-dans-8-sututgart-cikarmasi-filmi-izle."""
    try:
        return json.dumps(_f.parse_film_detail(_http.fetch_film(film_url)), ensure_ascii=False)
    except (_http.CineverseError, ValueError) as e:
        return _err(e)


@mcp.tool()
def cineverse_list_cinemas(city: str = "") -> str:
    """All Paribu Cineverse cinemas (77 on 2026-11-07) with city, address and \
phone. city: optional filter, e.g. "Bolu", "İstanbul", "Ankara"."""
    try:
        return json.dumps(
            _f.parse_cinemas(_http.fetch_cinemas(), city or None), ensure_ascii=False
        )
    except (_http.CineverseError, ValueError) as e:
        return _err(e)


@mcp.tool()
def cineverse_get_showtimes(cinema_slug: str) -> str:
    """Today's showtimes at one cinema: per film, session times + format + \
booking link. cinema_slug: e.g. "14-burda", "akasya" (from list_cinemas)."""
    try:
        return json.dumps(_f.parse_showtimes(_http.fetch_cinema(cinema_slug)), ensure_ascii=False)
    except (_http.CineverseError, ValueError) as e:
        return _err(e)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
