from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    debug: bool = False
    firefox_remote: str = 'http://localhost:4444/wd/hub'
    downloads_dir: str = 'downloads'
    downloads_threads: int = 3
    watch_model_url: str

    class Config:
        env_nested_delimiter = '__'


settings = Settings()