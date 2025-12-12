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
