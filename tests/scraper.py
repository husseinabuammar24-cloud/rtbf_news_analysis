from playwright.sync_api import sync_playwright


def get_page_title(url: str):

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=False)

        page = browser.new_page()

        page.goto(url)

        title = page.title()

        browser.close()

        return title


if __name__ == "__main__":

    url = "https://www.rtbf.be/article/elon-musk-trillionnaire-etes-vous-actionnaire-de-spacex-sans-le-savoir-11796242"

    print(get_page_title(url))