import httpx

from app.ingestion import portfolio_crawler

PORTFOLIO_HTML = """<html><head><title>Portfolio</title></head>
<body>
<section id="about"><h2>About</h2><p>자기소개 문단입니다.</p></section>
<section id="projects"><h2>Selected Projects</h2><p>프로젝트 설명입니다.</p></section>
<section id="empty"><h2>Empty</h2></section>
<section><p>id가 없는 섹션이라 제외되어야 함.</p></section>
</body></html>"""


def test_crawl_portfolio_extracts_sections_with_id_and_content(monkeypatch):
    def fake_get(url, timeout=None):
        assert url == "https://example.github.io"
        return httpx.Response(200, text=PORTFOLIO_HTML, request=httpx.Request("GET", url))

    monkeypatch.setattr(portfolio_crawler.httpx, "get", fake_get)

    sections = portfolio_crawler.crawl_portfolio("https://example.github.io/")

    assert [s["title"] for s in sections] == ["About", "Selected Projects"]
    assert sections[0]["url"] == "https://example.github.io#about"
    assert sections[0]["text"] == "About\n자기소개 문단입니다."
    assert sections[0]["document_id"]
    assert sections[1]["url"] == "https://example.github.io#projects"
