from pydantic_settings import BaseSettings

class settings(BaseSettings):
    mongodb_url: str
    mongodb_db: str
    mongodb_user: str
    mongodb_password: str
    ollama_url: str

    model_config = {
        "env_file": ".env",
    }

settings = settings()