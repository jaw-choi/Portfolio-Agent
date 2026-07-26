import time
import uuid
import xml.etree.ElementTree as ElementTree

import httpx
from bs4 import BeautifulSoup

from app.ingestion.parser import clean_text

REQUEST_DELAY_SECONDS = 0.5
CONTENT_CLASS = "tt_article_useless_p_margin"
REQUEST_TIMEOUT_SECONDS = 10.0
SITEMAP_NAMESPACE = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


def discover_post_urls(blog_url: str) -> list[str]:
    blog_url = blog_url.rstrip("/")
    response = httpx.get(f"{blog_url}/sitemap.xml", timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    root = ElementTree.fromstring(response.text)
    urls = []
    for loc in root.iterfind(".//sm:loc", SITEMAP_NAMESPACE):
        url = (loc.text or "").strip()
        path = url.removeprefix(blog_url).strip("/")
        if path.isdigit():
            urls.append(url)
    return urls


def fetch_post(url: str) -> dict:
    response = httpx.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else url

    content = soup.find("div", class_=CONTENT_CLASS)
    text = clean_text(content.get_text(separator="\n", strip=True)) if content else ""

    return {
        "document_id": uuid.uuid5(uuid.NAMESPACE_URL, url).hex,
        "url": url,
        "title": title,
        "text": text,
    }


def crawl_blog(blog_url: str) -> dict:
    posts = []
    failed = []
    urls = discover_post_urls(blog_url)
    for index, url in enumerate(urls):
        try:
            posts.append(fetch_post(url))
        except httpx.HTTPError as exc:
            failed.append({"url": url, "error": str(exc)})

        if index < len(urls) - 1:
            time.sleep(REQUEST_DELAY_SECONDS)

    return {"posts": posts, "failed": failed}
