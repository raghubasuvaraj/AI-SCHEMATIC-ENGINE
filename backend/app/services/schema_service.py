"""
Schema introspection service with multi-database support.
Supports: MySQL, PostgreSQL, MSSQL, Oracle, SQLite
"""
from typing import Dict, List, Optional
from sqlalchemy import text, inspect
from backend.app.config import get_settings
from backend.app.models.schema import Column, EnumValue, ForeignKey, SchemaSnapshot, Table
from backend.app.storage.state_store import JsonState
from backend.app.utils.db import get_engine
from backend.app.services.join_service import auto_approve_joins_from_schema

schema_cache = JsonState("backend/app/storage/schema_snapshot.json")


# ===== Database-specific introspection queries =====

def _introspect_mysql(conn, db_name: str) -> tuple:
    """Introspect MySQL/MariaDB database."""
    columns_rows = conn.execute(
        text("""
            SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_DEFAULT, IS_NULLABLE,
                   COLUMN_KEY, COLUMN_COMMENT, EXTRA, COLUMN_TYPE
              FROM INFORMATION_SCHEMA.COLUMNS
             WHERE TABLE_SCHEMA = :db
             ORDER BY TABLE_NAME, ORDINAL_POSITION
        """),
        {"db": db_name},
    ).mappings()

    pk_rows = conn.execute(
        text("""
            SELECT TABLE_NAME, COLUMN_NAME
              FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
             WHERE TABLE_SCHEMA = :db AND CONSTRAINT_NAME = 'PRIMARY'
        """),
        {"db": db_name},
    ).mappings()

    fk_rows = conn.execute(
        text("""
            SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME, CONSTRAINT_NAME
              FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
             WHERE TABLE_SCHEMA = :db AND REFERENCED_TABLE_NAME IS NOT NULL
        """),
        {"db": db_name},
    ).mappings()

    return list(columns_rows), list(pk_rows), list(fk_rows)


def _introspect_postgres(conn, db_name: str) -> tuple:
    """Introspect PostgreSQL database."""
    columns_rows = conn.execute(
        text("""
            SELECT 
                t.table_name AS "TABLE_NAME",
                c.column_name AS "COLUMN_NAME",
                c.data_type AS "DATA_TYPE",
                c.column_default AS "COLUMN_DEFAULT",
                c.is_nullable AS "IS_NULLABLE",
                CASE WHEN pk.column_name IS NOT NULL THEN 'PRI' ELSE '' END AS "COLUMN_KEY",
                COALESCE(pgd.description, '') AS "COLUMN_COMMENT",
                '' AS "EXTRA",
                c.udt_name AS "COLUMN_TYPE"
            FROM information_schema.tables t
            JOIN information_schema.columns c 
                ON t.table_name = c.table_name AND t.table_schema = c.table_schema
            LEFT JOIN (
                SELECT kcu.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public'
            ) pk ON c.table_name = pk.table_name AND c.column_name = pk.column_name
            LEFT JOIN pg_catalog.pg_description pgd
                ON pgd.objsubid = c.ordinal_position
                AND pgd.objoid = (SELECT oid FROM pg_catalog.pg_class WHERE relname = c.table_name)
            WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
            ORDER BY t.table_name, c.ordinal_position
        """)
    ).mappings()

    pk_rows = conn.execute(
        text("""
            SELECT kcu.table_name AS "TABLE_NAME", kcu.column_name AS "COLUMN_NAME"
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public'
        """)
    ).mappings()

    fk_rows = conn.execute(
        text("""
            SELECT 
                kcu.table_name AS "TABLE_NAME",
                kcu.column_name AS "COLUMN_NAME",
                ccu.table_name AS "REFERENCED_TABLE_NAME",
                ccu.column_name AS "REFERENCED_COLUMN_NAME",
                tc.constraint_name AS "CONSTRAINT_NAME"
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
        """)
    ).mappings()

    return list(columns_rows), list(pk_rows), list(fk_rows)


