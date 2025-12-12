from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Configurazione pydantic-settings (v2)
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",  # ignora eventuali chiavi extra invece di esplodere
    )

    # === AI Model Configuration ===
    MODEL_NAME: str = "default-model"
    DEVICE: str = "cpu"
    MAX_TOKENS: int = 512

    # === API Configuration ===
    HOST: str = "127.0.0.1"
    PORT: int = 8001
    DEBUG: bool = True

    # === CORS / Frontend ===
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"


if __name__ == "__main__":
    settings = Settings()
    print("MODEL_NAME:", settings.MODEL_NAME)
    print("DEVICE:", settings.DEVICE)
    print("MAX_TOKENS:", settings.MAX_TOKENS)
    print("HOST:", settings.HOST)
    print("PORT:", settings.PORT)
    print("DEBUG:", settings.DEBUG)
    print("ALLOWED_ORIGINS:", settings.ALLOWED_ORIGINS)
