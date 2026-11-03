"""Geçici: tarayıcının sonradan gönderdiği istekleri yakala (26 Şub IST→NRT tek yön)."""
import json, re
from pathlib import Path
from fast_flights import FlightQuery, Passengers, create_query
from playwright.sync_api import sync_playwright

q = create_query(flights=[FlightQuery(date="2027-02-26", from_airport="IST", to_airport="NRT")],
                 trip="one-way", seat="economy", passengers=Passengers(adults=1),
                 language="tr", currency="TRY", max_stops=1)
reqs = []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(locale="tr-TR", viewport={"width": 1280, "height": 2000})

    def on_resp(r):
        u = r.url
        if "google.com" in u and ("/_/" in u or "batchexecute" in u or "data/" in u):
            try:
                body = r.text()
            except Exception:
                body = ""
            reqs.append({"url": u, "method": r.request.method,
                         "post": (r.request.post_data or "")[:6000],
                         "headers": {k: v for k, v in r.request.headers.items()
                                     if k.lower().startswith("x-") or k.lower() in ("content-type",)},
                         "status": r.status, "len": len(body),
                         "has_thai": "THAI" in body, "has_sichuan": "Sichuan" in body,
                         "body_head": body[:1500]})
    page.on("response", on_resp)
    page.goto(q.url(), wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(12000)
    more = page.get_by_role("button", name=re.compile("Daha fazla uçuş"))
    if more.count():
        more.first.click(); page.wait_for_timeout(5000)
    b.close()
Path(__file__).with_name("capture.json").write_text(json.dumps(reqs, ensure_ascii=False, indent=1), encoding="utf-8")
for r in reqs:
    print(r["method"], r["status"], r["len"], r["has_thai"], r["has_sichuan"], r["url"][:160])
