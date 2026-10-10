'''
Build dataset: convert json file into csv file
'''
import pandas as pd

from article_parser import extract_article


articles = []

for url in urls:

    try:

        article = extract_article(url)

        if article:
            articles.append(article)

            print(
                f"✓ {article['title']}"
            )

    except Exception as e:

        print(
            f"Error: {url}"
        )

        print(e)



df = pd.DataFrame(articles)

df.to_csv(
"data/raw/articles.csv",
index=False
)

print(df.shape)