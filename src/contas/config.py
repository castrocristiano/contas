from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://contas:contas@localhost:5432/contas"
    openapi_key: str = ""
    openai_api_key: str = ""
    openaiapi_key: str = ""
    openai_store: bool = True
    debug: bool = False

    @property
    def effective_openai_api_key(self) -> str:
        import os
        from pathlib import Path

        key = (
            self.openapi_key
            or self.openai_api_key
            or self.openaiapi_key
            or os.getenv("OPENAPI_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
            or os.getenv("OPENAIAPI_KEY", "")
        )
        if not key:
            key_file = Path.home() / ".openai_key"
            if key_file.is_file():
                key = key_file.read_text(encoding="utf-8").strip()

        return key


settings = Settings()
