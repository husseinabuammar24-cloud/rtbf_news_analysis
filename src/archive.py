'''
Collect ALL urls
'''

import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import sync_playwright

BASE = "https://www.rtbf.be"
START = f"{BASE}/en-continu"
OUT = Path("data/raw/article_urls.txt")
LOAD_MORE = re.compile(r"Charger \d+ articles en plus")


def dismiss_cookies(page) -> bool:
    button = page.get_by_role("button", name="Refuser les cookies optionnels")
    try:
        button.wait_for(state="visible", timeout=15000)
        button.click()
        page.locator("#didomi-host").wait_for(state="hidden", timeout=5000)
        print("Cookie banner dismissed")
        return True
    except Exception as e:
        print(f"Cookie banner not dismissed by button ({type(e).__name__}), hiding overlay")
        # Last resort: hide the overlay so it can't intercept clicks
        page.add_style_tag(content="#didomi-host{display:none !important}")
        return False


def get_links(page) -> list[str]:
    hrefs = page.eval_on_selector_all(
        'a[href*="/article/"]', "els => els.map(e => e.getAttribute('href'))"
    )
    out = []
    for h in hrefs:
        if not h:
            continue
        full = urljoin(BASE, h)
        parts = urlsplit(full)
        out.append(f"{parts.scheme}://{parts.netloc}{parts.path}")  # drop ?query/#hash
    return out


def save(urls) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(urls), encoding="utf-8")


def collect_urls(target: int = 3000, max_clicks: int = 100, headless: bool = False) -> list[str]:
    urls: dict[str, None] = {}  # dict keeps order and removes duplicates
    stalls = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(START, wait_until="domcontentloaded")
        dismiss_cookies(page)
        page.wait_for_timeout(2000)

        for click in range(max_clicks + 1):
            before = len(urls)
            for u in get_links(page):
                urls.setdefault(u)
            print(f"click {click}: {len(urls)} unique URLs (+{len(urls) - before})")

            # checkpoint every 10 clicks so a crash doesn't lose everything
            if click % 10 == 0:
                save(urls)

            if len(urls) >= target:
                break

            # stop if three clicks in a row bring nothing new
            stalls = stalls + 1 if (click > 0 and len(urls) == before) else 0
            if stalls >= 3:
                break

            button = page.get_by_text(LOAD_MORE)
            if button.count() == 0:
                print("No more 'Charger' button, stopping")
                break

            button.first.scroll_into_view_if_needed()
            button.first.click(timeout=10000)
            page.wait_for_timeout(2000)  # let the new articles render

        browser.close()

    return list(urls)


if __name__ == "__main__":
    urls = collect_urls(target=3000, headless=False)
    save(urls)
    print(f"\nSaved {len(urls)} URLs to {OUT}")