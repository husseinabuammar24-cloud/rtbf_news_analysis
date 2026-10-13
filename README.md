# RTBF News Analysis

An end-to-end NLP project that turns RTBF news articles into an explorable map of recurring topics. The workflow collects and parses articles, cleans the corpus, creates multilingual embeddings, clusters similar stories, and models topics with BERTopic.

## Live dashboard

[Open RTBF News Analysis](https://rtbf-news-analysis.streamlit.app/)

[Explore the interactive document map](outputs/documents_map.html)

## Project overview

RTBF publishes articles across many subjects, making it difficult to scan recurring coverage themes across a large corpus. This project collects public RTBF articles, cleans them, represents their meaning with multilingual sentence embeddings, groups them with clustering and topic modeling, and presents the results in an interactive dashboard. It is intended for readers and analysts who want to explore what RTBF covers and how themes change over time.

## Key results

- **2,123 cleaned articles** are included in the current results snapshot.
- **37 topics** were assigned by BERTopic; **623 articles (29.3%)** were left as outliers because they did not fit a topic.
- A separate K-Means analysis produced **10 article clusters**.

Results are based on the files currently committed under `outputs/` and will change when the pipeline is rerun on a new corpus.

## Features

- View article, topic, and cluster summaries, including coverage trends and potential gaps.
- Search topic names and keywords in the Topic Explorer.
- Filter and search articles by RTBF category, topic, date, and title; open the source article from its link.
- Explore a semantic article map, highlight topics, and color points by topic, RTBF category, or K-Means cluster.
- Explore interactive topic visualizations and download the article table as CSV.

## Pipeline

1. Collect article URLs with `src/archive.py`.
2. Scrape article metadata and text with `src/scrape_articles.py` and `src/article_parser.py`.
3. Clean and validate the corpus with `src/preprocessing.py`.
4. Generate multilingual sentence embeddings with `src/embeddings.py`.
5. Cluster articles with `src/clustering.py`.
6. Discover and summarize topics with `src/topic_modeling.py`, which exports interactive HTML visualizations, and build the document map with `src/make_doc_map.py`.
7. Explore results in the Streamlit dashboard.

The analysis uses Sentence Transformers, UMAP, HDBSCAN, and BERTopic. Data collection and processing use Python, Playwright, Requests, BeautifulSoup, pandas, and NumPy; visualizations use Plotly and Streamlit.

Sentence Transformers create multilingual semantic embeddings. BERTopic combines embeddings with dimensionality reduction and density-based clustering, which helps group articles by meaning rather than relying only on word counts as standard LDA does. K-Means is also run separately to provide a fixed-count cluster view. Topic labels combine keywords with manual names and should be reviewed.

## Repository structure

```text
.
├── .streamlit/          # Streamlit theme
├── assets/              # README screenshots
├── dashboard/
│   ├── app.py            # Streamlit dashboard
│   └── requirements.txt  # Dashboard dependencies
├── data/
│   ├── raw/             # Collected URLs and scraped articles
│   └── processed/       # Cleaned article corpus
├── outputs/             # Topic, cluster, map, and visualization results
├── src/                 # Collection, processing, and modeling scripts
├── tests/               # Scraper check
├── RTBF_Coverage_Intelligence.ppt  # Legacy PowerPoint deck
├── .gitignore
├── README.md
└── requirements.txt     # Full pipeline dependencies
```

## Setup and run

Requires Python 3. Create an environment and install dependencies:

**Python 3.11** is recommended for a consistent local setup. The optional development-container configuration is not included in this repository.

```bash
python3 -m venv nlp-env
source nlp-env/bin/activate
pip install -r requirements.txt
```

Run the pipeline from the project root, in order:

```bash
python src/archive.py
python src/scrape_articles.py
python src/preprocessing.py
python src/embeddings.py
python src/clustering.py
python src/topic_modeling.py
python src/make_doc_map.py
streamlit run dashboard/app.py
```

Scraping requires Playwright's Chromium browser. Install it once with `playwright install chromium` if needed. Topic visualizations are exported as interactive HTML charts.

## Screenshots

The article map appears near the top of this README. The dashboard overview and topic word-score chart are shown here:

![RTBF Coverage Intelligence dashboard overview](assets/readme/dashboard.png)

[Open the interactive topic word-score chart](outputs/topics_barchart.html)

## Main files

- `data/raw/articles.csv` — scraped article records
- `data/processed/articles_clean.csv` — cleaned article corpus
- `data/processed/embeddings.npy` — generated semantic vectors (not committed)
- `outputs/articles_with_clusters.csv`, `outputs/cluster_summary.csv` — cluster assignments and summaries
- `outputs/articles_with_topics.csv`, `outputs/topic_info.csv` — topic assignments and topic summaries
- `outputs/*.html` — interactive topic and document visualizations

Topic labels are automated summaries of semantic groups, not a definitive news taxonomy. Review representative articles and validate labels before drawing editorial conclusions.

## Project details

- **Timeline:** 4 days
- **Author:** [Hussein Abuammar](https://www.linkedin.com/in/hussein-abuammar)
- **Work sequence:** article collection and cleaning, embeddings and modeling, dashboard development, and deployment.
- **GitHub:** [husseinabuammar24-cloud](https://github.com/husseinabuammar24-cloud) · [Project repository](https://github.com/husseinabuammar24-cloud/rtbf_news_analysis)

High-level breakdown of the four-day project:

| Day | Work |
| --- | --- |
| 1 | Collect and parse RTBF articles; clean the corpus. |
| 2 | Generate embeddings and evaluate K-Means clusters. |
| 3 | Fit BERTopic, review topic labels, and create visualizations. |
| 4 | Build the dashboard, deploy it, and document the project. |

## Deployment and scaling

The dashboard is deployed on Streamlit Community Cloud and reads the prepared CSV and interactive HTML visualization files in this repository. The current project runs collection and model generation as manual pipeline steps. For a production workflow, schedule scraping and model updates on a worker, store raw and processed data plus model artifacts in cloud object storage, and let the hosted dashboard read the latest prepared outputs. This scheduled and storage-backed setup is a proposed next step; it is not currently automated.

## Limitations and next steps

- **Outliers:** 623 of 2,123 articles (29.3%) were not assigned to a BERTopic topic, so one-off or unusual stories are not represented by the topic summaries.
- **Dates:** 50 records fall outside the latest 30-day window used for trend views. Some publication dates are unexpectedly old or may reflect archive metadata, so date-based conclusions need checking.
- **Labels:** Topic labels are generated from keywords and selectively renamed by hand. Review representative articles before treating a label as a definitive classification.
- **Next steps:** review date anomalies and outlier handling, validate topic labels with representative articles, and automate the refresh pipeline if the dashboard is used continuously.

## Acknowledgements and license

Built as a BeCode project using public articles from RTBF. No software license file is currently included in the repository.
