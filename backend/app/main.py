import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from backend.app.routes import schema_routes, mapping_routes, join_routes, plan_routes, audit_routes, questions_routes, history_routes, database_routes

# Load .env from current working directory (project root when running uvicorn)
load_dotenv(override=True)

app = FastAPI(
    title="Semantic Query Engine (Plan-only)",
    description="LLM-assisted planning, deterministic SQL compilation, and audit-safe execution.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(schema_routes.router)
app.include_router(mapping_routes.router)
app.include_router(join_routes.router)
app.include_router(plan_routes.router)
app.include_router(audit_routes.router)
app.include_router(questions_routes.router)
app.include_router(history_routes.router)
app.include_router(database_routes.router)


@app.get("/health")
def health():
    return {"status": "ok"}
