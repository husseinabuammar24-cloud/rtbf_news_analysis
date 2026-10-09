'''
Parse each article 
'''

import html
import json
import re

import requests
from bs4 import BeautifulSoup

# 1. Imported the csv module
import csv

HEADERS = {"User-Agent": "Mozilla/5.0 (BeCode student project; contact: your@email)"}


def clean(text) -> str:
    if not isinstance(text, str):
        return ""
    return re.sub(r"\s+", " ", html.unescape(text)).strip()

def clean_author(raw: str) -> str:
    out = []
    for handle in raw.split(","):
        h = handle.strip().lstrip("@")
        h = re.sub(r"-\d+$", "", h)       # drop numeric suffix: belga-2 -> belga
        h = h.replace("-", " ").title()   # amid-faljaoui -> Amid Faljaoui
        if h:
            out.append(h)
    return ", ".join(out)

def names(value) -> str:
    if isinstance(value, str):
        return clean(value)
    if isinstance(value, dict):
        return clean(value.get("name", ""))
    if isinstance(value, list):
        return ", ".join(n for n in (names(v) for v in value) if n)
    return ""


def get_page(url: str) -> BeautifulSoup:
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def get_news_article_node(soup: BeautifulSoup) -> dict | None:
    for s in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(s.string or "")
        except json.JSONDecodeError:
            continue
        for item in (data if isinstance(data, list) else [data]):
            if isinstance(item, dict) and item.get("@type") == "NewsArticle":
                return item
    return None


def get_category(soup: BeautifulSoup) -> str:
    a = soup.select_one('main p.uppercase a[href^="/dossier/"]')
    return clean(a.get_text()) if a else ""


def get_article_type(soup: BeautifulSoup) -> str:
    el = soup.select_one("[data-elb-engagement]")
    if not el:
        return ""
    m = re.search(r"article_type:(\w+)", el["data-elb-engagement"])
    return m.group(1) if m else ""

def get_lead(soup: BeautifulSoup) -> str:
    h1 = soup.select_one('h1[data-testid="title"]')
    if h1:
        p = h1.find_next_sibling("p")
        if p:
            return clean(p.get_text(" ", strip=True))
    return ""
    
def extract_article(url: str) -> dict | None:
    soup = get_page(url)
    item = get_news_article_node(soup)
    if item is None:
        return None

    lead = get_lead(soup)
    body = clean(item.get("articleBody"))
    full_text = f"{lead}\n{body}".strip() if lead else body

    return {
        "url": url,
        "title": clean(item.get("headline")).removesuffix(" - RTBF Actus"),
        "published_date": item.get("datePublished"),
        "author": clean_author(names(item.get("author")).removeprefix("Par ")),
        "category": get_category(soup),
        "article_type": get_article_type(soup),
        "lead": lead,
        "article_body": full_text,
        "article_length": len(full_text),
    }


if __name__ == "__main__":
    from pathlib import Path

    url = "https://www.rtbf.be/article/execution-ratee-aux-etats-unis-christa-pike-a-recommence-a-marcher-selon-son-avocat-11797123"
    article = extract_article(url)

    if article is None:
        print("No NewsArticle JSON-LD found:", url)
    else:
        # Optional: keeps the terminal visualization clean
        print("Extracted article data successfully.")

        # 2. Changed output path to point to a .csv file
        out = Path("data/raw/sample_article.csv")
        out.parent.mkdir(parents=True, exist_ok=True)
        
        # 3. Use csv.DictWriter to safely handle headers and text contents
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=article.keys())
            writer.writeheader()  # Writes columns: url, title, published_date, etc.
            writer.writerow(article)
            
        print(f"\nSaved to {out}")
