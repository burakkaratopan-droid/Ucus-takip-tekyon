"""Geçici: Sichuan sitesinin yapısını ve arka plan isteklerini incele."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

out = {"requests": [], "links": []}
with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(locale="en-US", viewport={"width": 1280, "height": 1600})
    def on_resp(r):
        if r.request.resource_type in ("xhr", "fetch", "document"):
            try:
                body = r.text()[:800]
            except Exception:
                body = ""
            out["requests"].append({"url": r.url[:300], "method": r.request.method, "status": r.status,
                                    "post": (r.request.post_data or "")[:800], "body": body})
    page.on("response", on_resp)
    page.goto("https://global.sichuanair.com/", wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)
    out["title"] = page.title()
    out["final_url"] = page.url
    out["text"] = page.inner_text("body")[:3000]
    out["links"] = list({a for a in page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")})[:150]
    out["inputs"] = page.eval_on_selector_all("input,select,button", "els => els.map(e => [e.tagName, e.type||'', e.name||'', e.id||'', e.placeholder||'', (e.innerText||'').slice(0,40)])")[:80]
    page.screenshot(path=str(Path(__file__).with_name("shot.png")), full_page=False)
    b.close()
Path(__file__).with_name("capture.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(out["title"], out["final_url"], len(out["requests"]))
