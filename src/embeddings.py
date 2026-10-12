"""Generate sentence embeddings for the cleaned article corpus.

This script turns each article's ``text`` field into a semantic vector using a
pretrained multilingual sentence-transformer model. The resulting NumPy array is
then used by the clustering and topic-modeling stages.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

INPUT_FILE = Path("data/processed/articles_clean.csv")
OUTPUT_FILE = Path("data/processed/embeddings.npy")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def main() -> None:
    """Load cleaned articles, encode them, and save the embedding matrix."""
    dataframe = pd.read_csv(INPUT_FILE)
    texts = dataframe["text"].fillna("").tolist()

    model = SentenceTransformer(MODEL_NAME)
    embeddings = model.encode(texts, show_progress_bar=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    np.save(OUTPUT_FILE, embeddings)

    print(f"Saved embeddings with shape {embeddings.shape} to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
