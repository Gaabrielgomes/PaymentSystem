from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    rabbitmq_user: str
    rabbitmq_pass: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
