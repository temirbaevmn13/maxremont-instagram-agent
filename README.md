# MAX REMONT BISHKEK — бесплатный Instagram-агент (без рекламы)

**Что умеет:** каждый день собирать текстовый 15-секундный Reels, Story и по Вт/Чт/Сб — пост. При доступном бесплатном Gemini API пишет оригинальные тексты, без него использует 27 проверяемых тем. Монтаж: Pillow + FFmpeg; медиа автоматически формируются без оплаты. Включаемая отдельно публикация через официальный Meta Instagram API with Facebook Login и бесплатный лимит Cloudinary. Платную рекламу проект **никогда не запускает**.

## 0. Важные ограничения

- Бесплатно — если **есть доступ** к бесплатным лимитам GitHub Actions, Gemini и Cloudinary. Квоты и условия могут меняться. Код не производит платных вызовов намеренно, но следи за своими тарифами и не подключай оплачиваемый API-проект.
- Без GEMINI_API_KEY видео создаётся из **готовых шаблонов**: это автоматизация, но не генеративный ИИ.
- Видео — типографические карточки и субтитры, без автоматически генерируемых съёмочных сцен или голоса. Новые реалистичные видеосцены без твоих материалов бесплатно и без лимитов не обещаем.
- Для `PUBLISH_ENABLED=true` обязательно настроить **Instagram Business**, Meta Developer App, разрешение `instagram_content_publish`, страницу Facebook, токен Meta и Cloudinary. Для других аккаунтов может потребоваться проверка приложения Meta.
- GitHub Actions по cron может запускаться с задержкой, а публичные репозитории без активности 60 дней могут отключать scheduled workflows.
- Долгоживущий токен Meta тоже имеет срок: проверь механизм продления в своей конфигурации. Полная вечная автономия без обслуживания не гарантируется.
- Не добавляй реальные фото заказчиков без разрешения. Система не выдумывает реализованные проекты, достижения и отзывы.

## 1. Запусти пробный режим за 5 шагов

1. Создай новый **публичный** репозиторий GitHub `maxremont-instagram-agent`. Публичный нужен для бесплатных стандартных GitHub-hosted Actions. Если материалы приватные, изучи лимиты приватных репозиториев или запусти всё локально.
2. Загрузи в него **содержимое архива**, сохранив папку `.github/workflows/daily.yml`. Она начинается с точки и обычно скрыта в Windows — не потеряй её.
3. Открой `config.json`, проверь готовые данные MAX REMONT в `config.json`; телефон при необходимости поправь.
4. На странице GitHub открой **Actions → MAX REMONT — Instagram без рекламы → Run workflow**.
5. После выполнения открой запуск → **Artifacts → maxremont-content-...**. В архиве готовые `reel.mp4`, `story.jpg`, иногда `post.jpg`, а также `content.json`.

По умолчанию **ничего не публикуется**: `PUBLISH_ENABLED=false`.

## 2. Включи настоящую ИИ-генерацию бесплатно (если доступен тариф)

1. Открой https://aistudio.google.com/ и создай API-ключ Gemini в проекте с доступным **бесплатным тарифом**.
2. GitHub репозиторий → **Settings → Secrets and variables → Actions → Secrets → New repository secret**.
3. Добавь `GEMINI_API_KEY`. По умолчанию модель `gemini-2.5-flash-lite`; если бесплатная квота недоступна, измени `GEMINI_MODEL` в `.github/workflows/daily.yml` на модель, для которой у тебя есть бесплатная квота.
4. Проверь `content.json`: `source` должен быть `gemini`. Если `templates`, генерация ИИ не сработала, проект использовал бесплатный запасной вариант.

## 3. Подготовь официальный Instagram API

Подробные инструкции Meta: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-facebook-login/content-publishing/

1. Переведи Instagram в **Business** и свяжи с Facebook Page.
2. В https://developers.facebook.com/apps/ создай приложение Meta, настрой Facebook Login + Instagram Graph API, разрешения для публикаций (обычно `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`), роли приложения и токен с подходящим доступом.
3. Получи **Instagram Business Account ID** (`IG_USER_ID`) связанной страницы. ID — не никнейм.
4. Убедись, что приложение может публиковать контент для твоего аккаунта, и проверь срок токена. Не передавай доступ к аккаунту неофициальным ботам.
5. Добавь GitHub Secrets `META_ACCESS_TOKEN` и `IG_USER_ID`.

В проекте выбран **Facebook Login** и хост `graph.facebook.com`; не смешивай с Instagram Login, где другие токены и хост `graph.instagram.com`.

## 4. Cloudinary: чтобы Meta могла скачать видео

1. Зарегистрируй бесплатный аккаунт на https://cloudinary.com/pricing.
2. Найди `CLOUDINARY_URL` в своей консоли/инструкциях SDK вида `cloudinary://API_KEY:API_SECRET@CLOUD_NAME`.
3. Добавь **только в GitHub Secrets** `CLOUDINARY_URL`.
4. Убедись, что бесплатного месячного лимита хватает. Все опубликованные видео и картинки станут доступны по публичным HTTPS-ссылкам Cloudinary.

## 5. Включить автоматическую публикацию

Когда проверишь черновики и предоставишь рабочий Meta-токен:

1. GitHub → **Settings → Secrets and variables → Actions → Variables → New repository variable**.
2. Name: `PUBLISH_ENABLED`, Value: `true`.
3. Нажми **Actions → Run workflow** для пробной публикации.
4. Если тест прошёл, оставь расписание: `12:00` — Stories, `16:00` — посты Вт/Чт/Сб, `19:00` — Reels, timezone Asia/Bishkek. Запуски могут задерживаться.

Скрипт формирует Reels в 19:00, Story в 12:00 каждый день и пост Вт/Чт/Сб в 16:00. После успешной публикации пишет `state/YYYY-MM-DD.json`, чтобы избежать повторных постов при повторном запуске в тот же день. Если Meta приняла публикацию, но ответ потерялся, всё же проверь аккаунт вручную перед повтором.

## 6. Запуск на компьютере

Нужны Python 3.11+, `ffmpeg` и шрифты DejaVu Sans.

```bash
python -m pip install -r requirements.txt
python run.py
```

На Windows установи FFmpeg отдельно и поправь пути шрифтов в `render.py`, либо запускай в GitHub Actions (рекомендуется). Для отладки без публикации можно задать `TEST_DATE=2026-11-24` и `PUBLISH_ENABLED=false`.

## Что в проекте

- `agent.py` — идея, безопасный запрос к Gemini, fallback.
- `topics.json` — 30 тем бизнеса и услуг.
- `render.py` — создание mp4, Story и поста.
- `publish.py` — Cloudinary + Instagram Meta Graph API.
- `state.py` — защита от повторной публикации в один день.
- `run.py` — вся цепочка.
- `.github/workflows/daily.yml` — бесплатный ежедневный запуск на GitHub Actions.

**Не является инструментом накрутки:** никакой автоматической подписки/лайков/спама/ботов, никакой платной рекламы.
