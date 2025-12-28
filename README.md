# Leads Coloring Widget Backend

Микросервис для управления правилами окраски лидов в AmoCRM.

## Описание

Этот микросервис предоставляет API для:
- Создания и управления правилами окраски лидов
- Проверки условий и применения стилей к лидам
- Получения полей сделок из AmoCRM
- Тестирования правил

## Технологический стек

- **FastAPI** - REST API framework
- **FastStream** (RabbitMQ) - обработка сообщений из очередей
- **PostgreSQL** - хранение правил
- **SQLAlchemy** - ORM
- **Alembic** - миграции БД
- **aiohttp** - асинхронные HTTP запросы к AmoCRM API
- **Pydantic** - валидация данных

## Структура проекта

```
leads_coloring/
├── src/
│   ├── common/          # Общие модули (config, database, logging)
│   ├── amocrm/          # Работа с AmoCRM API (rate limiting, requests)
│   ├── broker/          # FastStream конфигурация (middlewares, routers)
│   ├── rules/           # Модели и логика правил окраски
│   └── conditions/      # Evaluator для проверки условий
├── migrations/          # Миграции базы данных (Alembic)
├── main.py             # Точка входа FastAPI
├── broker_app.py       # Точка входа FastStream worker
├── requirements.txt    # Зависимости Python
├── Dockerfile          # Docker образ
└── docker-compose.yml  # Конфигурация Docker Compose
```

## API Endpoints

### Управление правилами

- `GET /api/deal-fields` - Получение списка полей сделок
- `POST /api/rules` - Создание правила
- `PUT /api/rules/{id}` - Обновление правила
- `GET /api/rules` - Получение списка правил
- `DELETE /api/rules/{id}` - Удаление правила
- `PUT /api/rules/priorities` - Обновление приоритетов правил

### Применение стилей

- `POST /api/leads/styles` - Получение стилей для списка лидов

### Тестирование

- `POST /api/rules/test` - Тестирование правила на данных лида

## Установка и запуск

### Docker

1. Создать `.env-non-dev` файл с переменными окружения
2. Запустить через docker-compose:

```bash
docker-compose up -d
```

## Операторы условий

### Текстовые поля
- equals, not_equals, contains, not_contains, starts_with, ends_with, is_empty, is_not_empty

### Числовые поля
- equals, not_equals, greater_than, less_than, greater_or_equal, less_or_equal, between, is_empty, is_not_empty

### Даты
- equals, not_equals, after, before, today, yesterday, this_week, last_week, this_month, last_month, last_n_days

### Списки
- equals, not_equals, in_list, not_in_list, is_empty, is_not_empty
