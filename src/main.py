"""
Parse all collected article URLs and save them to a CSV file.

Usage (from the project root):
    python src/main.py        # all URLs
"""

import csv
import sys
import time
from pathlib import Path

import pandas as pd

from article_parser import extract_article

URLS_FILE = Path("data/raw/article_urls.txt")
OUT = Path("data/raw/articles.csv")
FAILED = Path("data/raw/failed_urls.txt")

FIELDS = [
    "url", "title", "published_date", "author", "category",
    "article_type", "lead", "article_body", "article_length",
]
DELAY = 0.5      # seconds between requests (be polite to RTBF)
RETRIES = 3


def load_urls() -> list[str]:
    lines = URLS_FILE.read_text(encoding="utf-8").splitlines()
    return list(dict.fromkeys(u.strip() for u in lines if u.strip()))


def already_scraped() -> set[str]:
    if not OUT.exists():
        return set()
    return set(pd.read_csv(OUT, usecols=["url"])["url"])


def fetch(url: str) -> dict | None:
    """Try a URL a few times, backing off between attempts."""
    for attempt in range(1, RETRIES + 1):
        try:
            return extract_article(url)
        except Exception as e:
            if attempt == RETRIES:
                raise
            print(f"  retry {attempt}/{RETRIES - 1} for {url}: {e}")
            time.sleep(2 * attempt)


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None

    urls = load_urls()
    done = already_scraped()
    todo = [u for u in urls if u not in done]
    if limit:
        todo = todo[:limit]
    print(f"{len(urls)} URLs total, {len(done)} already scraped, {len(todo)} to do")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    write_header = not OUT.exists()
    failed = []

    with open(OUT, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()

        for i, url in enumerate(todo, 1):
            try:
                article = fetch(url)
                if article is None:
                    print(f"[{i}/{len(todo)}] no JSON-LD: {url}")
                    failed.append(url)
                else:
                    writer.writerow(article)
                    f.flush()  # written to disk immediately
                    print(f"[{i}/{len(todo)}] {article['article_length']:>6} chars | {article['title'][:60]}")
            except Exception as e:
                print(f"[{i}/{len(todo)}] ERROR {url}: {e}")
                failed.append(url)
            time.sleep(DELAY)

    if failed:
        FAILED.write_text("\n".join(failed), encoding="utf-8")
        print(f"\n{len(failed)} failed URLs saved to {FAILED}")

    # Final summary
    df = pd.read_csv(OUT).drop_duplicates(subset="url")
    df.to_csv(OUT, index=False)
    print(f"\nDataset: {df.shape[0]} articles, {df.shape[1]} columns -> {OUT}")
    print(df["article_length"].describe())


if __name__ == "__main__":
    main()
