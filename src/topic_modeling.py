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
RECENT_DAYS = 30             # time chart only uses the last N days (a few old articles stretch the axis)
SEED = 42

# Readable names {topic_id: "name"}. Ids are only valid for THIS model run:
# if you change MIN_CLUSTER_SIZE, the data or the embeddings, check them again.
# Topics not listed here keep their automatic 3-keyword label.
TOPIC_NAMES: dict[int, str] = {
    0: "Cinéma & séries",
    1: "Musique & concerts",
    2: "Cyclisme",
    3: "Écoles & jeunesse",
    4: "Diables Rouges (football)",
    5: "Procès & justice",
    6: "Guerre en Ukraine",
    7: "Jeux vidéo",
    8: "Budget & gouvernement",
    9: "Météo",
    10: "Événements & festivals (Namur)",
    11: "Football : Ronaldo & Messi",
}

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


def apply_topic_names(topic_model):
    """Automatic 3-keyword labels first, then overwrite with TOPIC_NAMES. Returns {id: label}."""
    ids = sorted(topic_model.get_topics().keys())            # includes -1
    auto = topic_model.generate_topic_labels(
        nr_words=3, topic_prefix=False, word_length=15, separator=" / "
    )
    labels = dict(zip(ids, auto))
    labels.update(TOPIC_NAMES)
    labels[-1] = "Non classé"
    topic_model.set_topic_labels(labels)
    return labels


def save_visualizations(figures) -> None:
    """Save interactive Plotly figures and remove their legacy PNG exports."""
    for html_name, figure in figures.items():
        html_path = OUT_DIR / html_name
        figure.write_html(html_path, include_plotlyjs="cdn")
        print(f"Saved {html_path}")

    for html_name in figures:
        legacy_png = OUT_DIR / f"{Path(html_name).stem}.png"
        if legacy_png.exists():
            legacy_png.unlink()


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
    labels = apply_topic_names(topic_model)

    topic_info = topic_model.get_topic_info()
    topic_info["Label"] = topic_info["Topic"].map(labels)
    print("\n", topic_info[["Topic", "Count", "Label"]].head(25).to_string(index=False))

    # Save results
    topic_info.to_csv(OUT_DIR / "topic_info.csv", index=False)
    df.drop(columns=["text"]).to_csv(OUT_DIR / "articles_with_topics.csv", index=False)

    # Topic vs original RTBF category (sanity check: do topics make sense?)
    top_cats = df.groupby("topic")[CAT_COL].agg(lambda s: s.value_counts().head(3).to_dict())
    print("\nMain categories per topic (first 15):")
    print(top_cats.head(15).to_string())

    # Interactive HTML visualizations, all using the readable names.
    figures = {
        "topics_barchart.html": topic_model.visualize_barchart(
            top_n_topics=12, n_words=5, custom_labels=True, width=320, height=320
        ),
        "topics_map.html": topic_model.visualize_topics(custom_labels=True),
        "topics_hierarchy.html": topic_model.visualize_hierarchy(custom_labels=True),
    }

    umap_2d = UMAP(n_neighbors=15, n_components=2, min_dist=0.0,
                   metric="cosine", random_state=SEED).fit_transform(embeddings)
    figures["documents_map.html"] = topic_model.visualize_documents(
        df[TITLE_COL].tolist(), reduced_embeddings=umap_2d,
        hide_annotations=True, custom_labels=True,
    )

    # Topics over time: only the last RECENT_DAYS days, one bin per day.
    # Older articles with wrong/archived dates would otherwise stretch the axis over years.
    timestamps = df[DATE_COL].dt.tz_localize(None)           # BERTopic wants naive datetimes
    recent = timestamps >= timestamps.max() - pd.Timedelta(days=RECENT_DAYS)
    tot = topic_model.topics_over_time(
        [d for d, keep in zip(docs, recent) if keep],
        timestamps[recent].tolist(),
        topics=df.loc[recent, "topic"].tolist(),
        nr_bins=RECENT_DAYS,
    )
    figures["topics_over_time.html"] = topic_model.visualize_topics_over_time(
        tot, top_n_topics=8, custom_labels=True
    )

    save_visualizations(figures)

    print(f"\nSaved results and interactive HTML visualizations in {OUT_DIR}/")


if __name__ == "__main__":
    main()
