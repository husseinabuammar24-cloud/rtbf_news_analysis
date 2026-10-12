"""Build the raw article dataset from the collected RTBF URLs."""

from pathlib import Path

import pandas as pd

from article_parser import extract_article

URLS_FILE = Path("data/raw/article_urls.txt")
OUTPUT_FILE = Path("data/raw/articles.csv")


def load_urls(path: Path = URLS_FILE) -> list[str]:
    """Read unique article URLs, ignoring empty lines."""
    urls = path.read_text(encoding="utf-8").splitlines()
    return list(dict.fromkeys(url.strip() for url in urls if url.strip()))


def build_dataset(urls_file: Path = URLS_FILE, output_file: Path = OUTPUT_FILE) -> pd.DataFrame:
    """Fetch each article, keep valid records, and save them to CSV."""
    articles: list[dict] = []

    for index, url in enumerate(load_urls(urls_file), start=1):
        try:
            article = extract_article(url)
            if article is None:
                print(f"[{index}] No article data found: {url}")
                continue

            articles.append(article)
            print(f"[{index}] ✓ {article['title'][:80]}")
        except Exception as exc:  # pragma: no cover - this is an operational script.
            print(f"[{index}] Error for {url}: {exc}")

    output_file.parent.mkdir(parents=True, exist_ok=True)
    dataframe = pd.DataFrame(articles)
    dataframe.to_csv(output_file, index=False)

    print(f"Saved {len(dataframe)} articles to {output_file}")
    return dataframe


def main() -> None:
    """Entry point for the dataset builder."""
    build_dataset()


if __name__ == "__main__":
    main()