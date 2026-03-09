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

- **Backend smoke-тесты (минимальная проверка цепочки слоты → веб-запись → статусы):**

```bash
docker compose exec backend python -m app.smoke_tests
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

**Умные сценарии записи (без LLM):**

- Бот хранит состояние в `conversations.state` (flow/step/goal/format/time_pref/slot_id).
- Ключевые переменные окружения для сценариев:
  - `ALLOWED_FORMATS` — csv из `offline,online` (по умолчанию `offline,online`).
  - `ALLOWED_TIME_PREFS` — csv из `day,evening` (по умолчанию `day,evening`).
  - `DAY_START_HOUR` и `DAY_END_HOUR` — границы дневных слотов (по умолчанию `9` и `15`).
- Если в `ALLOWED_FORMATS` или `ALLOWED_TIME_PREFS` остался один вариант, бот его подставляет автоматически и не задаёт лишний вопрос.

**Сценарий теста “Записаться” end-to-end:**

1. В `.env` задайте:

   ```bash
   ALLOWED_FORMATS=offline
   ALLOWED_TIME_PREFS=day
   DAY_START_HOUR=9
   DAY_END_HOUR=15
   ```

2. Перезапустите `docker compose up --build`.
3. Напишите боту в Telegram: `Записаться`.
4. Бот:
   - создаст лида и диалог в БД;
   - начнёт `booking`-flow (`flow="booking"`, `step=1`);
   - задаст вопрос по цели (`booking_step_goal`) с кнопками:
     - Сон и восстановление (`goal:sleep`)
     - Боль / напряжение (`goal:pain`)
     - Пищеварение (`goal:digestion`)
     - Другое (`goal:other`).
5. Нажмите любую кнопку цели.
   - При `ALLOWED_FORMATS=offline` и `ALLOWED_TIME_PREFS=day` бот **не** задаёт вопросы про формат/время (они подставляются в состоянии автоматически).
   - Бот сразу переходит к шагу слотов (`booking_step_slots`) и предлагает **top‑3** ближайших свободных дневных слота (09:00–15:00) с кнопками выбора (`slot:<uuid>`).
6. Нажмите на один из слотов:
   - в БД создаётся `booking` со `status=requested`, `slot_id`, `lead_id`, `source="telegram"`;
   - увеличивается `reserved_count` выбранного слота (без превышения `capacity`);
   - ставится напоминание в очередь (`reminders_queue`) по тем же правилам, что и для веб-записей;
   - бот отправляет подтверждение вида:
     > Заявка на запись принята на {date_time}. Подтвержу в ближайшее время.
7. Откройте `http://localhost:5173/`:
   - в Inbox появится диалог с лидом;
   - в `/lead/:id` в правом блоке:
     - увидите созданный `booking` со статусом `requested`;
     - в блоке **State (debug)** — JSON с полями `flow/step/goal/format/time_pref/slot_id`.
8. Откройте `http://localhost:5173/web`:
   - вызовите ссылку из Telegram с параметрами, например:

     `http://localhost:5173/web?goal=sleep&format=offline&time=day`

   - на странице в блоке “Предзаполненные параметры” будут показаны выбранные значения;
   - список слотов будет отфильтрован по `time=day` и правилам “день 9–15”;
   - при отсутствии query‑параметров `/web` работает как раньше (все активные слоты на 7 дней вперёд).

**Проверка логики шаблонов и fallback:**

- Бот использует шаблоны из `reply_templates`:
  - шаги сценария записи: `booking_step_goal`, `booking_step_format`, `booking_step_time`, `booking_step_slots`, `booking_confirm_requested`;
  - сценарий цены: `price_step_goal` + базовый `price_general`;
  - общий fallback: `fallback_web`.
- Везде подставляется `{web_url}` = `FRONTEND_PUBLIC_URL.rstrip("/") + "/web"` (если переменная не задана, используется `APP_URL`).
- Если доставка в Telegram не удалась, бот использует `fallback_web` с ссылкой на веб-хаб.

**Проверка callback-кнопок (ping):**

1. Убедитесь, что backend запущен (`docker compose up --build`) и `/api/health` отдаёт `{"ok": true}`.
2. Напишите боту сообщение `ping`.
3. Бот ответит сообщением с кнопкой **Ping** (inline keyboard).
4. Нажмите кнопку **Ping**:
   - в логах backend появится строка вида:
     - `Received update <id> of type callback_query`
     - `Handling callback_query with data=ping`;
   - бот сразу (без крутилки) ответит сообщением `OK` и отправит `answerCallbackQuery` Telegram‑у.

