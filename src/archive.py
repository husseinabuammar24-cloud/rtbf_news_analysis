"""Collect RTBF article URLs by traversing the site and clicking "Charger ..."."""

import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from playwright.sync_api import Page, sync_playwright

BASE_URL = "https://www.rtbf.be"
START_URL = f"{BASE_URL}/en-continu"
OUTPUT_PATH = Path("data/raw/article_urls.txt")
LOAD_MORE_PATTERN = re.compile(r"Charger \d+ articles en plus")


def dismiss_cookies(page: Page) -> bool:
    """Close the cookie banner if visible; otherwise hide the overlay."""
    button = page.get_by_role("button", name="Refuser les cookies optionnels")
    try:
        button.wait_for(state="visible", timeout=15000)
        button.click()
        page.locator("#didomi-host").wait_for(state="hidden", timeout=5000)
        print("Cookie banner dismissed")
        return True
    except Exception as exc:  # pragma: no cover - script behavior only
        print(f"Cookie banner not dismissed by button ({type(exc).__name__}), hiding overlay")
        page.add_style_tag(content="#didomi-host{display:none !important}")
        return False


def get_links(page: Page) -> list[str]:
    """Collect all article links visible on the current page."""
    hrefs = page.eval_on_selector_all(
        'a[href*="/article/"]', "els => els.map(e => e.getAttribute('href'))"
    )

    unique_links: list[str] = []
    for href in hrefs:
        if not href:
            continue
        full_url = urljoin(BASE_URL, href)
        parsed = urlsplit(full_url)
        unique_links.append(f"{parsed.scheme}://{parsed.netloc}{parsed.path}")
    return unique_links


def save(urls: list[str] | dict[str, None]) -> None:
    """Persist discovered URLs to disk, keeping their order when possible."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(urls), encoding="utf-8")


def collect_urls(target: int = 3000, max_clicks: int = 100, headless: bool = False) -> list[str]:
    """Traverse progressively loaded article pages until enough URLs are collected."""
    urls: dict[str, None] = {}
    stalls = 0

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(START_URL, wait_until="domcontentloaded")
        dismiss_cookies(page)
        page.wait_for_timeout(2000)

        for click in range(max_clicks + 1):
            before = len(urls)
            for url in get_links(page):
                urls.setdefault(url)
            print(f"click {click}: {len(urls)} unique URLs (+{len(urls) - before})")

            if click % 10 == 0:
                save(urls)

            if len(urls) >= target:
                break

            stalls = stalls + 1 if (click > 0 and len(urls) == before) else 0
            if stalls >= 3:
                break

            button = page.get_by_text(LOAD_MORE_PATTERN)
            if button.count() == 0:
                print("No more 'Charger' button, stopping")
                break

            button.first.scroll_into_view_if_needed()
            button.first.click(timeout=10000)
            page.wait_for_timeout(2000)

        browser.close()

    return list(urls)


if __name__ == "__main__":
    collected_urls = collect_urls(target=3000, headless=False)
    save(collected_urls)
    print(f"\nSaved {len(collected_urls)} URLs to {OUTPUT_PATH}")