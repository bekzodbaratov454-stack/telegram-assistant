from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_api_id: int
    telegram_api_hash: str
    telegram_phone: str

    ai_provider: str = "groq"
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    user_name: str = "Bekzod Baratov"
    user_about: str = ""
    user_tone: str = "introvert, aniq va lo'nda"
    persona: str = "bekzod"

    max_history_messages: int = 20
    min_reply_delay: float = 3.0
    max_reply_delay: float = 10.0
    control_command_prefix: str = ".ai"

    data_dir: str = "data"
    session_name: str = "data/telegram_session"
    db_path: str = "data/conversations.db"
    control_state_path: str = "data/control.json"


def get_settings() -> Settings:
    return Settings()
