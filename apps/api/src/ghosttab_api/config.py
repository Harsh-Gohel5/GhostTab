from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GHOSTTAB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )
    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///.ghosttab/ghosttab.db"
    auth_mode: Literal["local", "supabase"] = "local"
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    frontend_url: str = "http://127.0.0.1:5173"
    google_client_id: str = ""
    google_client_secret: SecretStr = SecretStr("")
    google_redirect_uri: str = "http://127.0.0.1:8000/api/connections/google/callback"
    google_sources_callback_base: str = "http://127.0.0.1:8000/api/integrations/google"
    slack_client_id: str = ""
    slack_client_secret: SecretStr = SecretStr("")
    slack_redirect_uri: str = "http://127.0.0.1:8000/api/integrations/slack/callback"
    jira_client_id: str = ""
    jira_client_secret: SecretStr = SecretStr("")
    jira_redirect_uri: str = "http://127.0.0.1:8000/api/integrations/jira/callback"
    token_encryption_key: SecretStr = SecretStr("")
    model_api_key: SecretStr = Field(default=SecretStr(""), validation_alias="MODEL_API_KEY")
    meta_model_id: Literal["muse-spark-1.3", "muse-wonder-1.0"] = Field(
        default="muse-spark-1.3", validation_alias="META_MODEL_ID"
    )
    model_budget_usd: float = Field(default=10, ge=0, le=150)
    allow_model_requests: bool = False
    synthetic_demo: bool = False

    @property
    def google_ready(self) -> bool:
        return bool(
            self.google_client_id
            and self.google_client_secret.get_secret_value()
            and self.token_encryption_key.get_secret_value()
        )

    @model_validator(mode="after")
    def validate_deployment(self):
        if self.auth_mode == "supabase" and not (
            self.supabase_url.startswith("https://") and self.supabase_publishable_key
        ):
            raise ValueError("Supabase mode requires an HTTPS project URL and publishable key")
        if self.environment == "production":
            if self.auth_mode != "supabase" or not self.database_url.startswith("postgresql"):
                raise ValueError("Production requires Supabase authentication and PostgreSQL")
            if not self.frontend_url.startswith("https://"):
                raise ValueError("Production requires an HTTPS frontend URL")
        return self
