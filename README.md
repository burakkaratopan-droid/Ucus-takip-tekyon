# İstanbul ⇄ Japonya tek yön uçuş takipçisi

Gidiş ve dönüşü **ayrı tek yön biletler** olarak tarar, Google Flights'tan günde üç kez (TR saatiyle 07:00, 12:00, 19:00) çeker.

- **Gidiş:** 26 Şubat – 6 Mart 2027, IST veya SAW → Tokyo Haneda (HND), Tokyo Narita (NRT) veya Osaka Kansai (KIX)
- **Dönüş:** 13 – 17 Mart 2027, HND/NRT/KIX → IST veya SAW
- Filtre: en fazla 1 aktarma, toplam yolculuk süresi (aktarma beklemesi dahil) en fazla 20 saat
- Her yön için en ucuz 3 seçenek + gün gün en ucuz fiyat tablosu
- Google boş sonuç döndürürse son bilinen fiyat "eski" etiketiyle gösterilir
- Fiyatlar tek yetişkin, ekonomi, tek yön, TL

Ramazan gidiş-dönüş takibi [ucus-takip](https://github.com/burakkaratopan-droid/ucus-takip), Kurban takibi [ucus-takip-kurban](https://github.com/burakkaratopan-droid/ucus-takip-kurban) reposunda.

## Dosyalar

| Dosya | Ne işe yarar |
|---|---|
| `config.json` | Havalimanları, tarih aralıkları, aktarma ve süre sınırı, kaç seçenek gösterileceği |
| `tracker.py` | Taramayı yapar, sonuçları `docs/data.json`'a yazar |
| `docs/index.html` | Panel (GitHub Pages) |
| `.github/workflows/track.yml` | Günde 3 kez otomatik çalıştırır |

## Ayar değiştirmek

`config.json` dosyasını GitHub üzerinde düzenleyip kaydetmen yeterli; bir sonraki taramada geçerli olur. Tarihleri `outbound` / `return`, süre sınırını `max_hours`, gösterilen seçenek sayısını `top_n` değiştirir.

## Elle tarama başlatmak

GitHub'da **Actions → Fiyat taraması → Run workflow**.

## Yerelde çalıştırmak

```bash
pip install -r requirements.txt
python tracker.py
```
