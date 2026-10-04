from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "TaxTrace"
    app_env: str = "development"
    database_url: str = "sqlite:///./taxtrace.db"
    secret_key: str = "dev-secret-key-must-be-at-least-32-bytes-long!"
    storage_dir: str = "./storage_vault"
    max_upload_size_bytes: int = 25 * 1024 * 1024  # 25 MB
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Security settings
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    # Rate limiting
    rate_limit_requests_per_minute: int = 200
    rate_limit_requests_per_hour: int = 5000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
