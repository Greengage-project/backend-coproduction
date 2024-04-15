import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn, validator
import os


class Settings(BaseSettings):
    SECRET_KEY: str = secrets.token_urlsafe(32)
    BACKEND_SECRET: str

    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    PROTOCOL: str
    SERVER_NAME: str
    BASE_PATH: str
    COMPLETE_SERVER_NAME: AnyHttpUrl = os.getenv(
        "PROTOCOL") + os.getenv("SERVER_NAME") + os.getenv("BASE_PATH")
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME = "Coproduction API"

    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    DEFAULT_LANGUAGE: str
    ALLOWED_LANGUAGES_LIST: list = os.getenv(
        "ALLOWED_LANGUAGES", "").split(",")

    # OTHER MICROS
    CATALOGUE_SERVICE_NAME: str
    CATALOGUE_PORT: int
    CATALOGUE_SERVICE: str = os.getenv(
        "CATALOGUE_SERVICE_NAME") + ":" + os.getenv("CATALOGUE_PORT")

    # MAIL
    SMTP_TLS: bool = os.getenv("SMTP_TLS", False)
    SMTP_PORT: Optional[int] = os.getenv("SMTP_PORT", 25)
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    EMAILS_FROM_EMAIL: Optional[str] = os.getenv(
        "EMAILS_FROM_EMAIL", "support@greengage-project.eu")
    EMAILS_FROM_NAME: Optional[str] = os.getenv(
        "EMAILS_FROM_NAME", "Greengage Project")
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    EMAIL_TEMPLATES_DIR: str = "/app/email-templates/build"
    EMAILS_ENABLED: bool = True

    KEYCLOAK_CLIENT_ID: str
    KEYCLOAK_CLIENT_SECRET: str
    KEYCLOAK_REALM: str
    KEYCLOAK_URL_REALM: str

    @validator("EMAILS_ENABLED", pre=True)
    def get_emails_enabled(cls, v: bool, values: Dict[str, Any]) -> bool:
        return bool(
            values.get("SMTP_HOST")
            and values.get("SMTP_PORT")
            and values.get("EMAILS_FROM_EMAIL")
        )

    EMAIL_TEST_USER: str = "test@example.com"  # type: ignore

    class Config:
        case_sensitive = True


settings = Settings()
