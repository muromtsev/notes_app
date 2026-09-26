# Postman collection для Notes API

## Импорт

1. Открой Postman
2. **File → Import** (или Ctrl+O)
3. Перетащи оба файла:
   - `Notes-API.postman_collection.json`
   - `Notes-API-local.postman_environment.json`
4. Выбери environment **Notes API - Local** в правом верхнем углу

## Использование

1. Запусти API: `uv run fastapi dev src/notes_app/main.py`
2. **Health → Healthcheck** — проверь, что API живой
3. **Auth → Register** — создай пользователя (если ещё нет)
4. **Auth → Login** — токены автоматически сохранятся в `{{access_token}}` и `{{refresh_token}}`
5. **Notes → Create Note** — `{{note_id}}` сохранится автоматически
6. Дальше `Get Note`, `Update Note`, `Delete Note` подхватят `{{note_id}}` сами

## Переменные

| Переменная | Заполняется | Описание |
|------------|-------------|----------|
| `base_url` | вручную | Базовый URL API |
| `access_token` | автоматически после Login | JWT access |
| `refresh_token` | автоматически после Login | JWT refresh |
| `note_id` | автоматически после Create Note | ID последней созданной заметки |

## Автоматические проверки

Каждый запрос содержит **test-script**, который проверяет статус-код и структуру ответа. Результаты видны во вкладке **Test Results** после отправки.

## Запуск всей коллекции

**Runner → Notes API → Run** — Postman прогонит всю цепочку по порядку.
