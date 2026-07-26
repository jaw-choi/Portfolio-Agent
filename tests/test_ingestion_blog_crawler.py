import httpx
import pytest

from app.ingestion import blog_crawler

SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.tistory.com</loc></url>
  <url><loc>https://example.tistory.com/category</loc></url>
  <url><loc>https://example.tistory.com/guestbook</loc></url>
  <url><loc>https://example.tistory.com/1</loc></url>
  <url><loc>https://example.tistory.com/2</loc></url>
</urlset>
"""

POST_HTML = """<html><head><title>테스트 글 제목</title></head>
<body><div class="tt_article_useless_p_margin contents_style">
<h1>제목</h1>
<p>본문 내용입니다.</p>
</div></body></html>"""


def test_discover_post_urls_filters_non_post_pages(monkeypatch):
    def fake_get(url, timeout=None):
        assert url == "https://example.tistory.com/sitemap.xml"
        return httpx.Response(200, text=SITEMAP_XML, request=httpx.Request("GET", url))

    monkeypatch.setattr(blog_crawler.httpx, "get", fake_get)

    urls = blog_crawler.discover_post_urls("https://example.tistory.com")

    assert urls == ["https://example.tistory.com/1", "https://example.tistory.com/2"]


def test_fetch_post_extracts_title_and_text(monkeypatch):
    def fake_get(url, timeout=None):
        return httpx.Response(200, text=POST_HTML, request=httpx.Request("GET", url))

    monkeypatch.setattr(blog_crawler.httpx, "get", fake_get)

    post = blog_crawler.fetch_post("https://example.tistory.com/1")

    assert post["url"] == "https://example.tistory.com/1"
    assert post["title"] == "테스트 글 제목"
    assert post["text"] == "제목\n본문 내용입니다."
    assert post["document_id"]


def test_crawl_blog_collects_posts_and_skips_failures(monkeypatch):
    monkeypatch.setattr(blog_crawler.time, "sleep", lambda _: None)
    monkeypatch.setattr(
        blog_crawler,
        "discover_post_urls",
        lambda blog_url: ["https://example.tistory.com/1", "https://example.tistory.com/2"],
    )

    def fake_fetch_post(url):
        if url.endswith("/2"):
            raise httpx.HTTPError("boom")
        return {"document_id": "doc1", "url": url, "title": "t", "text": "hello"}

    monkeypatch.setattr(blog_crawler, "fetch_post", fake_fetch_post)

    result = blog_crawler.crawl_blog("https://example.tistory.com")

    assert len(result["posts"]) == 1
    assert result["posts"][0]["url"] == "https://example.tistory.com/1"
    assert len(result["failed"]) == 1
    assert result["failed"][0]["url"] == "https://example.tistory.com/2"
