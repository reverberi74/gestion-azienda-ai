from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # === AI Model Configuration ===
    MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    DEVICE: str = "cpu"
    MAX_TOKENS: int = 512

    # === API Configuration ===
    HOST: str = "127.0.0.1"
    PORT: int = 8001
    DEBUG: bool = True

    # === Internal security (Laravel -> service-ai) ===
    AI_INTERNAL_TOKEN: str = "dev-ai-internal-2025-12"

    # === Provider: OpenAI (API scenario) ===
    # NB: lasciare vuoto in repo; valorizzare solo in service-ai/.env locale/ambiente
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_TIMEOUT_SEC: int = 20

    # Defaults (possono essere override via metadata.options dal client)
    OPENAI_TEMPERATURE: float = 0.2
    OPENAI_MAX_OUTPUT_TOKENS: int = 280

    # === CORS / Frontend ===
    # Nel .env è una stringa separata da virgole.
    # Esempio:
    # ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """
        Ritorna ALLOWED_ORIGINS come lista pulita di stringhe.
        """
        if not self.ALLOWED_ORIGINS:
            return []
        return [
            origin.strip()
            for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    """
    Restituisce un'unica istanza di Settings (cached).
    """
    return Settings()
