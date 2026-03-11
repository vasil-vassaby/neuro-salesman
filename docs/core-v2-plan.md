# Core v2 Plan

## Что должен уметь Core v2

Core v2 — это минимальное, но правильное ядро AI-администратора для экспертного бизнеса.

### Обязательные сценарии

#### 1. Новый пользователь
- пользователь пишет /start
- получает приветствие
- даёт согласие на обработку персональных данных
- получает главное меню
- может перейти к записи или FAQ

#### 2. FAQ / вопросы
- бот отвечает на частые вопросы:
  - стоимость
  - как проходит консультация
  - где принимаете
  - сколько длится
  - как подготовиться
  - противопоказания
- если structured ответа нет, можно использовать LLM fallback
- бот не выдумывает цены, услуги и медицинские утверждения

#### 3. Запись
- пользователь запускает booking flow
- бот помогает выбрать нужный сценарий
- показывает свободные слоты
- создаёт booking
- отправляет подтверждение
- ставит reminders

#### 4. Перенос записи
- пользователь запускает reschedule flow
- бот находит активную запись
- показывает новые слоты
- переносит booking
- пересоздаёт reminders

#### 5. Handoff
- администратор может перевести диалог в ручной режим
- бот перестаёт автоматически отвечать
- сообщения сохраняются
- человек продолжает общение вручную

#### 6. Web admin
- просмотр входящих диалогов
- просмотр и управление booking
- управление slots
- управление expert settings
- редактирование FAQ/templates
- базовая аналитика

#### 7. Public web booking
- пользователь может оставить заявку через web
- может выбрать слот
- web использует ту же бизнес-логику, что и Telegram

---

## Основные сущности

### Lead
Хранит клиента / потенциального клиента.

Минимальные поля:
- id
- name
- telegram_username
- telegram_chat_id
- phone
- consent_given
- lead_status
- created_at

### Conversation
Хранит диалог.

Минимальные поля:
- id
- lead_id
- channel
- state_json
- handoff_mode
- last_intent
- created_at
- updated_at

### Message
Хранит историю сообщений.

Минимальные поля:
- id
- conversation_id
- role
- text
- meta
- created_at

### Slot
Хранит доступное время.

Минимальные поля:
- id
- starts_at_utc
- ends_at_utc
- capacity
- reserved_count
- is_active

### Booking
Хранит запись на консультацию.

Минимальные поля:
- id
- lead_id
- slot_id
- offer_id
- status
- source
- created_at

### Reminder
Хранит напоминание.

Минимальные поля:
- id
- booking_id
- remind_at_utc
- status
- channel

### Offer
Хранит услугу / формат.

Минимальные поля:
- id
- title
- description
- price_min
- price_max
- duration_minutes
- format_type
- active

### ExpertSettings
Хранит настройки эксперта.

Минимальные поля:
- business_name
- expert_name
- address
- contact_phone
- timezone
- day_start_hour
- day_end_hour
- slot_duration_minutes
- welcome_message
- booking_confirmation_text
- reminder_24h_text
- reminder_2h_text
- allow_online
- allow_offline
- is_bot_enabled

### FAQ / Templates / KB
- kb_articles
- reply_templates

---

## Архитектура

### Целевая архитектура

```text
Telegram / Web
↓
Conversation Orchestrator
↓
Intent Layer
↓
Services
  - Booking Service
  - FAQ Service
  - CRM Service
  - Reminder Service
  - Consent Service
  - Handoff Service
↓
LLM Fallback
↓
PostgreSQL