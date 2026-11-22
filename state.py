"""Идемпотентность: фиксируем успешные публикации в state/YYYY-MM-DD.json."""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent


def github_params(day: str):
    repo = os.getenv("GITHUB_REPOSITORY", "")
    token = os.getenv("GH_STATE_TOKEN", "")
    if repo and token:
        url = f"https://api.github.com/repos/{repo}/contents/state/{day}.json"
        headers = {"Authorization": f"Bearer {token}",
                   "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        return url, headers
    return None


def load(day: str):
    remote = github_params(day)
    if remote:
        url, headers = remote
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 404:
            return {}, None
        r.raise_for_status()
        data = r.json()
        return json.loads(base64.b64decode(data["content"]).decode("utf-8")), data["sha"]
    path = ROOT / "state" / f"{day}.json"
    return (json.loads(path.read_text(encoding="utf-8")), None) if path.exists() else ({}, None)


def save(day: str, status: dict, sha: str | None):
    remote = github_params(day)
    payload = json.dumps(status, indent=2, ensure_ascii=False)
    if remote:
        url, headers = remote
        data = {"message": f"record Instagram publishing {day}",
                "content": base64.b64encode(payload.encode()).decode(), "branch": os.getenv("GITHUB_REF_NAME", "main")}
        if sha:
            data["sha"] = sha
        r = requests.put(url, headers=headers, json=data, timeout=30)
        r.raise_for_status()
        return r.json()["content"]["sha"]
    path = ROOT / "state" / f"{day}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    return None
