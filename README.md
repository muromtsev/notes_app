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
uv run ruff check .       # линтер
uv run ruff format .      # форматтер
uv run mypy src           # проверка типов
```

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

**Параметры списка:** `skip`, `limit` (≤100), `search` (по title), `tag`, `order_by` (`created_at`, `updated_at`, `title`, `id`; с `-` для desc).

**Роли:** `user` видит только свои заметки, `admin` — все.

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

## Статус

### Проект в активной разработке.

+ Каркас проекта, конфиг, логирование
+ Модели User / Note / Tag, миграции, тесты
+ Аутентификация (JWT, access + refresh)
+ CRUD заметок, пагинация, теги, роли
+ Логирование запросов, единый формат ошибок
+ CI (GitHub Actions), pre-commit
