from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    firefox_remote: str = 'http://localhost:4444/wd/hub'
    watch_model_url: str = 'https://watchmdh.to/models/annacute/'
    downloads_dir: str = 'downloads'

    class Config:
        env_nested_delimiter = '__'


settings = Settings()