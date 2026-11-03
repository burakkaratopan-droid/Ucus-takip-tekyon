"""Geçici 2: GetShoppingResults isteğini tarayıcısız gönder; Sichuan geliyor mu?"""
import json, urllib.parse, urllib.request
from pathlib import Path
from primp import Client

EP = ("https://www.google.com/_/FlightsFrontendUi/data/travel.frontend.flights."
      "FlightsFrontendService/GetShoppingResults?hl=tr&soc-app=162&soc-platform=1&soc-device=1&rt=c")
inner = json.dumps([[], [None, None, 2, None, [], 1, [1, 0, 0, 0], None, None, None, None, None, None,
                         [[[[["IST", 0]]], [[["NRT", 0]]], None, 2, None, None, "2027-02-26",
                           None, None, None, None, None, None, None, 3]],
                         None, None, None, 1], 0, 1, 0, 1], separators=(",", ":"))
body = "f.req=" + urllib.parse.quote(json.dumps([None, inner], separators=(",", ":"))) + "&"
hdr = {"content-type": "application/x-www-form-urlencoded;charset=utf-8", "x-same-domain": "1",
       "x-goog-ext-259736195-jspb": '["tr","TR","TRY",2,null,[0],null,null,7,[]]'}
out = {}
# 1) primp (Chrome taklidi)
try:
    c = Client(impersonate="chrome_145", impersonate_os="macos", referer=True, cookie_store=True)
    r = c.post(EP, content=body.encode(), headers=hdr)
    t = r.text
    out["primp"] = {"status": r.status_code, "len": len(t), "sichuan": "Sichuan" in t, "thai": "THAI" in t}
    Path(__file__).with_name("primp_body.txt").write_text(t, encoding="utf-8")
except Exception as e:
    out["primp"] = {"error": str(e)}
# 2) düz urllib (telefondaki gibi)
try:
    req = urllib.request.Request(EP, data=body.encode(), headers={**hdr, "User-Agent":
          "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"})
    with urllib.request.urlopen(req, timeout=40) as r:
        t = r.read().decode("utf-8", "replace")
    out["urllib"] = {"status": 200, "len": len(t), "sichuan": "Sichuan" in t, "thai": "THAI" in t}
    Path(__file__).with_name("urllib_body.txt").write_text(t, encoding="utf-8")
except Exception as e:
    out["urllib"] = {"error": str(e)}
Path(__file__).with_name("capture.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(out)
