# Visit the Streamlit app with a real browser so Community Cloud counts it as
# traffic (plain HTTP GETs do not). If the app is hibernating, click the
# wake-up button and wait for it to boot.
import re
import sys
import time

from playwright.sync_api import sync_playwright

APP_URL = "https://line-wise26-27-5t5bh4e67t3xjvevkazpru.streamlit.app/"


def rendered(page):
    try:
        return page.locator('div[data-testid="stAppViewContainer"]').count() > 0
    except Exception:
        return False


def try_click_wake(page):
    try:
        for btn in page.get_by_role("button").all():
            txt = (btn.inner_text() or "").strip()
            if re.search(r"back up|wake", txt, re.I):
                print(f"Clicking wake button: {txt!r}")
                btn.click()
                return True
    except Exception as e:
        print("Wake-button scan error:", e)
    return False


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 800, "height": 900})
    page.goto(APP_URL, wait_until="domcontentloaded", timeout=120_000)
    time.sleep(12)
    print("url:", page.url)
    print("title:", page.title())

    ok = False
    for i in range(30):  # up to ~5 minutes, covers a cold boot
        if rendered(page):
            ok = True
            break
        try_click_wake(page)
        time.sleep(10)

    # Stay connected a little longer so the visit is registered
    time.sleep(20)

    try:
        snippet = page.inner_text("body")[:300].replace("\n", " | ")
        print("body snippet:", snippet)
    except Exception:
        pass
    try:
        page.screenshot(path="keep_awake_result.png", full_page=True)
    except Exception as e:
        print("screenshot failed:", e)

    print("App rendered:", ok)
    browser.close()
    sys.exit(0 if ok else 1)
