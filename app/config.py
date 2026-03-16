from pydantic_settings import BaseSettings

class settings(BaseSettings):
    mongodb_url: str
    mongodb_db: str
    mongodb_user: str
    mongodb_password: str
    ollama_url: str
    log_level: str = "INFO"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    model_config = {
        "env_file": ".env",
    }

settings = settings()