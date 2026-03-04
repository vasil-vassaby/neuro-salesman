## Neuro-Salesman (Telegram + Web MVP)

**Нейро-продажник для эксперта ТКМ:** превращает лиды из Telegram в запись через веб-хаб, снижая ручную рутину. Каналы MVP: **Telegram + Web**.

### Структура проекта

- `docker-compose.yml` — оркестрация `db` (Postgres) + `backend` (FastAPI) + `frontend` (React/Vite).
- `backend/` — FastAPI, SQLAlchemy, Telegram интеграция, bootstrap (таблицы, сиды, KB, RAG).
- `frontend/` — React/Vite интерфейс (Inbox, карточка лида, веб-форма).
- `seeds/` — CSV/JSON сиды (офферы, KB, шаблоны ответов, compliance).
- `rag_md_templates/` — Markdown база знаний для RAG.
- `.env.example` — пример переменных окружения (без секретов).
- `.env` — рабочий файл окружения (**не коммитить**).

### Подготовка `.env`

1. Скопируйте пример:

```bash
cp .env.example .env
```

2. Замените плейсхолдеры `CHANGE_ME_...` в `.env` на реальные значения:

- **JWT_SECRET** — секрет для JWT.
- **COOKIE_SECRET** — секрет для cookie/подписи.
- **POSTGRES_PASSWORD** — пароль к Postgres.
- **TELEGRAM_BOT_TOKEN** — токен Telegram-бота.
- **TELEGRAM_WEBHOOK_SECRET** — секрет для Telegram webhook (используется в заголовке).
- **OPENAI_API_KEY** — ключ к OpenAI/AITunnel (для RAG, опционально).

3. Ключевые переменные:

- **APP_ENV** — `dev` или `prod`.
- **APP_URL** — публичный URL backend API:
  - Локально: `http://localhost:8000`
  - На сервере: `https://your-domain`
- **FRONTEND_PUBLIC_URL** — публичный URL фронтенда:
  - Локально: `http://localhost:5173`
  - На сервере: `https://your-domain` (если фронт раздаётся с корня домена через nginx).
- **VITE_API_BASE_URL** — базовый URL API для фронта (по умолчанию `http://localhost:8000/api`).
- **TELEGRAM_WEBHOOK_URL**:
  - Локально: оставить пустым → бот в режиме **polling**.
  - На сервере: `https://your-domain/integrations/telegram/webhook` → бот в режиме **webhook**.

### Локальный запуск (polling-режим Telegram)

1. Убедитесь, что Docker установлен и запущен.
2. В корне проекта выполните:

```bash
docker compose up --build
```

Это поднимет:

- `db` — Postgres (host внутри сети: `db`).
- `backend` — FastAPI на `http://localhost:8000`.
- `frontend` — Vite dev server на `http://localhost:5173`.

### Запуск на сервере (webhook-режим Telegram)

1. В `.env` задайте:

- `APP_ENV=prod`
- `APP_URL=https://your-domain`
- `TELEGRAM_WEBHOOK_URL=https://your-domain/integrations/telegram/webhook`

2. Запустите в фоновом режиме:

```bash
APP_URL=https://your-domain TELEGRAM_WEBHOOK_URL=https://your-domain/integrations/telegram/webhook docker compose up -d --build
```

Backend при старте:

- Проверит соединение с БД и создаст таблицы.
- Создаст расширение `pgvector` (если возможно).
- Идемпотентно загрузит сиды из `/app/seeds`.
- Идемпотентно загрузит Markdown KB из `/app/rag_md_templates`.
- Если `RAG_ENABLED=true` — попытается построить embeddings (ошибки не ломают запуск).
- Если `TELEGRAM_WEBHOOK_URL` задан — вызовет `setWebhook` у Telegram и залогирует результат.

### Проверка работоспособности

- **Backend health:**

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/config
```

- **Frontend:**
  - Откройте `http://localhost:5173`.
  - Нажмите кнопку **Check API** — она сделает запрос `GET {VITE_API_BASE_URL}/health` и покажет результат.

- **Веб-форма:**
  - Откройте `http://localhost:5173/web`.
  - Заполните: имя, телефон, запрос.
  - После отправки ожидается ответ с подтверждением и создание лида в БД.

### Telegram-сценарии

1. Добавьте в `.env` `TELEGRAM_BOT_TOKEN=CHANGE_ME_TELEGRAM_BOT_TOKEN` (замените на реальный токен).
2. Локально (polling):
   - Оставьте `TELEGRAM_WEBHOOK_URL` пустым.
   - Перезапустите `docker compose up --build`.
3. На сервере (webhook):
   - Установите `TELEGRAM_WEBHOOK_URL=https://your-domain/integrations/telegram/webhook`.
   - Запустите `docker compose up -d --build`.

**Проверка логики ответов:**

- Напишите боту сообщения:
  - `"цена"` → сработает intent `price`, шаблон с описанием цен.
  - `"записаться"` → intent `booking`, шаблон с инструкцией записи.
- В ответе бот использует шаблоны из `reply_templates` с подстановкой `{web_url}` = `FRONTEND_PUBLIC_URL.rstrip("/") + "/web"` (если переменная не задана, используется `APP_URL`).
- Если доставка в Telegram не удалась, бот вернет fallback-шаблон `fallback_web` с ссылкой на веб-хаб.

### Inbox и карточка лида

- Откройте `http://localhost:5173/`:
  - Список диалогов (Inbox) с последним сообщением и статусом лида.
  - Переход в `/lead/:id` открывает карточку лида с историей сообщений и формой отправки ответа.

### Важные эндпойнты backend

- `GET /api/health` → `{"ok": true}`
- `GET /api/config` → `{"app_url": ..., "web_url": ..., "rag_enabled": ..., "telegram_mode": "polling|webhook"}`
- `GET /api/inbox/conversations` → список диалогов для Inbox.
- `GET /api/conversations/{id}` → диалог + сообщения.
- `POST /api/conversations/{id}/messages` → отправка сообщения (Telegram + логирование статуса доставки).
- `POST /api/web/leads` → создание лида с веб-формы.
- CRUD: `/api/kb_articles`, `/api/offers`, `/api/reply_templates`.

### Напоминание о безопасности

- **`.env` не должен коммититься** — он уже добавлен в `.gitignore`.
- Не храните реальные токены и ключи в коде или README.
- Compliance-guard читает `seeds/compliance_rules.json` и не допускает запрещенные фразы в автоответах; при высоком риске используется безопасный текст без медицинских обещаний.

