# paribu-cineverse-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/paribu-cineverse-mcp

Unofficial **read-only** MCP server for **Paribu Cineverse** (paribucineverse.com), Türkiye's largest cinema chain — now-showing and coming-soon films, film detail, cinemas by city and today's showtimes.

> Part of the "Turkey MCP factory". Not affiliated with Paribu Cineverse.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "cineverse": {
      "command": "uvx",
      "args": ["paribu-cineverse-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m cineverse_mcp.server` (needs `mcp<2`, `curl-cffi`).

## Tools

| Tool | Description |
|------|-------------|
| `cineverse_list_now_showing` | Films now showing (33 on 2026-11-07): title, genre, release date, directors, cast, runtime, poster |
| `cineverse_list_coming_soon` | Films coming soon (26 on 2026-11-07) |
| `cineverse_get_movie` | Detail for one film — `film_url` (full URL or site path) |
| `cineverse_list_cinemas` | All cinemas (77 on 2026-11-07) with city, address, phone; optional `city` filter |
| `cineverse_get_showtimes` | Today's showtimes at one cinema — `cinema_slug` (e.g. "14-burda", "akasya"): per film, session times + format + booking link |

Example output (`cineverse_get_showtimes` / "14-burda"):

```json
{"cinema": "Paribu Cineverse 14 Bolu Burda", "city": "Bolu", "film_count": 11,
 "films": [{"name": "Çakallarla Dans 8: Şututgart Çıkarması", "genre": "Komedi",
 "duration_min": 107, "user_score_100": 61,
 "showtimes": [{"time": "13:45", "format": "2D",
 "booking_url": "https://www.paribucineverse.com/biletleme/..."}]}]}
```

Notes:
- Showtimes are for today at the time of the request; booking links point at the site's own ticket flow (no purchase is made here).
- `user_score_100` is the audience "Golden Egg" score (0–100).
- Data: the site's server-rendered pages + schema.org JSON-LD — no key, no login, read-only.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" curl-cffi pytest
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_films.py` — offline, parses real captured pages
- `tests/test_live.py` — 4 cautious live requests against paribucineverse.com

## License

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
