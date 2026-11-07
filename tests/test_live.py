"""Live tests — hit the real paribucineverse.com. Cautious: 4 requests, then stop.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set CINEVERSE_SKIP_LIVE=1)
"""
import os
import pathlib
import sys
import time
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from cineverse_mcp import films as _f
from cineverse_mcp import http as _http

pytestmark = pytest.mark.live
SKIP = os.environ.get("CINEVERSE_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="CINEVERSE_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_now_showing_is_real(self):
        parsed = _f.parse_movie_list(_http.fetch_now_showing())
        self.assertGreaterEqual(parsed["count"], 20)
        names = [m["name"] for m in parsed["movies"]]
        self.assertIn("Çakallarla Dans 8: Şututgart Çıkarması", names)
        print(f"\nLIVE now showing: {parsed['count']} films")
        time.sleep(1)

    def test_cinemas_are_real(self):
        parsed = _f.parse_cinemas(_http.fetch_cinemas())
        self.assertGreaterEqual(parsed["count"], 70)
        bolu = _f.parse_cinemas(_http.fetch_cinemas(), "Bolu")
        self.assertGreaterEqual(bolu["count"], 1)
        print(f"\nLIVE cinemas: {parsed['count']} total, Bolu: {bolu['count']}")
        time.sleep(1)

    def test_showtimes_are_real(self):
        parsed = _f.parse_showtimes(_http.fetch_cinema("14-burda"))
        self.assertEqual(parsed["cinema"], "Paribu Cineverse 14 Bolu Burda")
        self.assertGreater(parsed["film_count"], 5)
        first = parsed["films"][0]
        self.assertGreater(len(first["showtimes"]), 0)
        print(f"\nLIVE 14 Bolu Burda: {parsed['film_count']} films, first "
              f"{first['name']} at {[s['time'] for s in first['showtimes']]}")
        time.sleep(1)

    def test_film_detail_is_real(self):
        d = _f.parse_film_detail(
            _http.fetch_film(
                "/komedi-filmleri/cakallarla-dans-8-sututgart-cikarmasi-filmi-izle"
            )
        )
        self.assertEqual(d["name"], "Çakallarla Dans 8: Şututgart Çıkarması")
        self.assertEqual(d["directors"], ["Murat Şeker"])
