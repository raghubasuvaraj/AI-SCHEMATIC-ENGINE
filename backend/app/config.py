import os
from pydantic import BaseModel, Field


class DatabaseSettings(BaseModel):
    dialect: str = Field("mysql", description="SQL dialect name (mysql, postgres, mssql)")
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = ""
    read_only: bool = True


class OpenAISettings(BaseModel):
    api_key: str = ""
    model: str = "gpt-4o-mini"


class SecuritySettings(BaseModel):
    tenant_column: str = Field("tenant_id", description="Tenant isolation column name")
    require_tenant_filter: bool = Field(True, description="Require tenant filter in all queries")
    max_limit: int = 500


class Settings(BaseModel):
    db: DatabaseSettings = DatabaseSettings()
    openai: OpenAISettings = OpenAISettings()
    security: SecuritySettings = SecuritySettings()
    audit_log_path: str = "backend/app/storage/audit.log"


def get_settings() -> Settings:
    return Settings(
        db=DatabaseSettings(
            dialect=os.getenv("DB_DIALECT", "mysql"),
            host=os.getenv("DB_HOST", "127.0.0.1"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", ""),
            read_only=os.getenv("DB_READ_ONLY", "true").lower() == "true",
        ),
        openai=OpenAISettings(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        ),
        security=SecuritySettings(
            tenant_column=os.getenv("TENANT_COLUMN", "tenant_id"),
            require_tenant_filter=os.getenv("REQUIRE_TENANT_FILTER", "false").lower() == "true",
            max_limit=int(os.getenv("MAX_LIMIT", "500")),
        ),
        audit_log_path=os.getenv("AUDIT_LOG_PATH", "backend/app/storage/audit.log"),
    )
