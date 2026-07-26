import uuid

import httpx
from bs4 import BeautifulSoup

from app.ingestion.parser import clean_text

REQUEST_TIMEOUT_SECONDS = 10.0
MIN_SECTION_TEXT_LENGTH = 10


def crawl_portfolio(portfolio_url: str) -> list[dict]:
    portfolio_url = portfolio_url.rstrip("/")
    response = httpx.get(portfolio_url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    sections = []
    for section in soup.find_all("section", id=True):
        text = clean_text(section.get_text(separator="\n", strip=True))
        if len(text) < MIN_SECTION_TEXT_LENGTH:
            continue

        heading = section.find(["h1", "h2", "h3"])
        title = heading.get_text(strip=True) if heading else section["id"]
        url = f"{portfolio_url}#{section['id']}"

        sections.append(
            {
                "document_id": uuid.uuid5(uuid.NAMESPACE_URL, url).hex,
                "url": url,
                "title": title,
                "text": text,
            }
        )
    return sections
