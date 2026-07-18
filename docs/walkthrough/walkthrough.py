"""Story 4.7 DoD browser walkthrough: real Chromium against the live app.

Desktop (1440x900) + phone (360x740): upload the real sheet photo + info.xml,
tap Process, watch the strip, read the results; Lookup + Investigate for 001.
Screenshots land in docs/walkthrough/ for the report; horizontal-scroll checks
run at 360px on every page (DoD: no core-flow horizontal scroll).
"""

import sys
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = "http://localhost:8615"
ROOT = Path(r"C:\dev\CGV Group Assignment")
SHOTS = ROOT / "docs" / "walkthrough"
SHOTS.mkdir(parents=True, exist_ok=True)
SHEET = ROOT / "sample_signin-sheets" / "1.jpeg"
XML = ROOT / "sample_signin-sheets" / "1.xml"

results = []


def check(name, condition, detail=""):
    results.append((name, bool(condition), detail))
    print(f"{'PASS' if condition else 'FAIL'}  {name}  {detail}")


def no_hscroll(page, label):
    sw = page.evaluate("document.documentElement.scrollWidth")
    iw = page.evaluate("window.innerWidth")
    check(f"no horizontal scroll — {label}", sw <= iw + 1, f"scrollWidth={sw} innerWidth={iw}")


def process_flow(page, shot_prefix):
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector("h1:has-text('Mark today')", timeout=30000)
    page.screenshot(path=str(SHOTS / f"{shot_prefix}-1-landing.png"), full_page=True)

    inputs = page.locator("input[type='file']")
    expect(inputs).to_have_count(2, timeout=15000)
    inputs.nth(0).set_input_files(str(SHEET))
    page.wait_for_selector("text=✓ Ready", timeout=20000)
    inputs.nth(1).set_input_files(str(XML))
    page.wait_for_timeout(2500)  # second Ready + eager parse rerun
    page.screenshot(path=str(SHOTS / f"{shot_prefix}-2-ready.png"), full_page=True)

    process = page.get_by_role("button", name="Process")
    expect(process).to_be_enabled(timeout=15000)
    process.click()
    # The stage strip is the loading state; the run takes ~20-40s server-side.
    page.wait_for_selector("text=All finished", timeout=180000)
    page.wait_for_selector("text=Results saved.", timeout=30000)
    page.screenshot(path=str(SHOTS / f"{shot_prefix}-3-results.png"), full_page=True)
    body = page.locator("body").inner_text()
    check(f"{shot_prefix}: results summary shown", "students checked." in body)
    check(f"{shot_prefix}: saved stated once", body.count("Results saved.") == 1)
    check(f"{shot_prefix}: chips carry icon+label", ("✓ Present" in body) or ("✕ Absent" in body))


def nav_url(page, text):
    """Discover the real st.navigation URL for a page from the sidebar links."""
    links = page.locator("[data-testid='stSidebarNav'] a")
    for i in range(links.count()):
        if text.lower() in (links.nth(i).inner_text() or "").lower():
            return links.nth(i).get_attribute("href")
    return None


def lookup_flow(page, shot_prefix):
    url = nav_url(page, "Look up") or f"{BASE}/Lookup"
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector("h1:has-text('Look up a student')", timeout=30000)
    box = page.get_by_label("Student number")
    box.fill("001")
    box.press("Enter")
    page.wait_for_selector("[data-testid='stImage'] img", timeout=60000)  # the timeline chart
    page.wait_for_timeout(2000)
    page.screenshot(path=str(SHOTS / f"{shot_prefix}-4-lookup.png"), full_page=True)
    check(f"{shot_prefix}: lookup renders without error tone",
          "Something went wrong" not in page.locator("body").inner_text())


def investigate_flow(page, shot_prefix):
    url = nav_url(page, "Check a signature") or f"{BASE}/Investigate"
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector("h1:has-text('Check a signature')", timeout=30000)
    box = page.get_by_label("Student number")
    box.fill("001")
    box.press("Enter")
    page.wait_for_selector("text=/Match|Mismatch|don't have/", timeout=90000)
    page.wait_for_timeout(1500)
    page.screenshot(path=str(SHOTS / f"{shot_prefix}-5-investigate.png"), full_page=True)
    body = page.locator("body").inner_text()
    check(f"{shot_prefix}: verdict sentence shown", ("Match" in body) or ("Mismatch" in body))


with sync_playwright() as p:
    browser = p.chromium.launch()

    # --- Desktop pass (1440x900) ---------------------------------------------
    desktop = browser.new_context(viewport={"width": 1440, "height": 900})
    dpage = desktop.new_page()
    process_flow(dpage, "desktop")
    lookup_flow(dpage, "desktop")
    investigate_flow(dpage, "desktop")
    desktop.close()

    # --- Phone pass (360x740, touch) ------------------------------------------
    phone = browser.new_context(
        viewport={"width": 360, "height": 740},
        is_mobile=True,
        has_touch=True,
        device_scale_factor=2,
    )
    ppage = phone.new_page()
    process_flow(ppage, "phone")
    no_hscroll(ppage, "phone Process results")
    lookup_flow(ppage, "phone")
    no_hscroll(ppage, "phone Lookup")
    investigate_flow(ppage, "phone")
    no_hscroll(ppage, "phone Investigate")

    # Touch-target floor: measure the Process page buttons on phone.
    ppage.goto(BASE, wait_until="networkidle")
    ppage.wait_for_selector("h1:has-text('Mark today')", timeout=30000)
    heights = ppage.eval_on_selector_all(
        "button", "els => els.filter(e => e.offsetParent).map(e => e.getBoundingClientRect().height)"
    )
    visible = [h for h in heights if h > 0]
    check("phone: visible buttons >= 44px", visible and min(visible) >= 44, f"min={min(visible) if visible else 'n/a'}")
    phone.close()

    browser.close()

failed = [r for r in results if not r[1]]
print(f"\n{'='*60}\n{len(results) - len(failed)}/{len(results)} checks passed; screenshots in {SHOTS}")
sys.exit(1 if failed else 0)
