"""
Database utilities with multi-database support.
Supports: MySQL, PostgreSQL, MSSQL, Oracle, SQLite
"""
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from sqlalchemy.pool import QueuePool, NullPool
from backend.app.config import get_settings


# Database dialect configuration
DB_DIALECTS = {
    "mysql": {
        "drivername": "mysql+mysqlconnector",
        "connect_args": {"ssl_disabled": True},
        "pool_class": QueuePool,
    },
    "postgres": {
        "drivername": "postgresql+psycopg2",
        "connect_args": {},
        "pool_class": QueuePool,
    },
    "postgresql": {
        "drivername": "postgresql+psycopg2",
        "connect_args": {},
        "pool_class": QueuePool,
    },
    "mssql": {
        "drivername": "mssql+pyodbc",
        "connect_args": {"driver": "ODBC Driver 17 for SQL Server"},
        "pool_class": QueuePool,
    },
    "sqlserver": {
        "drivername": "mssql+pyodbc",
        "connect_args": {"driver": "ODBC Driver 17 for SQL Server"},
        "pool_class": QueuePool,
    },
    "oracle": {
        "drivername": "oracle+cx_oracle",
        "connect_args": {},
        "pool_class": QueuePool,
    },
    "sqlite": {
        "drivername": "sqlite",
        "connect_args": {"check_same_thread": False},
        "pool_class": NullPool,
    },
}


def get_dialect_config(dialect: str) -> Dict[str, Any]:
    """Get database dialect configuration."""
    dialect_lower = dialect.lower()
    if dialect_lower not in DB_DIALECTS:
        supported = ", ".join(DB_DIALECTS.keys())
        raise ValueError(f"Unsupported dialect '{dialect}'. Supported: {supported}")
    return DB_DIALECTS[dialect_lower]


def get_engine() -> Engine:
    """Create database engine based on configuration."""
    settings = get_settings()
    db = settings.db
    
    config = get_dialect_config(db.dialect)
    
    # Handle SQLite separately (file-based)
    if db.dialect.lower() == "sqlite":
        return create_engine(
            f"sqlite:///{db.database}",
            poolclass=config["pool_class"],
            connect_args=config["connect_args"],
        )
    
    # Use URL.create() to properly handle special characters in password
    url = URL.create(
        drivername=config["drivername"],
        username=db.user,
        password=db.password,
        host=db.host,
        port=db.port,
        database=db.database,
    )
    
    return create_engine(
        url,
        poolclass=config["pool_class"],
        pool_size=5,
        max_overflow=5,
        connect_args=config["connect_args"],
    )


def test_connection() -> Dict[str, Any]:
    """Test database connection and return status."""
    settings = get_settings()
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Simple query to test connection
            if settings.db.dialect.lower() in ("mysql", "postgres", "postgresql"):
                result = conn.execute(text("SELECT 1 as test"))
            elif settings.db.dialect.lower() in ("mssql", "sqlserver"):
                result = conn.execute(text("SELECT 1 as test"))
            elif settings.db.dialect.lower() == "oracle":
                result = conn.execute(text("SELECT 1 FROM DUAL"))
            else:
                result = conn.execute(text("SELECT 1"))
            
            row = result.fetchone()
            return {
                "status": "connected",
                "dialect": settings.db.dialect,
                "host": settings.db.host,
                "port": settings.db.port,
                "database": settings.db.database,
                "user": settings.db.user,
                "test_result": row[0] if row else None,
            }
    except Exception as e:
        return {
            "status": "error",
            "dialect": settings.db.dialect,
            "host": settings.db.host,
            "port": settings.db.port,
            "database": settings.db.database,
            "error": str(e),
        }


def get_supported_dialects() -> list:
    """Return list of supported database dialects."""
    return list(set([
        "mysql", "postgres", "postgresql", "mssql", "sqlserver", "oracle", "sqlite"
    ]))
