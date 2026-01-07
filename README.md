# AP Semantic Query Engine

FastAPI backend + React/Vite/Tailwind frontend that turns natural language questions into a **canonical query plan JSON**, validates it, and deterministically compiles SQL using only approved schema objects and joins. LLM usage is confined to intent detection and plan drafting—SQL is never produced by an LLM.

## Backend (FastAPI)
- Code: `backend/app`
- Run: `python -m venv .venv && .venv\Scripts\activate && pip install -r backend/requirements.txt`
- Start API: `uvicorn backend.app.main:app --reload --env-file .env`
- Env (`.env`): set `DB_DIALECT`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `OPENAI_API_KEY`, `TENANT_COLUMN` (default `tenant_id`), `MAX_LIMIT`.

### Modules
- **Schema Introspection**: `/schema` reads `information_schema` only; caches to `backend/app/storage/schema_snapshot.json`; no table data is read.
- **Human-in-the-loop mappings**: `/mappings` CRUD for fact/dim roles, priorities (Gold/Silver/Bronze), column meanings, tenant column.
- **Join approvals**: `/joins/suggestions` from FK metadata, `/joins/approve` stores only human-approved joins.
- **Intent detection**: `/intent/detect` prompt-only classifier (no schema in prompt).
- **Planner**: `/plan/build` creates canonical plan JSON using approved schema lists.
- **Validator**: `/plan/validate` enforces table/column existence, tenant filter, allowed aggs, join availability, limit ceiling.
- **Deterministic SQL compiler**: `/plan/compile` -> SQL string + params via fixed templates + approved joins; **no execution**.
- **SQL safety**: blocks DDL/DML, multi-statements, catalog access.
- **Audit**: logs to `backend/app/storage/audit.log`; view with `/audit/logs`.

Canonical plan contract:
```json
{
  "intent": "",
  "fact_table": "",
  "dimensions": [],
  "metrics": [],
  "filters": [],
  "group_by": [],
  "order_by": [],
  "limit": 100
}
```

## Frontend (React + Vite + Tailwind)
- Code: `frontend`
- Install: `cd frontend && npm install`
- Dev server: `npm run dev` (Vite 7 recommends Node ≥20; 18 works with warnings)
- Build: `npm run build`
- API base URL: set `VITE_API_BASE` (defaults to `http://localhost:8000`).
- Screens: NL input → intent + plan, schema/mapping capture, FK join approvals, plan validation, deterministic SQL display (no execution).

## Workflow
1) Set env + start backend.
2) `Introspect Schema` in UI to cache metadata; review FK join suggestions and approve required edges.
3) Mark fact/dimension tables, priorities, tenant column, and column meanings.
4) Enter a NL question → Detect intent → Build plan.
5) Validate plan (enforces tenant filter + approved objects) → Compile SQL (deterministic templates).
6) Audit trail is written for each compilation; retrieve via `/audit/logs`.

## Safety Guarantees
- LLM limited to intent + plan drafting; schema lists provided explicitly; SQL generation is template-only.
- Validation ensures tables/columns exist, joins are approved, aggregations allowed, tenant filter present, limit capped.
- Safety validator blocks DDL/DML and multi-statements.
- No table data is read during introspection; only `information_schema` is queried.
