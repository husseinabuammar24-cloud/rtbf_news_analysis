# RTBF News Analysis

This project collects RTBF news articles, cleans and validates them, generates multilingual sentence embeddings, and applies BERTopic to discover the main themes discussed in the corpus.

The work is now organized around a complete data pipeline: scraping, cleaning, embedding, topic modeling, and visualization of results.

## Current status

Completed ✅
- RTBF article URL collection and raw dataset creation
- Article metadata extraction and full content parsing
- Dataset cleaning and validation
- Multilingual embedding generation with SentenceTransformers
- BERTopic topic modeling on the cleaned corpus
- Topic summaries and interactive HTML visualizations exported to the outputs folder

In progress / planned 🔄
- Interactive dashboard for exploring topics and articles
- Deeper editorial interpretation of the discovered themes
- Deployment and presentation layer

## Dataset overview

### Final cleaned dataset
- 2,123 valid articles retained after cleaning
- Coverage period: 2020-10-01 to 2026-10-09
- Average article length: approximately 2,900 characters
- Most articles are written in French and cover a broad range of RTBF editorial themes

### Cleaning checks applied
- Removed missing title/body rows
- Removed duplicate URLs and duplicate titles
- Filtered non-news pages and promo/service pages
- Removed very short articles (< 500 characters)
- Parsed and validated publication dates
- Kept clean text fields for transformer-based embedding generation

## Project pipeline

1. Data collection
   - Crawl and store RTBF article URLs
   - Parse article metadata, title, date, category, body, and length

2. Data cleaning
   - Validate article structure
   - Remove duplicates and non-news entries
   - Normalize dates and produce a clean dataset

3. Embedding generation
   - Use a multilingual sentence transformer model
   - Create numerical vector representations for each article

4. Topic modeling
   - Apply BERTopic with UMAP + HDBSCAN
   - Discover semantic clusters without relying on RTBF category labels

5. Visualization
   - Export topic summaries and interactive HTML plots
   - Inspect topic distributions and document embeddings

## Repository structure

```text
rtbf_news_analysis/
├── data/
│   ├── raw/
│   │   ├── article_urls.txt
│   │   ├── articles.csv
│   │   └── sample_article.csv
│   └── processed/
│       ├── articles_clean.csv
│       └── embeddings.npy
├── outputs/
│   ├── topic_info.csv
│   ├── topics_barchart.html
│   ├── topics_map.html
│   ├── topics_hierarchy.html
│   ├── topics_over_time.html
│   └── documents_map.html
├── src/
│   ├── article_parser.py
│   ├── build_dataset.py
│   ├── clustering.py
│   ├── embeddings.py
│   ├── main.py
│   ├── preprocessing.py
│   ├── scraper.py
│   ├── topic_modeling.py
│   └── archive.py
├── dashboard/
│   └── app.py
├── notebooks/
├── tests/
├── README.md
├── requirements.txt
├── image.png
├── image-1.png
└── .gitignore
```

## Technical stack

### Data collection and parsing
- Python
- Requests
- BeautifulSoup
- JSON-LD extraction

### NLP / machine learning
- SentenceTransformers
- BERTopic
- UMAP
- HDBSCAN
- scikit-learn
- Pandas / NumPy

### Visualization
- Plotly
- HTML exports from BERTopic

## Topic modeling results

The BERTopic model was applied to the cleaned dataset using multilingual embeddings. The result is a semantic clustering of 2,123 RTBF articles into 37 meaningful topics.

### Top discovered themes
- Film, series, and culture
- Rock, music, and artists
- Cycling and sport events
- Education and student life
- Football and domestic sport coverage
- Court cases and public affairs
- Ukraine war and geopolitical news
- Video games and gaming culture
- Government, budget, and public finance
- Weather and climate
- AI and technology
- Health and cancer-related coverage
- Formula 1 and motorsport
- Transport, urban projects, and public services

### Example output

The model produced structured topic information in `outputs/topic_info.csv`, including:
- topic id
- article count per topic
- generated topic label
- representative documents
- topic representation words

The outputs folder also contains interactive visualizations such as:
- `topics_barchart.html`
- `topics_map.html`
- `topics_hierarchy.html`
- `topics_over_time.html`
- `documents_map.html`

## Key numbers

```text
Clean articles: 2123
Topics found: 37
Outliers: 1
Date range: 2020-10-01 to 2026-10-09
```

## How to run the pipeline

From the project root:

```bash
source nlp-env/bin/activate

python src/main.py
python src/preprocessing.py
python src/embeddings.py
python src/topic_modeling.py
```

This reproduces the core workflow from raw article extraction to topic modeling.

## What remains

The core analysis pipeline has been completed. The remaining work is mainly presentation and exploitation:
- build an interactive dashboard
- improve topic interpretation and storytelling
- prepare a final business or research presentation
- optionally deploy the dashboard in a web environment

## Summary

The project has already moved beyond data collection and into actual semantic analysis. The current state is not just a scraper: it is a working news-analysis pipeline with a cleaned dataset, embeddings, and BERTopic outputs that reveal the main editorial themes in RTBF coverage.
