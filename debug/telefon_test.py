"""Tek sorgu testi: 26 Şubat IST→NRT tam sonuç isteği. Sichuan'ın fiyatı geliyor mu?"""
import json, urllib.parse, urllib.request

EP = ("https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights."
      "FlightsFrontendService/GetShoppingResults?hl=tr&soc-app=162&soc-platform=1&soc-device=1&rt=c")
inner = json.dumps([[], [None, None, 2, None, [], 1, [1, 0, 0, 0], None, None, None, None, None, None,
                         [[[[["IST", 0]]], [[["NRT", 0]]], None, 2, None, None, "2027-02-26",
                           None, None, None, None, None, None, None, 3]],
                         None, None, None, 1], 0, 1, 0, 1], separators=(",", ":"))
body = "f.req=" + urllib.parse.quote(json.dumps([None, inner], separators=(",", ":"))) + "&"
req = urllib.request.Request(EP, data=body.encode(), headers={
    "content-type": "application/x-www-form-urlencoded;charset=utf-8", "x-same-domain": "1",
    "x-goog-ext-259736195-jspb": '["tr","TR","TRY",2,null,[0],null,null,7,[]]',
    "User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"})
t = urllib.request.urlopen(req, timeout=40).read().decode("utf-8", "replace")

found = {}
for ln in t.split("\n"):
    ln = ln.strip()
    if not ln.startswith("[["):
        continue
    for it in json.loads(ln):
        if it[0] != "wrb.fr" or not it[2]:
            continue
        p = json.loads(it[2])
        for bk in (2, 3):
            for r in ((p[bk] or [None])[0] or []) if len(p) > bk else []:
                f = r[0]
                try:
                    price = r[1][0][1]
                except (IndexError, TypeError):
                    price = None
                key = (tuple(f[1]), f[2][0][8] and tuple(f[2][0][8]), f[9])
                if price or key not in found:
                    found[key] = price
rows = sorted(found.items(), key=lambda kv: (kv[1] is None, kv[1] or 0))
print(f"{len(rows)} uçuş bulundu\n")
for (air, dep, mins), price in rows[:8]:
    print(f"{price if price else 'fiyat yok':>8}  {', '.join(air)}  {dep[0]:02d}:{dep[1]:02d}  {mins // 60} sa {mins % 60:02d} dk")
s = [(k, v) for k, v in found.items() if any("Sichuan" in a for a in k[0])]
print("\nSICHUAN:", s[0][1] if s and s[0][1] else ("listede var ama fiyat yok" if s else "listede yok"))
