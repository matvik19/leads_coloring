# Миграция с FastAPI на FastStream

## Обзор

Данный документ описывает миграцию REST API endpoints с FastAPI на FastStream message handlers для обработки через RabbitMQ.

## Архитектура

### До миграции
- FastAPI REST endpoints в `/src/app/api/api_v1/endpoints/`
- Синхронная обработка HTTP запросов
- Прямой вызов бизнес-логики

### После миграции
- FastStream handlers в `/src/app/core/broker/routers/`
- Асинхронная обработка сообщений из RabbitMQ
- Middleware для логирования и retry логики
- Dependency Injection для DB и HTTP сессий

## Структура проекта

```
src/app/core/broker/
├── app.py                      # Конфигурация брокера
├── config.py                   # Имена очередей и настройки
├── dependencies.py             # DI для handlers
├── middlewares/
│   ├── logging_middleware.py  # Логирование + context
│   └── retry_middleware.py    # Retry логика
└── routers/
    ├── rules.py               # Операции с правилами
    ├── leads.py               # Операции с лидами
    ├── fields.py              # Получение полей сделок
    └── health.py              # Healthcheck
```

## Маппинг endpoints → queues

| FastAPI Endpoint | HTTP Method | RabbitMQ Queue | Handler |
|-----------------|-------------|----------------|---------|
| `/api/deal-fields` | GET | `leads_coloring_deal_fields` | `handle_get_deal_fields` |
| `/api/rules` | POST | `leads_coloring_rules_create` | `handle_create_rule` |
| `/api/rules/{rule_id}` | PUT | `leads_coloring_rules_update` | `handle_update_rule` |
| `/api/rules` | GET | `leads_coloring_rules_list` | `handle_get_rules` |
| `/api/rules/{rule_id}` | DELETE | `leads_coloring_rules_delete` | `handle_delete_rule` |
| `/api/rules/priorities` | PUT | `leads_coloring_priorities_update` | `handle_update_priorities` |
| `/api/leads/styles` | POST | `leads_coloring_leads_styles` | `handle_get_leads_styles` |
| `/api/rules/test` | POST | `leads_coloring_rules_test` | `handle_test_rule` |
| `/health` | GET | `leads_coloring_health` | `handle_health_check` |

## Очереди RabbitMQ

Все очереди создаются с параметром `durable=True` для сохранения сообщений при перезапуске.

### Именование
Формат: `leads_coloring_{entity}_{operation}`

Примеры:
- `leads_coloring_rules_create`
- `leads_coloring_rules_update`
- `leads_coloring_leads_styles`

## Обработка сообщений

### Структура handler

```python
@router.subscriber(RabbitQueue(QueueNames.EXAMPLE, durable=True))
async def handle_example(
    data: dict,
    db_session: Annotated[AsyncSession, Depends(get_db_session)],
    http_session: Annotated[RateLimitedClientSession, Depends(get_http_session)],
) -> Dict[str, Any]:
    """Handler для обработки сообщения"""
    try:
        # 1. Валидация через Pydantic
        request = ExampleRequest(**data)

        # 2. Бизнес-логика
        result = await process_example(request, db_session)

        # 3. Возврат результата
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error("Ошибка: %s", e, exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
```

### Middleware стек

1. **RetryMiddleware** (внешний слой)
   - Автоматический retry при ошибках
   - Максимум 3 попытки
   - Задержка 5 секунд между попытками

2. **LoggingMiddleware** (внутренний слой)
   - Установка контекста (subdomain, request_id)
   - Логирование начала и конца обработки
   - Автоматический сброс контекста

### Dependency Injection

#### Database Session
```python
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session
```

#### HTTP Session
```python
async def get_http_session() -> AsyncGenerator[RateLimitedClientSession, None]:
    async with ClientSession(connector=TCPConnector(ssl=False, limit=100)) as session:
        rate_limited_session = RateLimitedClientSession(session)
        yield rate_limited_session
```

## Формат сообщений

