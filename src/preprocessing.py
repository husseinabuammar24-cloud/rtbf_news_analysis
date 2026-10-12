"""Clean the raw RTBF article dataset before embedding and clustering.

Usage (from the project root):
    python src/preprocessing.py
"""

import re
from pathlib import Path

import pandas as pd

RAW_PATH = Path("data/raw/articles.csv")
OUT_PATH = Path("data/processed/articles_clean.csv")
MIN_LENGTH = 500

NON_NEWS_TITLES = [
    r"^RTBF ACTUS\s*:",
    r"abonnez-vous",
    r"^Remportez ",
    r"^Gagnez ",
]


def clean_for_embeddings(text: str) -> str:
    """Normalize whitespace for embedding input."""
    return re.sub(r"\s+", " ", text.strip())


def step(frame: pd.DataFrame, label: str, before: int) -> int:
    """Print how many rows were removed and return the new row count."""
    removed = before - len(frame)
    print(f"{label:<35} {removed:>5} removed -> {len(frame)} rows")
    return len(frame)


def main() -> None:
    """Apply a series of cleanup rules to the raw RTBF dataset."""
    dataframe = pd.read_csv(RAW_PATH)
    before = len(dataframe)
    print(f"Raw: {before} rows, {dataframe.shape[1]} columns\n")

    dataframe = dataframe.dropna(subset=["title", "article_body"])
    before = step(dataframe, "Missing title/body", before)

    dataframe = dataframe.drop_duplicates(subset="url")
    before = step(dataframe, "Duplicate url", before)
    dataframe = dataframe.drop_duplicates(subset="title")
    before = step(dataframe, "Duplicate title", before)

    pattern = "|".join(NON_NEWS_TITLES)
    dataframe = dataframe[~dataframe["title"].str.contains(pattern, case=False, regex=True)]
    before = step(dataframe, "Non-news titles", before)

    dataframe = dataframe[dataframe["article_length"] >= MIN_LENGTH]
    before = step(dataframe, f"Shorter than {MIN_LENGTH} chars", before)

    dataframe = dataframe.copy()
    dataframe["published_date"] = pd.to_datetime(
        dataframe["published_date"], utc=True, errors="coerce"
    ).dt.tz_convert("Europe/Brussels")
    dataframe = dataframe.dropna(subset=["published_date"])
    before = step(dataframe, "Unparseable dates", before)
    dataframe["date"] = dataframe["published_date"].dt.date

    dataframe["text"] = (
        dataframe["title"] + ". " + dataframe["article_body"].str.replace("\n", " ")
    )
    dataframe["text"] = dataframe["text"].map(clean_for_embeddings)

    dataframe = dataframe.sort_values("published_date").reset_index(drop=True)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(OUT_PATH, index=False)

    print(f"\nClean dataset: {dataframe.shape[0]} articles -> {OUT_PATH}")
    print(f"Period: {dataframe['published_date'].min()}  ->  {dataframe['published_date'].max()}")
    print("\nArticles per category:")
    print(
        dataframe["category"].fillna("(none)").replace("", "(none)").value_counts().head(10)
    )
    print("\nArticle length:")
    print(dataframe["article_length"].describe())

    print(dataframe.sample(20, random_state=1)["article_body"].str[-150:].to_string())

    for phrase in ["Lire aussi", "Newsletter", "Publicité", "Cookie", "Belga", "abonnez"]:
        print(f"{phrase}: {dataframe['article_body'].str.contains(phrase, case=False).mean():.1%}")

    print(
        "Backslashes in body:",
        dataframe["article_body"].str.contains(r"\\", regex=True).mean(),
    )


if __name__ == "__main__":
    main()
