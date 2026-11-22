"""Официальный Instagram API with Facebook Login, никаких ботов/паролей Instagram."""
from __future__ import annotations
import os
import time
from pathlib import Path
import requests
import cloudinary
import cloudinary.uploader


def check_ready():
    needed = ("CLOUDINARY_URL", "META_ACCESS_TOKEN", "IG_USER_ID")
    missing = [x for x in needed if not os.getenv(x)]
    if missing:
        raise RuntimeError("Для публикации нужны секреты: " + ", ".join(missing))


def upload(path: Path):
    kind = "video" if path.suffix.lower() == ".mp4" else "image"
    response = cloudinary.uploader.upload(str(path), resource_type=kind,
                                          folder="instagram_ai_agent", overwrite=False)
    url = response["secure_url"]
    if not url.startswith("https://"):
        raise RuntimeError("Cloudinary did not return HTTPS URL")
    return url


def graph(method: str, endpoint: str, params: dict | None = None):
    version = os.getenv("META_GRAPH_VERSION", "v25.0")
    url = f"https://graph.facebook.com/{version}/{endpoint.lstrip('/')}"
    params = dict(params or {})
    # Запросы через заголовок, токен не появляется в URL или логе.
    headers = {"Authorization": f"Bearer {os.environ['META_ACCESS_TOKEN']}"}
    r = requests.request(method, url, headers=headers, data=params if method == "POST" else None,
                         params=params if method == "GET" else None, timeout=40)
    if not r.ok:
        try:
            msg = r.json().get("error", {}).get("message", "Unknown Meta error")
        except ValueError:
            msg = r.text[:150]
        raise RuntimeError(f"Meta API HTTP {r.status_code}: {msg}")
    return r.json()


def publish_one(kind: str, local_file: Path, caption: str):
    ig_id = os.environ["IG_USER_ID"]
    media_url = upload(local_file)
    if kind == "reel":
        params = {"media_type": "REELS", "video_url": media_url,
                  "caption": caption, "share_to_feed": "true"}
    elif kind == "story":
        params = {"media_type": "STORIES", "image_url": media_url}
    elif kind == "post":
        params = {"image_url": media_url, "caption": caption}
    else:
        raise ValueError(kind)
    container = graph("POST", f"{ig_id}/media", params)["id"]
    # Для video и Stories ждём готовность, также удобно для фото.
    for _ in range(15):
        status = graph("GET", container, {"fields": "status_code"}).get("status_code")
        if status == "FINISHED":
            break
        if status in {"ERROR", "EXPIRED"}:
            raise RuntimeError(f"Container {kind} status: {status}")
        time.sleep(10)
    else:
        raise RuntimeError(f"Container {kind} not FINISHED in time")
    # Не повторяем media_publish автоматически в случае неоднозначного ответа —
    # иначе иногда получается дублирование опубликованного контента.
    result = graph("POST", f"{ig_id}/media_publish", {"creation_id": container})
    return result["id"]
