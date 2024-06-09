# Auth microservice
Микровервис для аутентификации в "Цифровом двойнике".

## Разработано с помощью:
- Python 3.11
- FastAPI
- PostgreSQL 
- SQLAlchemy v2
- Pydantic v2
- AIOKafka

## Сборка и запуск проекта:
    git clone https://github.com/AgroScience-Team/auth-service.git

Поднять Kafka: https://github.com/AgroScience-Team/kafka/blob/main/README.md 

Если не создана docker-сеть `agronetwork`, то:

    docker create network agronetwork

Выполнить миграции (при необходимости):

    docker compose -f docker-compose.yml run migrations

Из корневой папки проекта:

    docker compose up -d 

Swagger: `http://0.0.0.0:8000/docs`

## Работа в Swagger:

При переходе на:
`http://0.0.0.0:8000/docs` будут доступны текущие эндпоинты. Для работы с некоторыми из них, требуется аутентификация/авторизация (такие эндпоинты помечены значком 🔓). 

- В правом верхнем углу есть кнопка `Authorize`, генерирующая форму для аутентификации.

- При успешной аутентификации, значки защищенных эндпоинтов меняются на 🔒, и теперь, вы можете тестировать защищенные эндпоинты (в заголовки запросов автоматически добаляется JWToken, сгенерированный на этапе аутентификации).

