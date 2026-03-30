from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    session_secret: str
    db_path: str = "/data/db.sqlite3"
    context_dir: str = "/data/context"
    model: str = "claude-sonnet-4-6"

    class Config:
        env_file = ".env"


settings = Settings()
