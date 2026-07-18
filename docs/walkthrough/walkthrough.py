"""Browser walkthrough for the report: real Chromium against the live app
(five-page shell, SAMS design).

Desktop (1440x900) + phone (360x740): the Dashboard landing, the Process flow
(upload the real sheet photo + info.xml, tap Process, watch the strip, read
the results), Session history, Lookup + Investigate for 001. Screenshots land
in docs/walkthrough/ for the report; horizontal-scroll checks run at 360px on
every page (DoD: no core-flow horizontal scroll).

Run with the app up first:  streamlit run webui/app.py  (from the project root)
"""

import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = "http://localhost:8501"
ROOT = Path(__file__).resolve().parent.parent.parent
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


def nav_url(page, text):
    """Discover the real st.navigation URL for a page from the sidebar links."""
    links = page.locator("[data-testid='stSidebarNav'] a")
    for i in range(links.count()):
        if text.lower() in (links.nth(i).inner_text() or "").lower():
            return links.nth(i).get_attribute("href")
    return None


def dashboard_flow(page, shot_prefix):
    page.goto(BASE, wait_until="networkidle")
    page.wait_for_selector("h1:has-text('Dashboard')", timeout=30000)
    page.wait_for_selector("text=students on roster", timeout=30000)
    page.wait_for_timeout(1500)  # signature alerts settle
    page.screenshot(path=str(SHOTS / f"{shot_prefix}-1-dashboard.png"), full_page=True)
    body = page.locator("body").inner_text()
    check(f"{shot_prefix}: dashboard tiles shown", "average attendance" in body)
    check(f"{shot_prefix}: quick actions shown", "QUICK ACTIONS" in body)


def process_flow(page, shot_prefix):
    url = nav_url(page, "Mark today") or f"{BASE}/Process"
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector("h1:has-text('Mark today')", timeout=30000)

    inputs = page.locator("input[type='file']")
    expect(inputs).to_have_count(2, timeout=15000)
    inputs.nth(0).set_input_files(str(SHEET))
    page.wait_for_selector("text=✓ Ready", timeout=20000)
    inputs.nth(1).set_input_files(str(XML))
    page.wait_for_timeout(2500)  # second Ready + eager parse rerun
    page.screenshot(path=str(SHOTS / f"{shot_prefix}-2-ready.png"), full_page=True)

    process = page.get_by_role("button", name="Process", exact=True)
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


def history_flow(page, shot_prefix):
    url = nav_url(page, "Session history") or f"{BASE}/History"
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector("h1:has-text('Session history')", timeout=30000)
    page.wait_for_selector("text=ATTENDANCE TREND", timeout=30000)
    page.wait_for_timeout(1000)
    page.screenshot(path=str(SHOTS / f"{shot_prefix}-4-history.png"), full_page=True)
    body = page.locator("body").inner_text()
    check(f"{shot_prefix}: history sessions listed", "present" in body and "%" in body)


def lookup_flow(page, shot_prefix):
    url = nav_url(page, "Look up") or f"{BASE}/Lookup"
    page.goto(url, wait_until="networkidle")
    page.wait_for_selector("h1:has-text('Look up a student')", timeout=30000)
    box = page.get_by_label("Student number")
    box.fill("001")
    box.press("Enter")
    page.wait_for_selector("[data-testid='stImage'] img", timeout=60000)  # the timeline chart
    page.wait_for_timeout(2000)
    page.screenshot(path=str(SHOTS / f"{shot_prefix}-5-lookup.png"), full_page=True)
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
    page.screenshot(path=str(SHOTS / f"{shot_prefix}-6-investigate.png"), full_page=True)
    body = page.locator("body").inner_text()
    check(f"{shot_prefix}: verdict sentence shown", ("Match" in body) or ("Mismatch" in body))


with sync_playwright() as p:
    browser = p.chromium.launch()

    # --- Desktop pass (1440x900) ---------------------------------------------
    desktop = browser.new_context(viewport={"width": 1440, "height": 900})
    dpage = desktop.new_page()
    dashboard_flow(dpage, "desktop")
    process_flow(dpage, "desktop")
    history_flow(dpage, "desktop")
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
    dashboard_flow(ppage, "phone")
    no_hscroll(ppage, "phone Dashboard")
    process_flow(ppage, "phone")
    no_hscroll(ppage, "phone Process results")
    history_flow(ppage, "phone")
    no_hscroll(ppage, "phone History")
    lookup_flow(ppage, "phone")
    no_hscroll(ppage, "phone Lookup")
    investigate_flow(ppage, "phone")
    no_hscroll(ppage, "phone Investigate")

    # Touch-target floor: measure the Process page buttons on phone.
    purl = nav_url(ppage, "Mark today") or f"{BASE}/Process"
    ppage.goto(purl, wait_until="networkidle")
    ppage.wait_for_selector("h1:has-text('Mark today')", timeout=30000)
    # Let the rerun fully settle: Streamlit's transient Stop/status chrome is
    # not part of SAMS and must not be measured as an app touch target.
    ppage.wait_for_selector("[data-testid='stStatusWidget']", state="detached", timeout=30000)
    ppage.wait_for_timeout(1500)
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
