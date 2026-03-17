from pydantic_settings import BaseSettings

class Settings(BaseSettings):
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

    llm_provider: str = "ollama"
    embedding_provider: str = "ollama"      # Quale provider usare per gli embedding. Valori: "ollama" | "openai"
    # ATTENZIONE: cambiare questo valore richiede re-indicizzazione completa.

    ollama_chat_model: str = "qwen2.5:7b"
    ollama_embed_model: str = "nomic-embed-text"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"
    groq_chat_model: str = "llama-3.3-70b-versatile"

    openai_api_key: str = ""                # Richiesta se llm_provider="openai" o embedding_provider="openai"
    groq_api_key: str = ""                  # Richiesta se llm_provider="groq"

    model_config = {
        "env_file": ".env",
    }

settings = Settings() # type: ignore[call-arg]