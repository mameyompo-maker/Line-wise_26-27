# Visit the Streamlit app with a real browser so Community Cloud counts it as
# traffic (plain HTTP GETs do not). If the app is hibernating, click the
# "get this app back up" button and wait for it to boot.
import re
import sys
import time

from playwright.sync_api import sync_playwright

APP_URL = "https://line-wise26-27-5t5bh4e67t3xjvevkazpru.streamlit.app/"


def app_is_rendered(page):
    try:
        return page.locator('div[data-testid="stAppViewContainer"]').count() > 0
    except Exception:
        return False


with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(APP_URL, wait_until="load", timeout=120_000)
    time.sleep(10)

    try:
        wake = page.get_by_text(re.compile(r"back up", re.I))
        if wake.count() > 0:
            print("App is asleep - clicking the wake-up button")
            wake.first.click()
    except Exception as e:
        print("Wake-button check failed:", e)

    ok = False
    for i in range(24):  # up to ~4 minutes for a cold boot
        if app_is_rendered(page):
            ok = True
            break
        time.sleep(10)

    # Stay connected a little longer so the visit is registered
    time.sleep(20)
    print("App rendered:", ok)
    browser.close()
    sys.exit(0 if ok else 1)
