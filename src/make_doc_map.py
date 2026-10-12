"""Compute 2D coordinates (UMAP) for every article and save them for the dashboard.

Run once from the project root:  python -m src.make_doc_map
The dashboard only reads the small CSV, so it does not need the full embedding model.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import umap

EMBEDDINGS_PATH = Path("data/processed/embeddings.npy")
ARTICLES_PATH = Path("data/processed/articles_clean.csv")
OUT_PATH = Path("outputs/doc_map_coords.csv")


def main() -> None:
    """Reduce the article embedding matrix to 2D coordinates and export them."""
    embeddings = np.load(EMBEDDINGS_PATH)
    urls = pd.read_csv(ARTICLES_PATH, usecols=["url"])["url"]

    if len(urls) != len(embeddings):
        raise ValueError(f"Row mismatch: {len(urls)} articles vs {len(embeddings)} embeddings")

    mapper = umap.UMAP(
        n_components=2,
        n_neighbors=15,
        min_dist=0.1,
        metric="cosine",
        random_state=42,
    )
    coordinates = mapper.fit_transform(embeddings)

    result = pd.DataFrame(
        {
            "url": urls,
            "x": coordinates[:, 0].round(4),
            "y": coordinates[:, 1].round(4),
        }
    )
    result = result.drop_duplicates("url")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(result)} points to {OUT_PATH}")


if __name__ == "__main__":
    main()