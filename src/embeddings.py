import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

df = pd.read_csv("data/processed/articles_clean.csv")

texts = df["text"].fillna("").tolist()

model = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2"
)

embeddings = model.encode(
    texts,
    show_progress_bar=True
)

np.save(
    "data/processed/embeddings.npy",
    embeddings
)

print("Shape:", embeddings.shape)
