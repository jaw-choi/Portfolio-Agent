import base64
import uuid

import httpx

from app.ingestion.parser import clean_text

REQUEST_TIMEOUT_SECONDS = 10.0
GITHUB_API_BASE = "https://api.github.com"
GITHUB_ACCEPT_HEADER = {"Accept": "application/vnd.github+json"}


def discover_repos(username: str) -> list[dict]:
    response = httpx.get(
        f"{GITHUB_API_BASE}/users/{username}/repos",
        params={"per_page": 100, "type": "owner"},
        headers=GITHUB_ACCEPT_HEADER,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return [repo for repo in response.json() if not repo["fork"]]


def fetch_readme(repo: dict) -> dict | None:
    response = httpx.get(
        f"{GITHUB_API_BASE}/repos/{repo['full_name']}/readme",
        headers=GITHUB_ACCEPT_HEADER,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    if response.status_code == 404:
        return None
    response.raise_for_status()

    data = response.json()
    content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    text = clean_text(content)
    if not text:
        return None

    url = repo["html_url"]
    return {
        "document_id": uuid.uuid5(uuid.NAMESPACE_URL, url).hex,
        "url": url,
        "title": repo["name"],
        "text": text,
    }


def crawl_github(username: str) -> dict:
    repos = discover_repos(username)
    documents = []
    failed = []
    for repo in repos:
        try:
            result = fetch_readme(repo)
        except httpx.HTTPError as exc:
            failed.append({"url": repo["html_url"], "error": str(exc)})
            continue

        if result:
            documents.append(result)

    return {"documents": documents, "failed": failed}
