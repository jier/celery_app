from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"
    otel_exporter_otlp_endpoint: str = "http://localhost:4318"

    model_config = {"env_file": ".env", "extra": "ignore"}
