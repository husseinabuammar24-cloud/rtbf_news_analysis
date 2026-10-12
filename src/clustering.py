"""Cluster cleaned RTBF articles into topic-like groups.

This script evaluates a range of cluster counts using silhouette score, selects
an appropriate k, and writes the cluster labels to a CSV alongside the article
metadata.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

EMBEDDINGS_PATH = Path("data/processed/embeddings.npy")
ARTICLES_PATH = Path("data/processed/articles_clean.csv")
OUT_PATH = Path("outputs/articles_with_clusters.csv")
SUMMARY_PATH = Path("outputs/cluster_summary.csv")


def choose_k(matrix: np.ndarray, ks: range = range(10, 51, 5)) -> int:
    """Pick the best cluster count from the provided range."""
    scores: dict[int, float] = {}

    for k in ks:
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(matrix)
        score = silhouette_score(
            matrix,
            labels,
            sample_size=min(len(matrix), 2000),
            random_state=42,
        )
        scores[k] = score
        print(f"k={k:>2}  silhouette={score:.3f}")

    return max(scores, key=scores.get)


def main() -> None:
    """Load the article embeddings, build clusters, and export the results."""
    embeddings = np.load(EMBEDDINGS_PATH)
    dataframe = pd.read_csv(ARTICLES_PATH)

    if len(dataframe) != len(embeddings):
        raise ValueError(
            f"Row mismatch: {len(dataframe)} articles vs {len(embeddings)} embeddings"
        )

    k = choose_k(embeddings)
    print(f"Chosen k: {k}")

    labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(embeddings)
    dataframe["cluster"] = labels

    crosstab = pd.crosstab(dataframe["cluster"], dataframe["category"])
    purity = (crosstab.max(axis=1) / crosstab.sum(axis=1)).round(2)
    summary = pd.DataFrame(
        {
            "size": crosstab.sum(axis=1),
            "top_category": crosstab.idxmax(axis=1),
            "purity": purity,
        }
    )
    print(summary.sort_values("size", ascending=False).to_string())

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(OUT_PATH, index=False)
    summary.to_csv(SUMMARY_PATH, index=False)
    print(f"Saved clustered output to {OUT_PATH}")


if __name__ == "__main__":
    main()