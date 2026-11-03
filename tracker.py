"""İstanbul (IST/SAW) <-> Japonya (HND/NRT/KIX) tek yön bilet takipçisi.

Gidiş ve dönüşü ayrı tek yön biletler olarak tarar: her tarih ve her havalimanı
çifti için Google Flights'tan en fazla 1 aktarmalı, toplam süresi sınırı aşmayan
seçenekleri çeker. Her yön için en ucuz seçenekleri docs/data.json'a yazar;
panel (docs/index.html) bu dosyayı okur.
"""

import json
import random
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from fast_flights import FlightQuery, Passengers, create_query, fetch_flights_html
from selectolax.lexbor import LexborHTMLParser

ROOT = Path(__file__).parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
DATA_FILE = ROOT / "docs" / "data.json"
MAX_MINUTES = CONFIG["max_hours"] * 60
KEEP_PER_ROUTE = 5  # her rota/tarih için saklanan seçenek sayısı


def days(span):
    d, end = date.fromisoformat(span["from"]), date.fromisoformat(span["to"])
    while d <= end:
        yield d
        d += timedelta(days=1)


def searches():
    """(yön, kalkış, varış, tarih) dörtlüleri. Geçmiş tarihler atlanır."""
    today = date.today()
    tr = [a["code"] for a in CONFIG["turkey"]]
    jp = [a["code"] for a in CONFIG["japan"]]
    for d in days(CONFIG["outbound"]):
        if d > today:
            for o in tr:
                for t in jp:
                    yield "out", o, t, d
    for d in days(CONFIG["return"]):
        if d > today:
            for o in jp:
                for t in tr:
                    yield "ret", o, t, d


def parse(html):
    """Google Flights sayfasından seçenekleri çıkarır (ucus-takip reposundaki ayrıştırıcının aynısı)."""
    node = LexborHTMLParser(html).css_first(r"script.ds\:1")
    if node is None:
        raise RuntimeError("Google Flights beklenen veriyi döndürmedi (engellenmiş olabilir)")
    js = node.text()
    raw = js.split("data:", 1)[1].rsplit(",", 1)[0]
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
            flight = row[0]
            legs = []
            for s in flight[2]:
                dep_t = (s[8] or []) + [None, None]
                arr_t = (s[10] or []) + [None, None]
                legs.append({
                    "from": s[3],
                    "to": s[6],
                    "dep": f"{dep_t[0] or 0:02d}:{dep_t[1] or 0:02d}",
                    "arr": f"{arr_t[0] or 0:02d}:{arr_t[1] or 0:02d}",
                    "arr_date": "-".join(f"{x:02d}" for x in s[21]) if s[21] else None,
                    "minutes": s[11],
                })
            options.append({
                "price": int(price),
                "airlines": flight[1],
                "legs": legs,
                "minutes": flight[9] if len(flight) > 9 and isinstance(flight[9], int) else None,
            })
    options.sort(key=lambda x: x["price"])
    return options


def fetch(frm, to, d, attempts=3):
    q = create_query(
        flights=[FlightQuery(date=d.isoformat(), from_airport=frm, to_airport=to)],
        trip="one-way",
        seat="economy",
        passengers=Passengers(adults=CONFIG["adults"]),
        language="tr",
        currency=CONFIG["currency"],
        max_stops=CONFIG["max_stops"],
    )
    err = None
    for i in range(attempts):
        try:
            options = parse(fetch_flights_html(q))
            # Google ara sıra boş sonuç döndürüyor; birkaç kez daha dene.
            if options or i == attempts - 1:
                return options, q.url()
        except Exception as e:  # ağ hatası, engelleme, değişen sayfa yapısı
            err = e
        time.sleep(5 * (i + 1) + random.random() * 3)
    raise err


def fits(o):
    """En fazla 1 aktarma ve toplam süre (aktarma beklemesi dahil) sınırın altında. Süre bilinmiyorsa eler."""
    return (len(o["legs"]) <= CONFIG["max_stops"] + 1
            and o.get("minutes") is not None and o["minutes"] <= MAX_MINUTES)


def compact(o):
    return {
        "price": o["price"],
        "airlines": o["airlines"],
        "via": [leg["to"] for leg in o["legs"][:-1]],
        "legs": o["legs"],
        "minutes": o["minutes"],
    }


def tl(n):
    return f"{n:,}".replace(",", ".") + " TL"


def hours(m):
    return f"{m // 60} sa {m % 60:02d} dk"


def main():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else {}
    data.setdefault("runs", [])
    data.setdefault("routes", {})
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data["runs"].append(now)
    run_idx = len(data["runs"]) - 1
    todo = list(searches())
    ok = failed = 0

    for n, (direction, frm, to, d) in enumerate(todo, 1):
        key = f"{direction}_{frm}_{to}_{d.isoformat()}"
        try:
            opts, url = fetch(frm, to, d)
        except Exception as e:
            failed += 1
            print(f"[{n}/{len(todo)}] {key} HATA: {e}", file=sys.stderr)
            continue
        time.sleep(1 + random.random() * 2)

        good = [compact(o) for o in opts if fits(o)][:KEEP_PER_ROUTE]
        entry = data["routes"].setdefault(key, {
            "dir": direction, "from": frm, "to": to, "date": d.isoformat(), "history": [],
        })
        # Google bazen boş döndürüyor: o zaman son bilinen sonucu koru, "eski" diye işaretle.
        if good:
            entry["options"] = good
            entry["stale"] = False
        elif not opts and entry.get("options"):
            entry["stale"] = True
        else:
            entry["options"] = []  # sonuç var ama hiçbiri filtreye uymuyor
            entry["stale"] = False
        best = entry["options"][0]["price"] if entry.get("options") else None
        if not entry["history"] or entry["history"][-1][1] != best:
            entry["history"].append([run_idx, best])
        entry["checked"] = run_idx
        entry["url"] = url
        ok += 1
        print(f"[{n}/{len(todo)}] {key} en ucuz={best}" + (" (eski)" if entry["stale"] else ""))

    # Her yön için en ucuz N seçenek (bu taramada kontrol edilen rotalardan)
    top = {}
    for direction in ("out", "ret"):
        pool = []
        for key, e in data["routes"].items():
            if e["dir"] != direction or e.get("checked") != run_idx:
                continue
            for o in e.get("options", []):
                pool.append({**o, "key": key, "from": e["from"], "to": e["to"], "date": e["date"],
                             "url": e["url"], "stale": e.get("stale", False)})
        pool.sort(key=lambda o: o["price"])
        top[direction] = pool[:CONFIG["top_n"]]

    data["top"] = top
    data["updated"] = now
    data["config"] = CONFIG
    data["last_run"] = {"at": now, "ok": ok, "failed": failed, "total": len(todo)}
    DATA_FILE.parent.mkdir(exist_ok=True)
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    for direction, label in (("out", "GİDİŞ"), ("ret", "DÖNÜŞ")):
        print(f"\n{label} — en ucuz {CONFIG['top_n']}:")
        for o in top[direction]:
            print(f"  {tl(o['price'])}  {o['date']}  {o['from']}→{o['to']}  {', '.join(o['airlines'])}"
                  f"  {'aktarmasız' if not o['via'] else o['via'][0] + ' aktarmalı'}  {hours(o['minutes'])}")
    print(f"\nBitti: {ok} başarılı, {failed} hatalı / {len(todo)}")
    # Hepsi başarısızsa iş akışı kırmızı görünsün.
    sys.exit(1 if ok == 0 and todo else 0)


if __name__ == "__main__":
    main()
