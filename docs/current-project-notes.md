---
alwaysApply: true
---
# Current Project Notes

## Что уже работает

### Инфраструктура
- Проект запускается через Docker и docker-compose
- Backend, frontend и PostgreSQL поднимаются в контейнерах
- Проект развернут на сервере
- Настроен nginx
- Настроен домен
- Работает HTTPS
- Telegram webhook на сервере работает
- Локально Telegram можно тестировать отдельно

### Backend / API
- Есть FastAPI backend
- Есть health/config endpoints
- Есть базовая структура API
- Есть работа с PostgreSQL
- Есть SQLAlchemy-модели
- Есть booking сущности
- Есть slot сущности
- Есть reminder сущности
- Есть lead / conversation / message логика
- Есть часть admin CRUD

### Telegram bot
- Бот умеет отвечать
- Есть /start
- Есть consent flow
- Есть главное меню
- Есть booking сценарий
- Есть price / FAQ ветки
- Есть reschedule flow, но он пока работает нестабильно
- Есть handoff-related заготовки
- Есть callback-кнопки

### Web / Admin
- Есть web-admin интерфейс
- Есть inbox / conversations
- Есть bookings
- Есть slots
- Есть базовая web booking форма
- Есть доступ по домену
- Есть frontend, который уже работает на сервере

### Архитектурный прогресс
- Начат переход к новой архитектуре
- Появился conversation state facade
- Появился intent layer
- Появился booking service layer
- Есть project rules
- Есть architecture.md

---

## Что нужно сохранить

### Инфраструктура и деплой
- docker-compose
- nginx конфиг
- серверный деплой
- HTTPS
- Telegram webhook setup
- текущую env-дисциплину (один .env, без хаоса)
- production routing через nginx
- доменную конфигурацию

### Данные и сущности
- Lead
- Conversation
- Message
- Slot
- Booking
- Reminder
- Offer
- ExpertSettings
- ReplyTemplate
- Knowledge/KB сущности, если они уже есть

### Рабочие куски логики
- базовую логику booking
- работу reminders
- существующий Telegram transport
- базовую web admin часть
- подтверждение записи
- cancel / no-show механику, если она уже работает
- consent как обязательный шаг
- reschedule как обязательный бизнес-сценарий

### Новые архитектурные шаги, которые уже сделаны
- conversation/state facade
- typed intents
- booking_service как отдельный слой

---

## Что в проекте плохое / мешает

### Архитектурные проблемы
- проект рос без чёткой продуктовой схемы
- бизнес-логика долгое время была размазана по handlers
- Telegram transport и бизнес-логика были смешаны
- state-машина была нестабильной
- consent logic уже ломалась
- reschedule flow сейчас ведёт себя не так, как должен
- routing местами ведёт в fallback / главное меню, когда не должен
- intent logic долгое время была нецентрализованной
- project started as prototype, not as product core

### Продуктовые проблемы
- изначально не было чёткого понимания продукта
- нет зафиксированного минимального Core v2
- LLM пытались подключать раньше, чем созрела архитектура
- UI / Telegram UX ощущаются непродуманными
- сценарии не всегда выглядят как работа цифрового администратора
- много решений принималось “по ходу”, а не от требований

### Технические проблемы
- есть исторические хвосты в коде
- есть риск скрытых багов в state transitions
- есть риск, что часть старых if/else логик конфликтует с новым слоем intents/services
- часть сообщений/кнопок Telegram может вести себя нестабильно
- есть риск повторного появления timezone-багов, если не централизовать время окончательно
- frontend и admin UI пока ещё не выглядят как законченный продукт

---

## Что можно перенести в Core v2

### Переносить почти точно
- SQLAlchemy модели:
  - Lead
  - Conversation
  - Message
  - Slot
  - Booking
  - Reminder
  - Offer
  - ExpertSettings
- docker-compose
- nginx конфиги
- серверную схему деплоя
- HTTPS / webhook setup
- env-переменные и общую env-структуру
- booking_service (как основу или как донор)
- conversation state ideas
- intent layer ideas
- API схемы и часть CRUD
- admin page ideas
- Telegram callback patterns

### Переносить после проверки
- consent flow
- reschedule flow
- FAQ routing
- reminder scheduling logic
- часть admin actions
- часть frontend pages
- часть current routes

### Не переносить как есть
- хаотичную routing-логику из старых Telegram handlers
- старые if/else сценарии без orchestration
- смешение transport + business logic
- ad hoc fixes
- временные патчи под конкретные баги
- всё, что выглядит как “костыль ради того, чтобы сейчас заработало”

---

## Главный вывод

Текущий проект не является хорошей финальной базой для масштабируемого продукта.

Но он очень полезен как:
- рабочий прототип
- источник требований
- донор кода
- донор deploy-инфраструктуры
- донор сущностей и моделей
- наглядный список ошибок, которые нельзя повторить в Core v2