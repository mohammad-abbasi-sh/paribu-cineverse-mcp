"""Offline tests — parse real captured Paribu Cineverse pages, no network."""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from cineverse_mcp import films

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


class TestNowShowing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parsed = films.parse_movie_list(
            (FIX / "now_showing.html").read_text(encoding="utf-8")
        )

    def test_count(self):
        self.assertEqual(self.parsed["count"], 33)

    def test_first_movie(self):
        m = self.parsed["movies"][0]
        self.assertEqual(m["name"], "Çakallarla Dans 8: Şututgart Çıkarması")
        self.assertEqual(m["genre"], "Komedi")
        self.assertEqual(m["release_date"], "2026-11-06")
        self.assertEqual(m["directors"], ["Murat Şeker"])
        self.assertIn("Şevket Çoruh", m["actors"])
        self.assertEqual(m["duration_min"], 107)
        self.assertTrue(m["url"].endswith("-filmi-izle"))
        self.assertTrue((m["poster_url"] or "").startswith("https://"))
        self.assertTrue(len(m["description"]) > 50)

    def test_durations_parse(self):
        by_name = {m["name"]: m for m in self.parsed["movies"]}
        self.assertEqual(by_name["Şapkalı Kedi"]["duration_min"], 108)
        self.assertEqual(by_name["Araknofobi: Kabus"]["duration_min"], 81)

    def test_bad_html(self):
        with self.assertRaises(ValueError):
            films.parse_movie_list("<html><body>no json-ld here</body></html>")


class TestComingSoon(unittest.TestCase):
    def test_count_and_first(self):
        parsed = films.parse_movie_list(
            (FIX / "coming_soon.html").read_text(encoding="utf-8")
        )
        self.assertEqual(parsed["count"], 26)
        names = [m["name"] for m in parsed["movies"]]
        self.assertIn("Avengers: Doomsday", names)
        self.assertIn("Dune: Çöl Gezegeni Bölüm Üç", names)


class TestFilmDetail(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = films.parse_film_detail(
            (FIX / "film_detail.html").read_text(encoding="utf-8")
        )

    def test_detail(self):
        self.assertEqual(self.d["name"], "Çakallarla Dans 8: Şututgart Çıkarması")
        self.assertEqual(self.d["genre"], "Komedi")
        self.assertEqual(self.d["directors"], ["Murat Şeker"])
        self.assertEqual(self.d["duration_min"], 107)
        self.assertEqual(self.d["runtime_text"], "1 sa 47 dk")
        self.assertEqual(self.d["release_date_text"], "06.11.2026")
        self.assertIn("Şevket Çoruh", self.d["actors"])


class TestCinemas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (FIX / "cinemas.html").read_text(encoding="utf-8")

    def test_all_cinemas(self):
        parsed = films.parse_cinemas(self.html)
        self.assertEqual(parsed["count"], 77)
        first = parsed["cinemas"][0]
        self.assertEqual(first["name"], "Paribu Cineverse 14 Bolu Burda")
        self.assertEqual(first["city"], "Bolu")
        self.assertEqual(first["slug"], "14-burda")
        self.assertTrue(first["url"].endswith("/sinemalar/14-burda"))

    def test_city_filter(self):
        parsed = films.parse_cinemas(self.html, "Bolu")
        self.assertGreaterEqual(parsed["count"], 1)
        self.assertTrue(all(c["city"] == "Bolu" for c in parsed["cinemas"]))

    def test_unknown_city(self):
        self.assertEqual(films.parse_cinemas(self.html, "Nowhere")[ "count"], 0)


class TestShowtimes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parsed = films.parse_showtimes(
            (FIX / "cinema_detail.html").read_text(encoding="utf-8")
        )

    def test_cinema_info(self):
        self.assertEqual(self.parsed["cinema"], "Paribu Cineverse 14 Bolu Burda")
        self.assertEqual(self.parsed["city"], "Bolu")
        self.assertEqual(self.parsed["phone"], "03742741429")
        self.assertIn("14 BURDA", self.parsed["address"])

    def test_film_count(self):
        self.assertEqual(self.parsed["film_count"], 11)

    def test_first_film_showtimes(self):
        f = self.parsed["films"][0]
        self.assertEqual(f["name"], "Çakallarla Dans 8: Şututgart Çıkarması")
        self.assertEqual(f["duration_min"], 107)
        self.assertEqual(f["user_score_100"], 61)
        times = [s["time"] for s in f["showtimes"]]
        self.assertEqual(times, ["13:45", "16:10", "18:35", "21:00"])
        self.assertEqual(f["showtimes"][0]["format"], "2D")
        self.assertTrue(
            f["showtimes"][0]["booking_url"].startswith(
                "https://www.paribucineverse.com/biletleme/"
            )
        )

    def test_no_duplicate_sessions(self):
        for f in self.parsed["films"]:
            urls = [s["booking_url"] for s in f["showtimes"]]
            self.assertEqual(len(urls), len(set(urls)))


if __name__ == "__main__":
    unittest.main()
