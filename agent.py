"""Генерация контента: Gemini free tier при наличии ключа, иначе локальные темы."""
from __future__ import annotations
import json
import os
import re
from datetime import date
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent


def read_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def make_fallback(topic: dict, cfg: dict):
    tips = topic["tips"][:3]
    cta = cfg.get("contact", "Напишите нам в Direct")
    return {
        "title": topic["title"],
        "tips": tips,
        "cta": cta,
        "caption": (
            f"{topic['title']}\n\n" + "\n".join(f"✅ {s}" for s in tips) +
            f"\n\n{cta}\n\n#ремонтбишкек #отделкабишкек #ремонтквартир"
        ),
        "story_text": f"{topic['title']}\n\n{tips[0]}\n\n{cta}",
        "post_text": f"{topic['title']}\n\n{tips[0]}",
    }


def generate(day: date):
    cfg = read_json("config.json")
    topics = read_json("topics.json")
    topic = topics[day.toordinal() % len(topics)]
    fallback = make_fallback(topic, cfg)
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return fallback, "templates"
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    # Ключ и авторизация передаются через заголовок, не в URL.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    instructions = {
        "role": "SMM-редактор небольшого бизнеса",
        "brand": cfg,
        "topic": topic,
        "rules": [
            "Пиши по-русски коротко и понятно",
            "Не выдумывай цены, отзывы, клиентов, сертификаты, адреса, опыт, скидки и результаты работ",
            "Не обещай гарантированный эффект, набор подписчиков или результаты ремонта",
            "Верни только JSON с title(str), tips(array of 3 short strings), cta(str), caption(str), story_text(str), post_text(str)",
            "Тематика: фактические советы по услугам, без вымышленных кейсов"
        ]
    }
    payload = {"contents": [{"parts": [{"text": json.dumps(instructions, ensure_ascii=False)}]}],
               "generationConfig": {"responseMimeType": "application/json", "temperature": 0.6}}
    try:
        response = requests.post(url, json=payload, headers={"x-goog-api-key": key}, timeout=45)
        response.raise_for_status()
        raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
        data = json.loads(raw)
        if not all(isinstance(data.get(k), str) and data[k].strip() for k in
                   ("title", "cta", "caption", "story_text", "post_text")):
            raise ValueError("Gemini returned missing fields")
        if not isinstance(data.get("tips"), list) or len(data["tips"]) < 3 or not all(
            isinstance(x, str) and x.strip() for x in data["tips"][:3]
        ):
            raise ValueError("Gemini returned invalid tips")
        # Ограничиваем размеры, чтобы контент помещался в шаблоны.
        data["title"] = data["title"][:100]
        data["tips"] = [x[:120] for x in data["tips"][:3]]
        data["cta"] = data["cta"][:110]
        data["caption"] = data["caption"][:1800]
        data["story_text"] = data["story_text"][:240]
        data["post_text"] = data["post_text"][:240]
        return data, "gemini"
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError) as e:
        print(f"Предупреждение: Gemini недоступен ({str(e)[:180]}). Используем шаблоны.")
        return fallback, "templates"