def _introspect_mssql(conn, db_name: str) -> tuple:
    """Introspect Microsoft SQL Server database."""
    columns_rows = conn.execute(
        text("""
            SELECT 
                t.name AS TABLE_NAME,
                c.name AS COLUMN_NAME,
                ty.name AS DATA_TYPE,
                OBJECT_DEFINITION(c.default_object_id) AS COLUMN_DEFAULT,
                CASE WHEN c.is_nullable = 1 THEN 'YES' ELSE 'NO' END AS IS_NULLABLE,
                CASE WHEN pk.column_id IS NOT NULL THEN 'PRI' ELSE '' END AS COLUMN_KEY,
                ISNULL(ep.value, '') AS COLUMN_COMMENT,
                CASE WHEN c.is_identity = 1 THEN 'auto_increment' ELSE '' END AS EXTRA,
                ty.name AS COLUMN_TYPE
            FROM sys.tables t
            INNER JOIN sys.columns c ON t.object_id = c.object_id
            INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
            LEFT JOIN (
                SELECT ic.object_id, ic.column_id
                FROM sys.index_columns ic
                JOIN sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id
                WHERE i.is_primary_key = 1
            ) pk ON c.object_id = pk.object_id AND c.column_id = pk.column_id
            LEFT JOIN sys.extended_properties ep 
                ON ep.major_id = c.object_id AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
            ORDER BY t.name, c.column_id
        """)
    ).mappings()

    pk_rows = conn.execute(
        text("""
            SELECT t.name AS TABLE_NAME, c.name AS COLUMN_NAME
            FROM sys.tables t
            JOIN sys.index_columns ic ON t.object_id = ic.object_id
            JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
            JOIN sys.indexes i ON ic.object_id = i.object_id AND ic.index_id = i.index_id
            WHERE i.is_primary_key = 1
        """)
    ).mappings()

    fk_rows = conn.execute(
        text("""
            SELECT 
                tp.name AS TABLE_NAME,
                cp.name AS COLUMN_NAME,
                tr.name AS REFERENCED_TABLE_NAME,
                cr.name AS REFERENCED_COLUMN_NAME,
                fk.name AS CONSTRAINT_NAME
            FROM sys.foreign_keys fk
            JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            JOIN sys.tables tp ON fkc.parent_object_id = tp.object_id
            JOIN sys.columns cp ON fkc.parent_object_id = cp.object_id AND fkc.parent_column_id = cp.column_id
            JOIN sys.tables tr ON fkc.referenced_object_id = tr.object_id
            JOIN sys.columns cr ON fkc.referenced_object_id = cr.object_id AND fkc.referenced_column_id = cr.column_id
        """)
    ).mappings()

    return list(columns_rows), list(pk_rows), list(fk_rows)


