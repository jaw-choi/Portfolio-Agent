import base64

import httpx

from app.ingestion import github_crawler


def _response(url, json_body=None, status_code=200):
    return httpx.Response(
        status_code,
        json=json_body,
        request=httpx.Request("GET", url),
    )


def test_discover_repos_excludes_forks(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        assert url == f"{github_crawler.GITHUB_API_BASE}/users/jaw-choi/repos"
        return _response(
            url,
            json_body=[
                {"name": "own-repo", "fork": False, "full_name": "jaw-choi/own-repo",
                 "html_url": "https://github.com/jaw-choi/own-repo"},
                {"name": "forked-repo", "fork": True, "full_name": "jaw-choi/forked-repo",
                 "html_url": "https://github.com/jaw-choi/forked-repo"},
            ],
        )

    monkeypatch.setattr(github_crawler.httpx, "get", fake_get)

    repos = github_crawler.discover_repos("jaw-choi")

    assert [r["name"] for r in repos] == ["own-repo"]


def test_fetch_readme_decodes_base64_content(monkeypatch):
    repo = {
        "name": "own-repo",
        "full_name": "jaw-choi/own-repo",
        "html_url": "https://github.com/jaw-choi/own-repo",
    }
    encoded = base64.b64encode("# 제목\n\n내용입니다.".encode("utf-8")).decode("ascii")

    def fake_get(url, headers=None, timeout=None):
        assert url == f"{github_crawler.GITHUB_API_BASE}/repos/jaw-choi/own-repo/readme"
        return _response(url, json_body={"content": encoded})

    monkeypatch.setattr(github_crawler.httpx, "get", fake_get)

    result = github_crawler.fetch_readme(repo)

    assert result["title"] == "own-repo"
    assert result["url"] == "https://github.com/jaw-choi/own-repo"
    assert result["text"] == "# 제목\n내용입니다."
    assert result["document_id"]


def test_fetch_readme_returns_none_on_404(monkeypatch):
    repo = {
        "name": "no-readme",
        "full_name": "jaw-choi/no-readme",
        "html_url": "https://github.com/jaw-choi/no-readme",
    }

    def fake_get(url, headers=None, timeout=None):
        return _response(url, status_code=404, json_body={"message": "Not Found"})

    monkeypatch.setattr(github_crawler.httpx, "get", fake_get)

    assert github_crawler.fetch_readme(repo) is None


def test_crawl_github_collects_documents_and_skips_failures(monkeypatch):
    repos = [
        {"name": "repo1", "full_name": "jaw-choi/repo1", "html_url": "https://github.com/jaw-choi/repo1"},
        {"name": "repo2", "full_name": "jaw-choi/repo2", "html_url": "https://github.com/jaw-choi/repo2"},
    ]
    monkeypatch.setattr(github_crawler, "discover_repos", lambda username: repos)

    def fake_fetch_readme(repo):
        if repo["name"] == "repo2":
            raise httpx.HTTPError("boom")
        return {"document_id": "doc1", "url": repo["html_url"], "title": repo["name"], "text": "hello"}

    monkeypatch.setattr(github_crawler, "fetch_readme", fake_fetch_readme)

    result = github_crawler.crawl_github("jaw-choi")

    assert len(result["documents"]) == 1
    assert result["documents"][0]["title"] == "repo1"
    assert len(result["failed"]) == 1
    assert result["failed"][0]["url"] == "https://github.com/jaw-choi/repo2"
