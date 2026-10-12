"""Scrape RTBF articles from a list of URL candidates and save them to CSV.

Usage from the project root:
    python src/scrape_articles.py
    python src/scrape_articles.py 100
"""

import csv
import sys
import time
from pathlib import Path

import pandas as pd

from article_parser import extract_article

URLS_FILE = Path("data/raw/article_urls.txt")
OUT_PATH = Path("data/raw/articles.csv")
FAILED_PATH = Path("data/raw/failed_urls.txt")

FIELDS = [
    "url",
    "title",
    "published_date",
    "author",
    "category",
    "article_type",
    "lead",
    "article_body",
    "article_length",
]
DELAY_SECONDS = 0.5
RETRIES = 3


def load_urls(path: Path = URLS_FILE) -> list[str]:
    """Read URLs while preserving their order and removing duplicates/blank lines."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return list(dict.fromkeys(url.strip() for url in lines if url.strip()))


def already_scraped(path: Path = OUT_PATH) -> set[str]:
    """Return the set of URLs already saved to the output CSV."""
    if not path.exists():
        return set()
    return set(pd.read_csv(path, usecols=["url"])["url"])


def fetch(url: str) -> dict | None:
    """Try to extract a single article, retrying on transient failures."""
    for attempt in range(1, RETRIES + 1):
        try:
            return extract_article(url)
        except Exception as exc:  # pragma: no cover - script behavior only
            if attempt == RETRIES:
                raise
            print(f"  retry {attempt}/{RETRIES - 1} for {url}: {exc}")
            time.sleep(2 * attempt)

    return None


def main() -> None:
    """Process URLs, skip ones already scraped, and persist the results to CSV."""
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    urls = load_urls(URLS_FILE)
    done = already_scraped(OUT_PATH)
    todo = [url for url in urls if url not in done]
    if limit is not None:
        todo = todo[:limit]

    print(f"{len(urls)} URLs total, {len(done)} already scraped, {len(todo)} to do")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_header = not OUT_PATH.exists()
    failed_urls: list[str] = []

    with OUT_PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()

        for index, url in enumerate(todo, start=1):
            try:
                article = fetch(url)
                if article is None:
                    print(f"[{index}/{len(todo)}] no JSON-LD: {url}")
                    failed_urls.append(url)
                else:
                    writer.writerow(article)
                    handle.flush()
                    print(
                        f"[{index}/{len(todo)}] {article['article_length']:>6} chars | "
                        f"{article['title'][:60]}"
                    )
            except Exception as exc:  # pragma: no cover - script behavior only
                print(f"[{index}/{len(todo)}] ERROR {url}: {exc}")
                failed_urls.append(url)

            time.sleep(DELAY_SECONDS)

    if failed_urls:
        FAILED_PATH.write_text("\n".join(failed_urls), encoding="utf-8")
        print(f"\n{len(failed_urls)} failed URLs saved to {FAILED_PATH}")

    dataframe = pd.read_csv(OUT_PATH).drop_duplicates(subset="url")
    dataframe.to_csv(OUT_PATH, index=False)
    print(f"\nDataset: {dataframe.shape[0]} articles, {dataframe.shape[1]} columns -> {OUT_PATH}")
    print(dataframe["article_length"].describe())


if __name__ == "__main__":
    main()
