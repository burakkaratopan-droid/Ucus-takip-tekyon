"""Geçici: Sichuan sitesinde 26 Şub IST→Tokyo tek yön aramasını tarayıcıyla yap; Amadeus'a giden isteği yakala."""
import json, re, traceback
from pathlib import Path
from playwright.sync_api import sync_playwright

D = Path(__file__).parent
out = {"steps": [], "posts": [], "xhr": []}
def step(s): out["steps"].append(s); print(s, flush=True)
with sync_playwright() as pw:
    b = pw.chromium.launch()
    ctx = b.new_context(locale="en-US", viewport={"width": 1280, "height": 1800})
    page = ctx.new_page()
    def on_req(r):
        if "e-travel.com" in r.url and r.method == "POST":
            out["posts"].append({"url": r.url, "post": (r.post_data or "")[:4000]})
    def on_resp(r):
        if "e-travel.com" in r.url and r.request.resource_type in ("xhr", "fetch", "document"):
            try: body = r.text()
            except Exception: body = ""
            out["xhr"].append({"url": r.url[:250], "method": r.request.method, "status": r.status, "len": len(body),
                               "post": (r.request.post_data or "")[:1500], "body": body[:3000],
                               "sichuan_price": bool(re.search(r"(TRY|EUR|USD|CNY)", body))})
    ctx.on("request", on_req); ctx.on("response", on_resp)
    try:
        page.goto("https://global.sichuanair.com/app/home", wait_until="networkidle", timeout=60000)
        for t in ("Reject", "Accept"):
            btn = page.get_by_role("button", name=t)
            if btn.count(): btn.first.click(); break
        page.get_by_role("button", name="One Way").first.click(); step("one way")
        dep = page.get_by_placeholder("Departure city"); dep.click(); dep.fill("Istanbul"); page.wait_for_timeout(2500)
        page.screenshot(path=str(D / "s1.png"))
        page.get_by_text("IstanbulAirport").first.click(); page.wait_for_timeout(800); step("from ok: " + dep.input_value())
        arr = page.get_by_placeholder("Arrival city"); arr.click(); arr.fill("Tokyo"); page.wait_for_timeout(2500)
        page.screenshot(path=str(D / "s2.png"))
        page.get_by_text("Tokyo Narita International Airport").first.click(); page.wait_for_timeout(800); step("to ok: " + arr.input_value())
        page.get_by_role("button", name=re.compile(r"^\w{3} \d{2} \w{3} \d{4}")).first.click(); page.wait_for_timeout(1500)
        out["cal_html"] = page.locator("[role=dialog], [data-reka-popper-content-wrapper]").first.inner_html()[:6000] if page.locator("[role=dialog], [data-reka-popper-content-wrapper]").count() else page.content()[-6000:]
        page.screenshot(path=str(D / "s3.png"))
        dlg = page.locator("[data-slot=popover-content][data-state=open]").first
        for _ in range(8):
            head = dlg.locator("div.grid").first.inner_text()
            if "Feb" in head and "2027" in head:
                break
            dlg.locator("div.grid").first.locator("button").nth(4).click(); page.wait_for_timeout(400)
        step("month ok: " + dlg.locator("div.grid").first.inner_text().replace("\n", " "))
        dlg.get_by_role("button", name="26", exact=True).first.click()
        step("date ok"); page.wait_for_timeout(800)
        page.screenshot(path=str(D / "s4.png"))
        for t in ("Confirm", "Done", "OK", "Apply"):
            btn = page.get_by_role("button", name=t)
            if btn.count() and btn.first.is_visible(): btn.first.click(); break
        step("depart: " + page.get_by_role("button", name=re.compile(r"^\w{3} \d{2} \w{3} \d{4}")).first.inner_text())
        page.get_by_role("button", name="Search").first.click(); page.wait_for_timeout(2000)
        conf = page.get_by_role("button", name="Confirm")
        try:
            with ctx.expect_page(timeout=20000) as newp:
                if conf.count() and conf.first.is_visible():
                    conf.first.click()
            res = newp.value; step("new tab")
        except Exception:
            res = page; step("same tab")
    except Exception as e:
        out["error"] = traceback.format_exc()[-1500:]
        res = page
        try:
            page.get_by_role("button", name="Search").first.click(); step("search clicked (same tab)")
        except Exception:
            pass
    try:
        res.wait_for_timeout(25000)
        out["result_url"] = res.url
        out["result_text"] = res.inner_text("body")[:6000]
        res.screenshot(path=str(D / "s5.png"), full_page=True)
    except Exception as e:
        out["result_error"] = str(e)
    b.close()
(D / "capture.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