### Inbox и карточка лида

- Откройте `http://localhost:5173/`:
  - Список диалогов (Inbox) с последним сообщением и статусом лида.
  - Переход в `/lead/:id` открывает карточку лида с историей сообщений и формой отправки ответа.

### Важные эндпойнты backend

- `GET /api/health` → `{"ok": true}`
- `GET /api/config` → `{"app_url": ..., "web_url": ..., "rag_enabled": ..., "telegram_mode": "...", "reminder_hours_before": ...}`
- `GET /api/inbox/conversations` → список диалогов для Inbox.
- `GET /api/conversations/{id}` → диалог + сообщения.
- `POST /api/conversations/{id}/messages` → отправка сообщения (Telegram + логирование статуса доставки).
- `GET /api/slots` / `POST /api/slots` / `PATCH /api/slots/{id}` / `DELETE /api/slots/{id}` → управление слотами.
- `POST /api/web/bookings` → создание брони с веб-формы (лид + booking + напоминание).
- `GET /api/bookings` / `GET /api/leads/{id}/bookings` / `PATCH /api/bookings/{id}` → просмотр и управление бронями.
- `POST /api/leads/{id}/lost` → пометить лид как Lost с reason_code.
- CRUD: `/api/kb_articles`, `/api/offers`, `/api/reply_templates`.

### Сброс сценария и отладка state-машины

- В любой момент пользователь может отправить `/reset` в Telegram:
  - состояние `conversations.state` сбрасывается в пустой словарь;
  - следующий `/start`, «записаться», «цена» или «перенести» начнёт новый сценарий с нуля.
- В карточке лида (`/lead/:id`) блок **«Состояние (отладка)**» показывает текущее `state` для Telegram-диалога:
  - после успешного подбора слота оно очищается (`flow="other", step=0`);
  - после `confirm/cancel/no_show` через админку состояние также сбрасывается.
- Если сценарий кажется «зависшим», проверьте:
  - есть ли активный `booking` для лида (блок «Записи»);
  - значение `flow/step` в отладочном блоке;
  - при необходимости отправьте `/reset` и начните сценарий заново.

### Напоминание о безопасности

- **`.env` не должен коммититься** — он уже добавлен в `.gitignore`.
- Не храните реальные токены и ключи в коде или README.
- Compliance-guard читает `seeds/compliance_rules.json` и не допускает запрещенные фразы в автоответах; при высоком риске используется безопасный текст без медицинских обещаний.

### Чек-лист ручной проверки

- **Telegram:**
  - `/start` показывает приветствие и кнопки целей; в `conversations.state` → `flow="booking"`, `step=1`.
  - «Цена» / «Стоимость» дают ответ по стоимости с ссылкой на `{web_url}`.
  - «Записаться» запускает booking-flow; выбор `goal:*`, `format:*`, `time:*`, `slot:*` создаёт `booking` и `reminders`.
  - «Перенести» при наличии активной записи предлагает новые `reslot:*` и переносит `booking` без переполнения `reserved_count`.
  - `/reset` всегда сбрасывает состояние, после него глобальные команды работают независимо от прошлого flow.

- **Web / админка:**
  - `/` (Inbox) показывает список диалогов, переход в `/lead/:id` открывает историю сообщений и блоки «Записи», «Отметить как потерян», «Состояние (отладка)».
  - `/slots` позволяет создавать и деактивировать слоты; новые слоты сразу видны в списке и на `/web`.
  - `/web` отображает форму записи, фильтрует слоты по параметрам `goal/format/time`, создаёт `booking` со `status="requested"`.
  - `/bookings` группирует записи по дням, показывает статусы и напоминания.

- **Бронирования и статусы:**
  - Создание записи через Telegram и Web увеличивает `reserved_count` слота, не превышая `capacity`.
  - `PATCH /api/bookings/{id}` с `confirmed/cancelled/no_show` не даёт 500, корректно меняет статусы и, при отмене, уменьшает `reserved_count`.
  - Напоминания создаются при `status=requested`, отправляются только для `confirmed`, статус в очереди и `event_log` обновляется.

- **FAQ и правила:**
  - Вопросы про «как проходит приём», длительность, адрес, подготовку, противопоказания, переноса и услуги попадают в соответствующие шаблоны `reply_templates`.
  - При отсутствии точного шаблона используется fallback с ссылкой на веб-хаб (`fallback_web`), без запрещённых фраз и медицинских обещаний.

