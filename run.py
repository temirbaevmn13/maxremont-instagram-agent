"""Точка входа. По умолчанию только черновики; публикация включается переменной."""
from __future__ import annotations
import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from agent import generate, read_json
from render import render
from state import load, save

ROOT = Path(__file__).resolve().parent


def main():
    day = datetime.now(ZoneInfo("Asia/Bishkek")).date()
    selected_day = os.getenv("TEST_DATE", "").strip()
    if selected_day:
        day = datetime.strptime(selected_day, "%Y-%m-%d").date()
    daystr = day.isoformat()
    cfg = read_json("config.json")
    content, source = generate(day)
    out = ROOT / "output" / daystr
    # Вт / Чт / Сб: дополнительный статический пост.
    make_post = day.weekday() in (1, 3, 5)
    kind = os.getenv("CONTENT_KIND", "all").strip().lower()
    if kind not in {"all", "reel", "story", "post"}:
        raise ValueError("CONTENT_KIND должен быть all, reel, story или post")
    paths = render(content, cfg["company_name"], out, make_post, kind)
    (out / "content.json").write_text(json.dumps({"source": source, **content},
                                       ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Подготовлены материалы: {out}. Источник текста: {source}")
    enabled = os.getenv("PUBLISH_ENABLED", "false").lower() == "true"
    if not enabled:
        print("РЕЖИМ ЧЕРНОВИКОВ. Для публикации установите PUBLISH_ENABLED=true в GitHub Variables.")
        return
    if selected_day:
        raise RuntimeError("TEST_DATE запрещён при включённой публикации: защита от случайных повторов")
    from publish import check_ready, publish_one
    check_ready()
    old, sha = load(daystr)
    for kind in ("reel", "story", "post"):
        path = paths.get(kind)
        if path is None or old.get(kind):
            print(f"Пропущено: {kind} (нет файла или уже опубликовано)")
            continue
        print(f"Отправка: {kind}")
        media_id = publish_one(kind, path, content["caption"])
        old[kind] = {"media_id": media_id, "date": daystr}
        sha = save(daystr, old, sha)
        print(f"Опубликовано: {kind}, media id {media_id}")


if __name__ == "__main__":
    main()
