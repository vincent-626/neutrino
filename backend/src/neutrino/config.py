from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    loki_url: str = "http://loki:3100"
    cache_ttl_seconds: int = 21600  # 6 hours
    max_log_lines: int = 5000
    top_k: int = 25
    model_name: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"


settings = Settings()
