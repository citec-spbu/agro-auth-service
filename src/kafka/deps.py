from fastapi import Request
from aiokafka import AIOKafkaProducer

def get_kafka_producer(request: Request) -> AIOKafkaProducer:
    return request.app.state.kafka_producer