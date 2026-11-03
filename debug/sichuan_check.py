"""Geçici teşhis 2: Sichuan gerçek tarayıcıda (sayfa tam yüklendiğinde) görünüyor mu?"""
import json, re, sys
from pathlib import Path
from fast_flights import FlightQuery, Passengers, create_query
from playwright.sync_api import sync_playwright

q = create_query(flights=[FlightQuery(date="2027-02-26", from_airport="IST", to_airport="NRT")],
                 trip="one-way", seat="economy", passengers=Passengers(adults=1),
                 language="tr", currency="TRY", max_stops=1)
out = {}
with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(locale="tr-TR", viewport={"width": 1280, "height": 2000})
    page.goto(q.url(), wait_until="domcontentloaded", timeout=45000)
    page.wait_for_function("() => [...document.querySelectorAll('li')].some(li => li.innerText.includes('₺'))", timeout=30000)
    page.wait_for_timeout(4000)
    out["before_more"] = [t for t in page.locator("li").all_inner_texts() if "₺" in t]
    more = page.get_by_role("button", name=re.compile("Daha fazla uçuş"))
    if more.count():
        more.first.click()
        page.wait_for_timeout(3000)
    out["after_more"] = [t for t in page.locator("li").all_inner_texts() if "₺" in t]
    b.close()
out["sichuan_before"] = sum("Sichuan" in t for t in out["before_more"])
out["sichuan_after"] = sum("Sichuan" in t for t in out["after_more"])
Path(__file__).with_name("sonuc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(out["sichuan_before"], out["sichuan_after"], len(out["after_more"]))
