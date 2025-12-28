# Leads Coloring Widget Backend

Микросервис для управления правилами окраски лидов в AmoCRM.

## Технологический стек

- **FastAPI** - REST API framework
- **FastStream** (RabbitMQ) - обработка сообщений из очередей
- **PostgreSQL** - хранение правил
- **SQLAlchemy** + **Alembic** - ORM и миграции БД
- **aiohttp** - асинхронные HTTP запросы к AmoCRM API
- **Pydantic Settings** - управление конфигурацией

## Структура проекта

```
src/
├── app/
│   ├── api/api_v1/endpoints/  # REST API endpoints
│   ├── commands/              # CLI команды
│   ├── core/                  # Настройки, логирование, broker
│   ├── db/                    # База данных
│   ├── models/                # SQLAlchemy модели
│   ├── schemas/               # Pydantic схемы
│   ├── services/              # Бизнес-логика
│   ├── amocrm/                # AmoCRM API интеграция
│   └── utils/                 # Утилиты
├── alembic/                   # Миграции БД
├── manage.py                  # CLI точка входа
└── requirements.txt
```

## API Endpoints

### Управление правилами
- `GET /api/v1/deal-fields` - Получение списка полей сделок
- `POST /api/v1/rules` - Создание правила
- `PUT /api/v1/rules/{id}` - Обновление правила
- `GET /api/v1/rules` - Получение списка правил
- `DELETE /api/v1/rules/{id}` - Удаление правила
- `PUT /api/v1/rules/priorities` - Обновление приоритетов

### Применение стилей
- `POST /api/v1/leads/styles` - Получение стилей для лидов

### Тестирование
- `POST /api/v1/rules/test` - Тестирование правила

### Служебные
- `GET /api/v1/health` - Health check

## Запуск

### CLI команды

```bash
# Development сервер с auto-reload
python manage.py run-dev-server

# Production сервер через Gunicorn
python manage.py run-prod-server

# FastStream worker
python manage.py run-worker --devel
```

### Docker

```bash
# Development
docker-compose -f docker-compose.dev.vendor.yml up --build

# Production
docker-compose up --build
```

## Конфигурация

Все настройки через переменные окружения (см. `.env.example`):
- `DB_*` - PostgreSQL
- `RABBITMQ_*` - RabbitMQ
- `AMOCRM_*` - AmoCRM интеграция
- `WEB_*` - Gunicorn
- `WORKER_*` - FastStream воркер
- `APP_*` - Приложение

## Операторы условий

### Текстовые поля
equals, not_equals, contains, not_contains, starts_with, ends_with, is_empty, is_not_empty

### Числовые поля
equals, not_equals, greater_than, less_than, greater_or_equal, less_or_equal, between

### Даты
equals, not_equals, after, before, today, yesterday, this_week, last_week, this_month, last_month, last_n_days

### Списки
equals, not_equals, in_list, not_in_list

## Миграции БД

```bash
# Создать миграцию
cd src && alembic revision --autogenerate -m "Description"

# Применить миграции
cd src && alembic upgrade head

# Откатить миграцию
cd src && alembic downgrade -1
```
