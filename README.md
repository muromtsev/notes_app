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

## Статус
### Проект в активной разработке.

+ Каркас проекта, конфиг, логирование
+ Модели User / Note / Tag, миграции, тесты
