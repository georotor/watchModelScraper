from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    debug: bool = False
    firefox_remote: str = 'http://localhost:4444/wd/hub'
    watch_model_url: str
    syno_tasks: int = 3
    syno_wait_timeout: int = 2
    syno_url: str
    syno_port: int = 5000
    syno_user: str
    syno_password: str

    class Config:
        env_nested_delimiter = '__'


settings = Settings()