from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://contas:contas@localhost:5432/contas"
    openai_api_key: str = ""
    openapi_key: str = ""
    debug: bool = False

    @property
    def effective_openai_api_key(self) -> str:
        return self.openapi_key or self.openai_api_key


settings = Settings()
