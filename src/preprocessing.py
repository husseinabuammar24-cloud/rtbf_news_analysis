"""
Clean the raw RTBF articles.

Usage (from the project root, after the scraper has finished):
    python src/preprocessing.py
"""

from pathlib import Path

import pandas as pd

RAW = Path("data/raw/articles.csv")
OUT = Path("data/processed/articles_clean.csv")

MIN_LENGTH = 500  # shorter pages are usually videos, briefs or promos

# Titles that are service/promo pages, not news (case-insensitive regex).
# Extend this list as you spot more in the data.
NON_NEWS_TITLES = [
    r"^RTBF ACTUS\s*:",
    r"abonnez-vous",
    r"^Remportez ",
    r"^Gagnez ",
]


def step(df: pd.DataFrame, label: str, before: int) -> int:
    print(f"{label:<35} {before - len(df):>5} removed -> {len(df)} rows")
    return len(df)


def main() -> None:
    df = pd.read_csv(RAW)
    n = len(df)
    print(f"Raw: {n} rows, {df.shape[1]} columns\n")

    # 1. Missing essentials
    df = df.dropna(subset=["title", "article_body"])
    n = step(df, "Missing title/body", n)

    # 2. Duplicates
    df = df.drop_duplicates(subset="url")
    n = step(df, "Duplicate url", n)
    df = df.drop_duplicates(subset="title")
    n = step(df, "Duplicate title", n)

    # 3. Service / promo pages
    pattern = "|".join(NON_NEWS_TITLES)
    df = df[~df["title"].str.contains(pattern, case=False, regex=True)]
    n = step(df, "Non-news titles", n)

    # 4. Too-short articles
    df = df[df["article_length"] >= MIN_LENGTH]
    n = step(df, f"Shorter than {MIN_LENGTH} chars", n)

    # 5. Dates: parse with timezone, convert to Brussels time
    df = df.copy()
    df["published_date"] = pd.to_datetime(
        df["published_date"], utc=True, errors="coerce"
    ).dt.tz_convert("Europe/Brussels")
    df = df.dropna(subset=["published_date"])
    n = step(df, "Unparseable dates", n)
    df["date"] = df["published_date"].dt.date

    # 6. Text used later for embeddings.
    # article_body already starts with the lead, so don't add 'lead' again.
    df["text"] = df["title"] + ". " + df["article_body"].str.replace("\n", " ")

    df = df.sort_values("published_date").reset_index(drop=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    print(f"\nClean dataset: {df.shape[0]} articles -> {OUT}")
    print(f"Period: {df['published_date'].min()}  ->  {df['published_date'].max()}")
    print("\nArticles per category:")
    print(df["category"].fillna("(none)").replace("", "(none)").value_counts().head(10))
    print("\nArticle length:")
    print(df["article_length"].describe())


if __name__ == "__main__":
    main()