### Запрос на создание правила
```json
{
  "subdomain": "example",
  "name": "Правило 1",
  "is_active": true,
  "priority": 1,
  "conditions": {
    "type": "AND",
    "rules": [
      {
        "field": "price",
        "operator": ">",
        "value": 1000
      }
    ]
  },
  "style": {
    "text_color": "#000000",
    "background_color": "#FFFFFF"
  }
}
```

### Ответ
```json
{
  "success": true,
  "id": 123
}
```

### Формат ошибки
```json
{
  "success": false,
  "error": "Описание ошибки"
}
```

## Конфигурация

### Environment Variables

```bash
# RabbitMQ
RABBITMQ_HOST=broker
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
RABBITMQ_VHOST=/

# Worker
WORKER_WORKERS=1
WORKER_PREFETCH_COUNT=10

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=password
DB_DATABASE=leads_coloring

# AmoCRM
AMOCRM_CLIENT_SECRET=...
AMOCRM_CLIENT_ID=...
AMOCRM_REDIRECT_URL=...
AMOCRM_RATE_LIMIT=6.0
AMOCRM_RATE_BURST=6
```

## Запуск

### FastStream Worker
```bash
# Из директории проекта
cd src
faststream run app.broker_app:app --workers 1

# С параметрами
faststream run app.broker_app:app --workers 2 --log-level info
```

### FastAPI Server (опционально, если нужен REST API)
```bash
cd src
uvicorn app.web_app:application --host 0.0.0.0 --port 8000
```

## Миграция клиентского кода

### До (HTTP запрос)
```javascript
const response = await fetch('/api/rules', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
});
const result = await response.json();
```

### После (RabbitMQ сообщение)
```python
# Отправка сообщения в очередь
await broker.publish(
    message=data,
    queue="leads_coloring_rules_create"
)

# RPC паттерн (с ожиданием ответа)
response = await broker.request(
    message=data,
    queue="leads_coloring_rules_create",
    timeout=30
)
```

## Преимущества FastStream

1. **Асинхронная обработка** - не блокирует клиента
2. **Масштабируемость** - можно запустить несколько воркеров
3. **Retry логика** - автоматическое переповторение при ошибках
4. **Middleware** - переиспользуемая логика (логирование, retry)
5. **Dependency Injection** - чистый код, легкое тестирование
6. **Type hints** - полная поддержка типизации
7. **Декларативный синтаксис** - похож на FastAPI

## Мониторинг

### Логи
Каждое сообщение логируется с контекстом:
```
[subdomain] [request_id] 2026-01-24 10:00:00 | INFO | handle_create_rule:50 | Создано правило id=123
```

### Метрики RabbitMQ
- Количество сообщений в очередях
- Скорость обработки
- Количество ошибок (nack/reject)

## Тестирование

### Unit тесты
```python
@pytest.mark.asyncio
async def test_handle_create_rule():
    data = {
        "subdomain": "test",
        "name": "Test Rule",
        # ...
    }

    result = await handle_create_rule(data, mock_db_session)

    assert result["success"] is True
    assert "id" in result
```

### Интеграционные тесты
```python
@pytest.mark.asyncio
async def test_full_flow():
    # Отправка сообщения в очередь
    await broker.publish(message=data, queue=QueueNames.RULES_CREATE)

    # Ожидание обработки
    await asyncio.sleep(1)

    # Проверка результата в БД
    rule = await get_rule_by_id(rule_id, db_session)
    assert rule is not None
```

## Rollback Plan

Если потребуется откатиться к FastAPI:

1. Переключить клиентов обратно на HTTP endpoints
2. Остановить FastStream воркеры
3. Запустить FastAPI сервер
4. Старые endpoints сохранены в `/src/app/api/api_v1/endpoints/`

## Заметки

- Все очереди persistent (durable=True)
- Prefetch count = 10 (можно увеличить для большей нагрузки)
- Timeout для RPC = 30 секунд
- Rate limiting для AmoCRM: 6 запросов/сек
- Контекст логирования автоматически управляется middleware

## Авторы

Миграция выполнена согласно референсной реализации:
https://github.com/matvik19/amocrm-widget-allocation/tree/claude/fix-request-processing-8mA3m
