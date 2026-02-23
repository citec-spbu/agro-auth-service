from aiokafka import AIOKafkaProducer
from fastapi import FastAPI
import json

from src.kafka.config import kafka_settings
from src.api.auth import router as auth_router
from src.api.users import router as users_router
import logging

logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title="Auth service",
    description="Digital twin auth microservice.",
    version="0.0.1"
)

@app.on_event("startup")
async def startup():
    producer = AIOKafkaProducer(
        bootstrap_servers=kafka_settings.BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    try:
        await producer.start()
        app.state.kafka_producer = producer
        logger.info("Kafka producer started: %s", kafka_settings.BOOTSTRAP_SERVERS)
    except Exception as e:
        # НЕ падаем, если Kafka нет
        app.state.kafka_producer = None
        logger.warning("Kafka is not available, starting without it: %s", e)

@app.on_event("shutdown")
async def shutdown():
    await app.state.kafka_producer.stop()

app.include_router(auth_router)
app.include_router(users_router)
