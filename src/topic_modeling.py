"""
topic_modeling.py - BERTopic on precomputed embeddings (RTBF articles).

Run from the project root:  python src/topic_modeling.py
Needs: data/processed/articles_clean.csv and data/processed/embeddings.npy
(embeddings.npy must come from the SAME csv - re-run embeddings.py if you re-run preprocessing).
"""
from pathlib import Path

import numpy as np
import pandas as pd
from bertopic import BERTopic
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP

DATA_PATH = Path("data/processed/articles_clean.csv")
EMB_PATH = Path("data/processed/embeddings.npy")
OUT_DIR = Path("outputs")

DATE_COL = "date"            # or "published_date"
TITLE_COL = "title"
CAT_COL = "category"

MIN_CLUSTER_SIZE = 10        # smaller -> more, finer topics; larger -> fewer, broader topics
REDUCE_OUTLIERS = False
SEED = 42

# Compact French stopword list (no extra download needed) + RTBF-specific words.
FRENCH_STOPWORDS = """
a à afin ai aie ainsi ait alors après au aucun aura aurait aussi autre autres aux avait avant avec avoir
beaucoup bien car ce ceci cela celle celles celui ces cet cette ceux chaque chez comme comment dans de des
depuis dès deux donc dont du elle elles en encore entre est et étaient était été étre être eu eux fait faire
fois il ils je jusqu jusque la là le les leur leurs lors lui ma mais me même mes moi moins mon ne ni nos notre
nous on ont ou où par parce pas peu peut plus plusieurs pour pourquoi premier puis qu quand que quel quelle
quelles quels qui sa sans se sera ses si sont sous sur ta te tes toi ton tous tout toute toutes très tu un une
vers voici voilà vos votre vous y d l j m n s t c qu aujourd hui cette ceux ici déjà sera seront peut-être
être avoir ans an jour jours selon également ainsi alors afin notamment depuis lors
rtbf belga photo auvio première vidéo article lire aussi son ça sa ses leur leurs cest dun dune
the of and to in is it for you
""".split()


def load_data():
    df = pd.read_csv(DATA_PATH)
    df[DATE_COL] = pd.to_datetime(df[DATE_COL], utc=True)
    embeddings = np.load(EMB_PATH)
    assert len(df) == len(embeddings), (
        f"Row mismatch: {len(df)} articles vs {len(embeddings)} embeddings. Re-run embeddings.py."
    )
    return df, embeddings


def build_topic_model():
    umap_model = UMAP(n_neighbors=15, n_components=5, min_dist=0.0,
                      metric="cosine", random_state=SEED)
    hdbscan_model = HDBSCAN(min_cluster_size=MIN_CLUSTER_SIZE, metric="euclidean",
                            cluster_selection_method="eom", prediction_data=True)
    vectorizer = CountVectorizer(stop_words=FRENCH_STOPWORDS, ngram_range=(1, 2), min_df=3)
    return BERTopic(
        language="french",          
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer,
        top_n_words=10,
        calculate_probabilities=False,
        verbose=True,
    )


def main():
    OUT_DIR.mkdir(exist_ok=True)
    df, embeddings = load_data()
    docs = df["text"].tolist()

    topic_model = build_topic_model()
    topics, _ = topic_model.fit_transform(docs, embeddings)
    print(f"\nTopics found: {len(set(topics)) - (1 if -1 in topics else 0)}")
    print(f"Outliers (-1): {sum(t == -1 for t in topics)} / {len(topics)}")

    if REDUCE_OUTLIERS:
        topics = topic_model.reduce_outliers(docs, topics, strategy="embeddings", embeddings=embeddings)
        topic_model.update_topics(docs, topics=topics, vectorizer_model=topic_model.vectorizer_model)
        print(f"Outliers after reduction: {sum(t == -1 for t in topics)}")

    df["topic"] = topics
    topic_info = topic_model.get_topic_info()
    print("\n", topic_info[["Topic", "Count", "Name"]].head(25).to_string(index=False))

    # Save results
    topic_info.to_csv(OUT_DIR / "topic_info.csv", index=False)
    df.drop(columns=["text"]).to_csv(OUT_DIR / "articles_with_topics.csv", index=False)

    # Topic vs original RTBF category (sanity check: do topics make sense?)
    top_cats = df.groupby("topic")[CAT_COL].agg(lambda s: s.value_counts().head(3).to_dict())
    print("\nMain categories per topic (first 15):")
    print(top_cats.head(15).to_string())

    # Visualizations (interactive HTML)
    topic_model.visualize_barchart(top_n_topics=12).write_html(OUT_DIR / "topics_barchart.html")
    topic_model.visualize_topics().write_html(OUT_DIR / "topics_map.html")
    topic_model.visualize_hierarchy().write_html(OUT_DIR / "topics_hierarchy.html")

    umap_2d = UMAP(n_neighbors=15, n_components=2, min_dist=0.0,
                   metric="cosine", random_state=SEED).fit_transform(embeddings)
    topic_model.visualize_documents(df[TITLE_COL].tolist(), reduced_embeddings=umap_2d,
                                    hide_annotations=True).write_html(OUT_DIR / "documents_map.html")

    timestamps = df[DATE_COL].dt.tz_localize(None)   # BERTopic wants naive datetimes
    tot = topic_model.topics_over_time(docs, timestamps, nr_bins=24)
    topic_model.visualize_topics_over_time(tot, top_n_topics=8).write_html(OUT_DIR / "topics_over_time.html")

    print(f"\nSaved results and HTML visualizations in {OUT_DIR}/")


if __name__ == "__main__":
    main()