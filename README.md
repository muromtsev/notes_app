# Notes API

REST API для заметок с авторизацией и ролевой моделью.
Учебный проект для отработки продакшн-стека: FastAPI, PostgreSQL, SQLAlchemy 2.x (async), Alembic, JWT.

## Стек

- **Python** 3.12
- **FastAPI** + Uvicorn
- **SQLAlchemy 2.x** (async) + asyncpg
- **PostgreSQL** 16
- **Alembic** (async-миграции)
- **Pydantic v2** + pydantic-settings
- **JWT** (python-jose) + bcrypt (passlib)
- **structlog** — структурированное логирование
- **pytest** + pytest-asyncio + httpx — тесты
- **uv** — управление зависимостями
- **Docker Compose** — локальный Postgres
- **Ruff** + mypy — линт и типы

# Архитектура

Слоистая архитектура — каждый слой отвечает за своё:

```bash
┌─────────────────────────────────────┐
│  API (FastAPI routers)              │  ← валидация запроса/ответа, HTTP
├─────────────────────────────────────┤
│  Services (бизнес-логика)           │  ← проверки прав, теги, транзакции
├─────────────────────────────────────┤
│  Repositories (доступ к БД)         │  ← SQLAlchemy-запросы
├─────────────────────────────────────┤
│  Models (SQLAlchemy) + Schemas      │  ← структура данных
└─────────────────────────────────────┘
           ↓
      PostgreSQL
```

**Ключевые решения:**

- Транзакционная граница — на уровне **сервиса** (`commit()`), репозиторий только `flush()`
- Доменные ошибки (`AppError`) автоматически конвертируются в HTTP-ответы единого формата
- Логи структурированные (`structlog`), `request_id` привязан через `contextvars`

## Запуск локально

### 1. Клонировать и установить зависимости

```bash
git clone https://github.com/muromtsev/notes_app.git
cd notes_app
uv sync
```

### 2. Настроить окружение

```bash
cp .env.example .env
# при необходимости отредактируй .env
```

### 3. Поднять Postgres

```bash
docker compose up -d
```

### 4. Применить миграции

```bash
uv run alembic upgrade head
```

### 5. Запустить приложение

```bash
uv run fastapi dev src/notes_app/main.py
```

API: http://localhost:8000

Swagger: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

## API

Все эндпоинты, кроме `/health`, требуют JWT в заголовке `Authorization: Bearer <token>`.

### Аутентификация

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/v1/auth/register` | Регистрация (email + password) |
| `POST` | `/api/v1/auth/login` | Логин (OAuth2 password flow), возвращает access + refresh |
| `POST` | `/api/v1/auth/refresh` | Обновление access-токена по refresh |
| `GET` | `/api/v1/auth/me` | Текущий пользователь |

### Заметки

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/api/v1/notes/` | Создать заметку (с тегами) |
| `GET` | `/api/v1/notes/` | Список с пагинацией, поиском, фильтром по тегу |
| `GET` | `/api/v1/notes/{id}` | Одна заметка |
| `PATCH` | `/api/v1/notes/{id}` | Частичное обновление |
| `DELETE` | `/api/v1/notes/{id}` | Удалить |

**Параметры списка:**

- `skip`
- `limit` (≤100)
- `search` (по title)
- `tag`
- `order_by` (`created_at`, `updated_at`, `title`, `id`; с `-` для desc)

**Роли:**

- `user` видит только свои заметки
- `admin` — все

### Пример запроса

```bash
# Логин
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=user@example.com&password=password123"

# Создание заметки
curl -X POST http://localhost:8000/api/v1/notes/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Hello", "content": "World", "tags": ["work"]}'
```

# Формат ошибок

Все ошибки приходят в едином формате:

```json
{
  "detail": "Invalid email or password",
  "code": "invalid_credentials"
}
```

Для ошибок валидации добавляется список `errors`:

```json
{
  "detail": "Validation error",
  "code": "validation_error",
  "errors": [
    { "field": "body.email", "message": "value is not a valid email address", "type": "value_error" }
  ]
}
```

## Тесты

### Создай тестовую БД один раз:
```bash
docker compose exec postgres psql -U notes -d notes -c "CREATE DATABASE notes_test;"
```

### Запуск:

```bash
uv run pytest -v
```

## Разработка

```bash
uv run ruff check .          # линтер
uv run ruff check . --fix    # линтер с автоправками
uv run ruff format .         # форматтер
uv run mypy src              # проверка типов
uv run pre-commit run --all-files   # все хуки
```

# Postman

В папке `postman/` — готовая коллекция для ручного тестирования:

- `Notes-API.postman_collection.json` — все запросы с test-scripts
- `Notes-API-local.postman_environment.json` — переменные окружения
- `README.md` — инструкция по импорту и использованию

Импортируй оба файла в Postman → выбери environment **Notes API - Local** → запусти `Auth → Register` → `Auth → Login` (токены сохранятся автоматически) → остальные запросы подхватят токен сами.

# CI

GitHub Actions запускается на каждый push и PR в `main`:

- **lint** — Ruff check + Ruff format check + mypy
- **test** — pytest с реальным PostgreSQL в `services`

Конфиг: `.github/workflows/ci.yml`

# Переменные окружения

Смотри `.env.example`. Ключевые:

| Переменная                     | Назначение                                |
|--------------------------------|-------------------------------------------|
| `POSTGRES_*`                   | Подключение к PostgreSQL                  |
| `POSTGRES_TEST_DB`             | Имя тестовой БД                           |
| `JWT_SECRET_KEY`               | Секрет для подписи JWT (менять в проде!)  |
| `JWT_ALGORITHM`                | Алгоритм подписи (HS256)                  |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | Время жизни access-токена                 |
| `REFRESH_TOKEN_EXPIRE_DAYS`    | Время жизни refresh-токена                |
| `LOG_LEVEL`                    | Уровень логирования                       |