def _introspect_oracle(conn, db_name: str) -> tuple:
    """Introspect Oracle database."""
    columns_rows = conn.execute(
        text("""
            SELECT 
                atc.TABLE_NAME,
                atc.COLUMN_NAME,
                atc.DATA_TYPE,
                atc.DATA_DEFAULT AS COLUMN_DEFAULT,
                atc.NULLABLE AS IS_NULLABLE,
                CASE WHEN acc.CONSTRAINT_TYPE = 'P' THEN 'PRI' ELSE '' END AS COLUMN_KEY,
                NVL(acc.COMMENTS, '') AS COLUMN_COMMENT,
                '' AS EXTRA,
                atc.DATA_TYPE AS COLUMN_TYPE
            FROM ALL_TAB_COLUMNS atc
            LEFT JOIN ALL_COL_COMMENTS acc 
                ON atc.TABLE_NAME = acc.TABLE_NAME AND atc.COLUMN_NAME = acc.COLUMN_NAME
            LEFT JOIN (
                SELECT ac.TABLE_NAME, acc2.COLUMN_NAME, ac.CONSTRAINT_TYPE
                FROM ALL_CONSTRAINTS ac
                JOIN ALL_CONS_COLUMNS acc2 ON ac.CONSTRAINT_NAME = acc2.CONSTRAINT_NAME
                WHERE ac.CONSTRAINT_TYPE = 'P'
            ) pk ON atc.TABLE_NAME = pk.TABLE_NAME AND atc.COLUMN_NAME = pk.COLUMN_NAME
            WHERE atc.OWNER = UPPER(:db)
            ORDER BY atc.TABLE_NAME, atc.COLUMN_ID
        """),
        {"db": db_name},
    ).mappings()

    pk_rows = conn.execute(
        text("""
            SELECT ac.TABLE_NAME, acc.COLUMN_NAME
            FROM ALL_CONSTRAINTS ac
            JOIN ALL_CONS_COLUMNS acc ON ac.CONSTRAINT_NAME = acc.CONSTRAINT_NAME
            WHERE ac.CONSTRAINT_TYPE = 'P' AND ac.OWNER = UPPER(:db)
        """),
        {"db": db_name},
    ).mappings()

    fk_rows = conn.execute(
        text("""
            SELECT 
                ac.TABLE_NAME,
                acc.COLUMN_NAME,
                rc.TABLE_NAME AS REFERENCED_TABLE_NAME,
                rcc.COLUMN_NAME AS REFERENCED_COLUMN_NAME,
                ac.CONSTRAINT_NAME
            FROM ALL_CONSTRAINTS ac
            JOIN ALL_CONS_COLUMNS acc ON ac.CONSTRAINT_NAME = acc.CONSTRAINT_NAME
            JOIN ALL_CONSTRAINTS rc ON ac.R_CONSTRAINT_NAME = rc.CONSTRAINT_NAME
            JOIN ALL_CONS_COLUMNS rcc ON rc.CONSTRAINT_NAME = rcc.CONSTRAINT_NAME
            WHERE ac.CONSTRAINT_TYPE = 'R' AND ac.OWNER = UPPER(:db)
        """),
        {"db": db_name},
    ).mappings()

    return list(columns_rows), list(pk_rows), list(fk_rows)


def _introspect_sqlite(conn, db_name: str) -> tuple:
    """Introspect SQLite database using SQLAlchemy inspector."""
    inspector = inspect(conn)
    
    columns_list = []
    pk_list = []
    fk_list = []
    
    for table_name in inspector.get_table_names():
        # Get columns
        columns = inspector.get_columns(table_name)
        pk_cols = inspector.get_pk_constraint(table_name).get("constrained_columns", [])
        fks = inspector.get_foreign_keys(table_name)
        
        for col in columns:
            columns_list.append({
                "TABLE_NAME": table_name,
                "COLUMN_NAME": col["name"],
                "DATA_TYPE": str(col["type"]),
                "COLUMN_DEFAULT": col.get("default"),
                "IS_NULLABLE": "YES" if col.get("nullable", True) else "NO",
                "COLUMN_KEY": "PRI" if col["name"] in pk_cols else "",
                "COLUMN_COMMENT": "",
                "EXTRA": "",
                "COLUMN_TYPE": str(col["type"]),
            })
        
        for pk_col in pk_cols:
            pk_list.append({"TABLE_NAME": table_name, "COLUMN_NAME": pk_col})
        
        for fk in fks:
            for i, col in enumerate(fk.get("constrained_columns", [])):
                fk_list.append({
                    "TABLE_NAME": table_name,
                    "COLUMN_NAME": col,
                    "REFERENCED_TABLE_NAME": fk.get("referred_table"),
                    "REFERENCED_COLUMN_NAME": fk.get("referred_columns", [None])[i] if fk.get("referred_columns") else None,
                    "CONSTRAINT_NAME": fk.get("name", f"fk_{table_name}_{col}"),
                })
    
    return columns_list, pk_list, fk_list


# ===== Main introspection function =====

