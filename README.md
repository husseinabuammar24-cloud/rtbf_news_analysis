# RTBF News Analysis & Clustering

## Project Overview

This project analyzes RTBF news coverage by:

- Scraping RTBF news articles and metadata
- Cleaning and validating a large-scale news dataset
- Performing topic modeling to discover major themes
- Clustering semantically similar articles
- Visualizing trends, news cycles, and content coverage
- Building an interactive dashboard for exploring the results

The objective is to help identify trending topics, content clusters, and potential coverage gaps within RTBF news production.

---

## Dataset Summary

### Raw Dataset
- 2,161 scraped articles

### Clean Dataset
- 2,123 validated articles

### Coverage Period
- October 2020 to October 2026

### Average Article Length
- 2,900 characters

---

## Technologies

### Data Collection
- Python
- Requests
- BeautifulSoup
- JSON-LD Parsing

### NLP & Machine Learning
- Sentence Transformers
- BERTopic
- HDBSCAN
- UMAP

### Data Processing
- Pandas
- NumPy

### Visualization & Deployment
- Streamlit
- Plotly

---

## Project Structure

```text
rtbf_news_analysis/

├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── article_parser.py
│   ├── preprocessing.py
│   ├── embeddings.py
│   ├── topic_modeling.py
│   ├── clustering.py
│   └── scraper.py
│
├── dashboard/
│
├── notebooks/
│
├── tests/
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

## Data Cleaning & Validation

The preprocessing pipeline performs the following checks:

- Removed duplicate articles
- Removed duplicate titles
- Removed articles with missing content
- Removed non-news pages
- Filtered articles shorter than 500 characters
- Standardized publication dates
- Validated date parsing
- Checked dataset quality and article lengths
- Retained natural French text for transformer-based embeddings

### Cleaning Results

| Step | Removed |
|--------|----------|
| Missing title/body | 0 |
| Duplicate URLs | 0 |
| Duplicate titles | 1 |
| Non-news pages | 6 |
| Articles shorter than 500 characters | 31 |
| Invalid dates | 0 |

### Final Dataset

```text
2123 articles
```

---

## Dataset Statistics

### Article Length

```text
Count : 2123
Mean  : 2900 characters
Median: 2260 characters
Min   : 501 characters
Max   : 28350 characters
```

### Most Frequent Categories

- Belgique
- Monde
- Bruxelles
- Journal du Rock
- Diables Rouges
- Jeux vidéo
- Hainaut
- Cyclisme
- Classic 21
- Formule 1

---

## Data Quality Checks

The dataset was inspected for common boilerplate and template content:

- Lire aussi
- Newsletter
- Publicité
- Cookie
- Belga
- Abonnez

Occurrences were found to be very rare and mostly appeared in legitimate article content, so they were not removed.

---

## Current Progress

### Completed

- [x] Repository setup
- [x] Virtual environment setup
- [x] RTBF article scraper
- [x] Metadata extraction
- [x] Full article extraction via JSON-LD
- [x] Dataset creation
- [x] Dataset cleaning and validation
- [x] 2,123 clean news articles collected

### In Progress

- [ ] Sentence embeddings generation
- [ ] Topic modeling with BERTopic
- [ ] Article clustering
- [ ] Topic visualization

### Planned

- [ ] Interactive Streamlit dashboard
- [ ] Deployment
- [ ] Azure architecture documentation
- [ ] Business presentation

---

## Next Steps

1. Generate multilingual article embeddings using Sentence Transformers.
2. Apply BERTopic to discover major news themes.
3. Cluster semantically similar articles.
4. Create visualizations for topics and content clusters.
5. Develop and deploy an interactive Streamlit dashboard.
6. Present key editorial insights and coverage trends.

---

## Status

✅ Dataset acquisition complete

✅ Preprocessing complete

✅ Quality validation complete

🔄 Topic modeling in progress

🔄 Clustering in progress

⏳ Dashboard and deployment pending



## Topic Modeling Results

BERTopic was applied to 2,123 cleaned RTBF articles using multilingual sentence embeddings.

Results:

- 37 semantic topics identified
- Articles grouped by meaning rather than website categories
- Topics discovered automatically from article content

Examples of topics:

- Film & Television
- Rock & Music
- Cycling
- Education
- Government & Budget
- Ukraine War
- Video Games
- Artificial Intelligence
- Health & Cancer
- Formula 1
- Gaza Conflict
- Public Transport
- Weather