# paribu-cineverse-mcp 🇹🇷

Türkiye'nin en büyük sinema zinciri **Paribu Cineverse** (paribucineverse.com) için gayriresmî, **salt-okunur** MCP sunucusu — vizyondaki ve yakında gelecek filmler, film detayı, şehre göre sinemalar ve bugünün seansları.

> "Türkiye MCP fabrikası" parçasıdır. Paribu Cineverse ile bağlantısı yoktur.

## Yapay zekâ ajanları için

MCP istemcinize ekleyin (stdio):

```json
{
  "mcpServers": {
    "cineverse": {
      "command": "uvx",
      "args": ["paribu-cineverse-mcp==0.1.1"]
    }
  }
}
```

## Araçlar

| Araç | Açıklama |
|------|----------|
| `cineverse_list_now_showing` | Vizyondaki filmler (2026-11-07'de 33): ad, tür, vizyon tarihi, yönetmen, oyuncular, süre, afiş |
| `cineverse_list_coming_soon` | Yakında gelecek filmler (2026-11-07'de 26) |
| `cineverse_get_movie` | Tek filmin detayı — `film_url` (tam URL veya site yolu) |
| `cineverse_list_cinemas` | Tüm sinemalar (2026-11-07'de 77): şehir, adres, telefon; isteğe bağlı `city` filtresi |
| `cineverse_get_showtimes` | Bir sinemada bugünün seansları — `cinema_slug` ("14-burda", "akasya"…): film başına seans saatleri + format + bilet linki |

Notlar:
- Seanslar isteğin yapıldığı gün içindir; bilet linkleri sitenin kendi bilet akışına gider (buradan satın alma yapılmaz).
- `user_score_100`, izleyici "Golden Egg" puanıdır (0–100).
- Veri: sitenin sunucu taraflı sayfaları + schema.org JSON-LD — anahtar yok, giriş yok, salt-okunur.

## Kurallar

Gayriresmî ve salt-okunur — giriş yok, API anahtarı yok, yazma yok. Testler: çevrimdışı fixture + canlı testler (17/17 yeşil).

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