def introspect_schema() -> SchemaSnapshot:
    """
    Reads metadata from database. Supports MySQL, PostgreSQL, MSSQL, Oracle, SQLite.
    Does NOT touch table data - only metadata.
    """
    settings = get_settings()
    db_name = settings.db.database
    dialect = settings.db.dialect.lower()
    engine = get_engine()
    
    with engine.connect() as conn:
        # Set read-only mode where supported
        if settings.db.read_only:
            if dialect == "mysql":
                try:
                    conn.execute(text("SET SESSION TRANSACTION READ ONLY"))
                except:
                    pass  # Some MySQL versions don't support this
            elif dialect in ("postgres", "postgresql"):
                try:
                    conn.execute(text("SET TRANSACTION READ ONLY"))
                except:
                    pass
        
        # Get database-specific introspection
        if dialect == "mysql":
            columns_rows, pk_rows, fk_rows = _introspect_mysql(conn, db_name)
        elif dialect in ("postgres", "postgresql"):
            columns_rows, pk_rows, fk_rows = _introspect_postgres(conn, db_name)
        elif dialect in ("mssql", "sqlserver"):
            columns_rows, pk_rows, fk_rows = _introspect_mssql(conn, db_name)
        elif dialect == "oracle":
            columns_rows, pk_rows, fk_rows = _introspect_oracle(conn, db_name)
        elif dialect == "sqlite":
            columns_rows, pk_rows, fk_rows = _introspect_sqlite(conn, db_name)
        else:
            raise ValueError(f"Unsupported dialect: {dialect}")
        
        # Build maps
        pk_map: Dict[str, List[str]] = {}
        for row in pk_rows:
            pk_map.setdefault(row["TABLE_NAME"], []).append(row["COLUMN_NAME"])
        
        fk_map: Dict[str, Dict[str, ForeignKey]] = {}
        for row in fk_rows:
            if row.get("REFERENCED_TABLE_NAME"):
                fk_map.setdefault(row["TABLE_NAME"], {})[row["COLUMN_NAME"]] = ForeignKey(
                    column=row["COLUMN_NAME"],
                    ref_table=row["REFERENCED_TABLE_NAME"],
                    ref_column=row["REFERENCED_COLUMN_NAME"],
                    constraint_name=row.get("CONSTRAINT_NAME", ""),
                )
        
        # Build schema
        enums: List[EnumValue] = []
        tables: Dict[str, Table] = {}
        
        for row in columns_rows:
            tname = row["TABLE_NAME"]
            pk_cols = pk_map.get(tname, [])
            fk_for_table = fk_map.get(tname, {})
            
            column = Column(
                name=row["COLUMN_NAME"],
                data_type=row["DATA_TYPE"],
                is_nullable=row["IS_NULLABLE"] == "YES" or row["IS_NULLABLE"] == "Y",
                is_primary=row["COLUMN_NAME"] in pk_cols,
                is_foreign=row["COLUMN_NAME"] in fk_for_table,
                foreign_key=fk_for_table.get(row["COLUMN_NAME"]),
                default=row.get("COLUMN_DEFAULT"),
                comment=row.get("COLUMN_COMMENT", ""),
            )
            
            # Handle enum types (MySQL specific)
            if row["DATA_TYPE"] == "enum" and row.get("COLUMN_TYPE"):
                raw = row["COLUMN_TYPE"]
                if raw.startswith("enum(") and raw.endswith(")"):
                    values = raw[5:-1].split(",")
                    enums.append(
                        EnumValue(
                            table=tname,
                            column=row["COLUMN_NAME"],
                            values=[v.strip("'") for v in values]
                        )
                    )
            
            tables.setdefault(tname, Table(name=tname, columns=[], comment=None)).columns.append(column)
        
        snapshot = SchemaSnapshot(
            tables=list(tables.values()),
            enums=enums,
            dialect=dialect,
            database=db_name,
        )
        schema_cache.save(snapshot.model_dump())
        
        # Auto-approve joins from foreign key relationships
        auto_approve_joins_from_schema(snapshot)
        
        return snapshot


def load_cached_schema() -> Optional[SchemaSnapshot]:
    """Load schema from cache."""
    data = schema_cache.load()
    if not data:
        return None
    snapshot = SchemaSnapshot.model_validate(data)
    
    # Auto-approve joins from foreign key relationships
    auto_approve_joins_from_schema(snapshot)
    
    return snapshot


def get_table_names() -> List[str]:
    """Get list of table names from cached or live schema."""
    schema = load_cached_schema() or introspect_schema()
    return [t.name for t in schema.tables]


def get_table_columns(table_name: str) -> List[Column]:
    """Get columns for a specific table."""
    schema = load_cached_schema() or introspect_schema()
    for table in schema.tables:
        if table.name == table_name:
            return table.columns
    return []
