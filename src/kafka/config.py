from pydantic_settings import BaseSettings, SettingsConfigDict

class KafkaSettings(BaseSettings):
    BOOTSTRAP_SERVERS: str
    REQUESTS_TOPIC: str = "agro.notification.requests"

    model_config = SettingsConfigDict(env_prefix="KAFKA_", env_file=".env")

kafka_settings = KafkaSettings()