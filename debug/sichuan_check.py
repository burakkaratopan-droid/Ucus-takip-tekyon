"""Geçici teşhis: Sichuan neden sonuçlarda yok? Google'a konum (gl) vermeden ve gl=TR ile sorar."""
import json, sys
from pathlib import Path
from primp import Client
from fast_flights import FlightQuery, Passengers, create_query
from selectolax.lexbor import LexborHTMLParser

sys.path.insert(0, str(Path(__file__).parent.parent))
from tracker import parse

q = create_query(flights=[FlightQuery(date="2027-02-26", from_airport="IST", to_airport="NRT")],
                 trip="one-way", seat="economy", passengers=Passengers(adults=1),
                 language="tr", currency="TRY", max_stops=1)
out = {}
for label, extra in (("varsayilan", {}), ("gl_TR", {"gl": "TR"})):
    client = Client(impersonate="chrome_145", impersonate_os="macos", referer=True, cookie_store=True)
    html = client.get("https://www.google.com/travel/flights", params={**q.params(), **extra}).text
    res = {"html_sichuan": html.count("Sichuan"), "html_3U": html.count('"3U"')}
    try:
        opts = parse(html)
        res["parsed"] = [{"price": o["price"], "airlines": o["airlines"], "minutes": o["minutes"],
                          "legs": len(o["legs"])} for o in opts]
    except Exception as e:
        res["parse_error"] = str(e)
    # Sichuan satırlarını ham haliyle yakala (hangi blokta, fiyat alanı nasıl)
    node = LexborHTMLParser(html).css_first(r"script.ds\:1")
    if node:
        raw = node.text().split("data:", 1)[1].rsplit(",", 1)[0]
        try:
            payload = json.loads(raw)
            rows = []
            for bi, block in enumerate(payload if isinstance(payload, list) else []):
                s = json.dumps(block, ensure_ascii=False)
                if "Sichuan" in s:
                    rows.append({"block": bi, "len": len(s)})
                    try:
                        for r in block[0]:
                            if "Sichuan" in json.dumps(r, ensure_ascii=False):
                                f = r[0]
                                rows.append({"block": bi, "airlines": f[1], "price_field": r[1],
                                             "minutes_field": f[9] if len(f) > 9 else None,
                                             "legs": len(f[2])})
                    except Exception as e:
                        rows.append({"block": bi, "row_error": str(e)})
            res["sichuan_rows"] = rows
        except Exception as e:
            res["payload_error"] = str(e)
    out[label] = res
Path(__file__).with_name("sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=1)[:4000])
