# agro-auth-service

Микросервис аутентификации и интроспекции JWT для платформы.

## Стек
- Python 3.11
- FastAPI
- PostgreSQL
- SQLAlchemy v2

## Быстрый запуск
```bash
docker network create agronetwork 2>/dev/null || true
docker compose up -d --build
```

Сервис доступен на `http://localhost:8001`, Swagger - `http://localhost:8001/docs`.

## Переменные окружения
Конфигурация хранится в `.env` (используется `docker-compose.yml`).

## Проверка интроспекции токена
```bash
curl -X POST http://localhost:8001/api/auth/introspect \
  -H "Authorization: Bearer <JWT>"
```

