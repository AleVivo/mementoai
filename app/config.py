from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_url: str
    mongodb_db: str
    mongodb_user: str
    mongodb_password: str
    ollama_url: str
    ollama_num_gpu: int = 0
    log_level: str = "INFO"
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    llm_model: str = "ollama/qwen3.5:4b" 
    embedding_model: str = "ollama/nomic-embed-text"

    openai_api_key: str = ""                # Richiesta se llm_provider="openai" o embedding_provider="openai"
    groq_api_key: str = ""                  # Richiesta se llm_provider="groq"

    model_config = {
        "env_file": ".env",
    }

settings = Settings() # type: ignore[call-arg]