"""Helpers to extract structured metadata from RTBF article pages.

The scraper relies on the JSON-LD ``NewsArticle`` block embedded in each page.
This module normalizes the HTML and text extracted from those pages before the
rest of the pipeline stores them in CSV files.
"""

import csv
import html
import json
import re
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (BeCode student project; contact: your@email)"
}


def clean_text(value: Any) -> str:
    """Normalize whitespace and HTML entities in a text-like value."""
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def clean_author(raw: str) -> str:
    """Format author names from RTBF JSON-LD, including trailing numeric suffixes."""
    authors: list[str] = []
    for handle in raw.split(","):
        name = handle.strip().lstrip("@")
        name = re.sub(r"-\d+$", "", name)
        name = name.replace("-", " ").title()
        if name:
            authors.append(name)
    return ", ".join(authors)


def normalize_names(value: Any) -> str:
    """Turn author metadata into a readable string."""
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, dict):
        return clean_text(value.get("name", ""))
    if isinstance(value, list):
        return ", ".join(part for part in (normalize_names(item) for item in value) if part)
    return ""


def get_page(url: str) -> BeautifulSoup:
    """Return a parsed HTML page from a RTBF article URL."""
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def get_news_article_node(soup: BeautifulSoup) -> dict[str, Any] | None:
    """Extract the NewsArticle JSON-LD node, if present."""
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "NewsArticle":
                return item
    return None


def get_category(soup: BeautifulSoup) -> str:
    """Find the RTBF dossier category for the article."""
    link = soup.select_one('main p.uppercase a[href^="/dossier/"]')
    return clean_text(link.get_text()) if link else ""


def get_article_type(soup: BeautifulSoup) -> str:
    """Read the article type encoded in the RTBF engagement metadata."""
    element = soup.select_one("[data-elb-engagement]")
    if not element:
        return ""
    match = re.search(r"article_type:(\w+)", element["data-elb-engagement"])
    return match.group(1) if match else ""


def get_lead(soup: BeautifulSoup) -> str:
    """Retrieve the lead paragraph placed under the article title."""
    heading = soup.select_one('h1[data-testid="title"]')
    if not heading:
        return ""
    paragraph = heading.find_next_sibling("p")
    if paragraph:
        return clean_text(paragraph.get_text(" ", strip=True))
    return ""


def extract_article(url: str) -> dict[str, Any] | None:
    """Return a normalized article record for a RTBF URL."""
    soup = get_page(url)
    item = get_news_article_node(soup)
    if item is None:
        return None

    lead = get_lead(soup)
    body = clean_text(item.get("articleBody"))
    full_text = f"{lead}\n{body}".strip() if lead else body

    return {
        "url": url,
        "title": clean_text(item.get("headline")).removesuffix(" - RTBF Actus"),
        "published_date": item.get("datePublished"),
        "author": clean_author(normalize_names(item.get("author")).removeprefix("Par ")),
        "category": get_category(soup),
        "article_type": get_article_type(soup),
        "lead": lead,
        "article_body": full_text,
        "article_length": len(full_text),
    }


if __name__ == "__main__":
    SAMPLE_URL = (
        "https://www.rtbf.be/article/execution-ratee-aux-etats-unis-christa-pike-"
        "a-recommence-a-marcher-selon-son-avocat-11797123"
    )
    article = extract_article(SAMPLE_URL)

    if article is None:
        print(f"No NewsArticle JSON-LD found for: {SAMPLE_URL}")
    else:
        print("Extracted article data successfully.")

        out = Path("data/raw/sample_article.csv")
        out.parent.mkdir(parents=True, exist_ok=True)

        with out.open("w", newline="", encoding="utf-8") as file_obj:
            writer = csv.DictWriter(file_obj, fieldnames=article.keys())
            writer.writeheader()
            writer.writerow(article)

        print(f"Saved sample article to {out}")
