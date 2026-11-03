"""Telefondan (Termux) tek yön tarama: aramayı senin Türkiye IP'nle yapar.

Kurulum gerektirmez, sadece Python yeter (ek kütüphane yok).
Arama linklerini GitHub'daki panelin veri dosyasından alır, her birini
Google Flights'ta açar ve her yön için en ucuz seçenekleri listeler.

Çalıştırma:  python telefon.py
"""

import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

DATA_URL = "https://raw.githubusercontent.com/burakkaratopan-droid/Ucus-takip-tekyon/main/docs/data.json"
UA = ("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0.0.0 Mobile Safari/537.36")
WORKERS = 2
DS1 = re.compile(r'<script[^>]*class="ds:1"[^>]*>(.*?)</script>', re.S)


def get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def parse(html):
    """Google Flights sayfasından seçenekleri çıkarır (tracker.py'deki ayrıştırıcının ek kütüphanesiz hali)."""
    m = DS1.search(html)
    if not m:
        raise RuntimeError("Google beklenen veriyi döndürmedi")
    raw = m.group(1).split("data:", 1)[1].rsplit(",", 1)[0]
    if raw.endswith("errorHasStatus: true"):
        return []
    payload = json.loads(raw)
    options = []
    for block in (2, 3):
        rows = payload[block][0] if len(payload) > block and payload[block] else None
        for row in rows or []:
            try:
                price = row[1][0][1]
            except (IndexError, TypeError):
                continue
            if not price:
                continue
            f = row[0]
            options.append({
                "price": int(price),
                "airlines": f[1],
                "via": [s[6] for s in f[2][:-1]],
                "dep": "{:02d}:{:02d}".format(*(((f[2][0][8] or []) + [0, 0])[:2])),
                "minutes": f[9] if len(f) > 9 and isinstance(f[9], int) else None,
            })
    options.sort(key=lambda x: x["price"])
    return options


def search_url(url):
    # Panel linki /travel/flights/search?tfs=... biçiminde; sunucu tarafı veriyi bu adres döndürüyor.
    return url.replace("/travel/flights/search?", "/travel/flights?")


def scan(route, max_stops, max_minutes):
    for i in range(4):
        try:
            opts = parse(get(search_url(route["url"])))
            if opts or i == 3:
                return route, [o for o in opts
                               if len(o["via"]) <= max_stops and o["minutes"] and o["minutes"] <= max_minutes]
        except Exception as e:
            if i == 3:
                return route, e
        time.sleep(4 * (i + 1))


def tl(n):
    return f"{n:,}".replace(",", ".") + " TL"


def main():
    local = len(sys.argv) > 1 and sys.argv[1] == "--yerel"
    data = (json.load(open("docs/data.json", encoding="utf-8")) if local
            else json.loads(get(DATA_URL)))
    cfg = data["config"]
    max_minutes = cfg["max_hours"] * 60
    routes = [r for r in data["routes"].values() if r.get("url")]
    print(f"{len(routes)} arama yapılacak (aynı anda {WORKERS}), birkaç dakika sürer…\n")

    pool = {"out": [], "ret": []}
    failed = done = 0
    with ThreadPoolExecutor(WORKERS) as ex:
        for route, res in ex.map(lambda r: scan(r, cfg["max_stops"], max_minutes), routes):
            done += 1
            if isinstance(res, Exception):
                failed += 1
            else:
                for o in res:
                    pool[route["dir"]].append({**o, "date": route["date"], "from": route["from"],
                                               "to": route["to"]})
            print(f"\r{done}/{len(routes)} tamamlandı" + (f" ({failed} hatalı)" if failed else ""), end="", flush=True)
    print("\n")

    n = cfg.get("top_n", 3)
    for d, label in (("out", "GİDİŞ"), ("ret", "DÖNÜŞ")):
        print(f"== {label} · en ucuz {n} ==")
        best = sorted(pool[d], key=lambda o: o["price"])[:n]
        if not best:
            print("  Filtreye uyan seçenek yok.")
        for i, o in enumerate(best, 1):
            via = "aktarmasız" if not o["via"] else f"{o['via'][0]} aktarmalı"
            print(f"{i}. {tl(o['price'])}  {o['date']}  {o['from']}→{o['to']}  {o['dep']}")
            print(f"   {', '.join(o['airlines'])} · {via} · {o['minutes'] // 60} sa {o['minutes'] % 60:02d} dk")
        print()
    if failed:
        print(f"Not: {failed} arama başarısız oldu, sonuçlar eksik olabilir.")


if __name__ == "__main__":
    main()
