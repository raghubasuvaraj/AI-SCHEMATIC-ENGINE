"""
API routes for dynamic database configuration and table analysis.
"""
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from backend.app.config import get_settings
from backend.app.utils.db import get_engine, test_connection
from backend.app.services.schema_service import introspect_schema, load_cached_schema
from backend.app.services.table_analyzer_service import auto_analyze_and_map_tables
from backend.app.services.mapping_service import get_mapping_state, save_mapping_state
from backend.app.models.mapping import MappingState

router = APIRouter(prefix="/database", tags=["database"])


class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    dialect: str = "mysql"
    host: str = "127.0.0.1"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = ""


@router.get("/config", summary="Get current database configuration")
def get_config():
    """Get current database configuration (password masked)."""
    settings = get_settings()
    return {
        "dialect": settings.db.dialect,
        "host": settings.db.host,
        "port": settings.db.port,
        "user": settings.db.user,
        "database": settings.db.database,
        "password_set": bool(settings.db.password),
        "read_only": settings.db.read_only,
    }


@router.post("/config", summary="Update database configuration")
def update_config(config: DatabaseConfig):
    """
    Update database configuration dynamically.
    Note: This updates environment variables for the current session.
    For permanent changes, update the .env file.
    """
    # Update environment variables
    os.environ["DB_DIALECT"] = config.dialect
    os.environ["DB_HOST"] = config.host
    os.environ["DB_PORT"] = str(config.port)
    os.environ["DB_USER"] = config.user
    if config.password:
        os.environ["DB_PASSWORD"] = config.password
    os.environ["DB_NAME"] = config.database
    
    # Test connection with new config
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return {
            "success": True,
            "message": f"Connected to {config.database} on {config.host}",
            "config": {
                "dialect": config.dialect,
                "host": config.host,
                "port": config.port,
                "database": config.database,
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "config": None
        }


@router.get("/test", summary="Test database connection")
def test_db_connection():
    """Test the current database connection."""
    result = test_connection()
    settings = get_settings()
    return {
        **result,
        "config": {
            "dialect": settings.db.dialect,
            "host": settings.db.host,
            "port": settings.db.port,
            "database": settings.db.database,
        }
    }


@router.post("/analyze", summary="Auto-analyze tables and create mappings")
def analyze_tables(include_row_counts: bool = True):
    """
    Automatically analyze all tables and classify them as fact or dimension tables.
    Creates mappings based on analysis.
    """
    try:
        snapshot = load_cached_schema() or introspect_schema()
        results = auto_analyze_and_map_tables(snapshot, include_row_counts)
        return {
            "success": True,
            "database": snapshot.database,
            "dialect": snapshot.dialect,
            **results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/refresh", summary="Refresh schema and re-analyze")
def refresh_and_analyze():
    """Introspect schema fresh and auto-analyze tables."""
    try:
        # Force fresh introspection
        snapshot = introspect_schema()
        results = auto_analyze_and_map_tables(snapshot, include_row_counts=True)
        return {
            "success": True,
            "message": "Schema refreshed and tables analyzed",
            "database": snapshot.database,
            "tables_count": len(snapshot.tables),
            **results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")


@router.delete("/mappings/clear", summary="Clear all table mappings")
def clear_mappings():
    """Clear all table mappings."""
    save_mapping_state(MappingState(tables=[], columns=[]))
    return {"message": "All mappings cleared"}


@router.get("/supported-dialects", summary="Get list of supported database dialects")
def supported_dialects():
    """Get list of supported database dialects."""
    return {
        "dialects": [
            {"name": "mysql", "label": "MySQL", "default_port": 3306},
            {"name": "postgres", "label": "PostgreSQL", "default_port": 5432},
            {"name": "mssql", "label": "SQL Server", "default_port": 1433},
            {"name": "oracle", "label": "Oracle", "default_port": 1521},
            {"name": "sqlite", "label": "SQLite", "default_port": None},
        ]
    }

