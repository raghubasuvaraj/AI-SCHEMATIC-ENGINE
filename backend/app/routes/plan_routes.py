"""
Plan routes for the semantic query pipeline.
Provides endpoints for intent detection, plan building, validation, compilation, execution, and narration.
"""
from fastapi import APIRouter, HTTPException
from uuid import uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from openai import OpenAI
from sqlalchemy import text
from backend.app.models.plan import CanonicalPlan
from backend.app.services.intent_service import detect_intent
from backend.app.services.plan_service import build_plan
from backend.app.services.validation_service import (
    validate_plan, validate_question, validate_sql_safety,
    PlanValidationError, ValidationResult, ValidationError
)
from backend.app.services.sql_compiler import compile_sql
from backend.app.services.safety_service import assert_sql_safe, SqlSafetyError
from backend.app.services.schema_service import load_cached_schema, introspect_schema
from backend.app.services.mapping_service import get_mapping_state
from backend.app.services.join_service import get_join_graph
from backend.app.services.audit_service import log_audit
from backend.app.models.audit import AuditRecord
from backend.app.utils.db import get_engine, test_connection, get_supported_dialects
from backend.app.config import get_settings
from backend.app.services.history_service import add_to_history, QueryHistoryItem

router = APIRouter(tags=["planning"])


def _save_failed_to_history(
    question: str,
    error: str,
    intent: str = None,
    plan: dict = None,
    sql: str = None,
    execution_time_ms: int = None
):
    """Save a failed query to history."""
    try:
        settings = get_settings()
        history_item = QueryHistoryItem(
            id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            database=settings.db.database,
            question=question,
            intent=intent,
            plan=plan,
            sql=sql,
            params=None,
            row_count=None,
            execution_time_ms=execution_time_ms,
            success=False,
            error=error,
            status="failed",
        )
        add_to_history(history_item)
    except Exception:
        pass  # Don't fail if history save fails


# ===== Response Models =====

class PipelineStep(BaseModel):
    """Single pipeline step result."""
    step: str
    status: str  # pending, running, success, error
    duration_ms: Optional[int] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None


class PipelineResponse(BaseModel):
    """Complete pipeline execution response."""
    success: bool
    question: str
    intent: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    sql: Optional[str] = None
    params: Optional[List] = None
    results: Optional[Dict[str, Any]] = None
    narration: Optional[str] = None
    audit_id: Optional[str] = None
    validation_errors: Optional[List[Dict]] = None
    validation_warnings: Optional[List[Dict]] = None
    steps: List[PipelineStep] = []
    execution_time_ms: Optional[int] = None
    database_info: Optional[Dict[str, Any]] = None


# ===== Endpoints =====

@router.get("/database/status")
def database_status():
    """Check database connection status and get supported dialects."""
    connection_status = test_connection()
    return {
        "connection": connection_status,
        "supported_dialects": get_supported_dialects(),
    }


@router.post("/intent/detect")
def detect(question: dict):
    """Detect intent from natural language question."""
    q = question.get("question", "")
    
    # Validate question
    validation = validate_question(q)
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Question validation failed",
                "errors": [e.model_dump() for e in validation.errors]
            }
        )
    
    intent = detect_intent(q)
    return {
        "intent": intent,
        "question": q,
        "warnings": [w.model_dump() for w in validation.warnings] if validation.warnings else []
    }


@router.post("/plan/build")
def plan_build(payload: dict):
    """Build query plan from natural language question."""
    question = payload.get("question", "")
    
    # Validate question
    validation = validate_question(question)
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Question validation failed",
                "errors": [e.model_dump() for e in validation.errors]
            }
        )
    
    snapshot = load_cached_schema() or introspect_schema()
    mappings = get_mapping_state()
    joins = get_join_graph()
    
    try:
        plan = build_plan(question, snapshot, mappings, joins)
        return {
            "plan": plan.model_dump(),
            "warnings": [w.model_dump() for w in validation.warnings] if validation.warnings else []
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/plan/validate")
def plan_validate(plan: CanonicalPlan):
    """Validate a query plan against schema and rules."""
    snapshot = load_cached_schema() or introspect_schema()
    mappings = get_mapping_state()
    joins = get_join_graph()
    
    try:
        result = validate_plan(plan, snapshot, mappings, joins)
        return {
            "status": "valid",
            "validated_plan": result.validated_plan,
            "warnings": [w.model_dump() for w in result.warnings] if result.warnings else []
        }
    except PlanValidationError as exc:
        return {
            "status": "invalid",
            "errors": [e.model_dump() for e in exc.validation_result.errors] if exc.validation_result else exc.errors,
            "warnings": [w.model_dump() for w in exc.validation_result.warnings] if exc.validation_result else []
        }


@router.post("/plan/compile")
def plan_compile(plan: CanonicalPlan):
    """Compile validated plan to SQL."""
    snapshot = load_cached_schema() or introspect_schema()
    mappings = get_mapping_state()
    joins = get_join_graph()
    
    try:
        validate_plan(plan, snapshot, mappings, joins)
        sql, params = compile_sql(plan, snapshot, joins)
        
        # Validate SQL safety
        safety_result = validate_sql_safety(sql)
        if not safety_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "SQL safety validation failed",
                    "errors": [e.model_dump() for e in safety_result.errors]
                }
            )
        
        assert_sql_safe(sql)
    except PlanValidationError as exc:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Plan validation failed",
                "errors": [e.model_dump() for e in exc.validation_result.errors] if exc.validation_result else exc.errors
            }
        )
    except SqlSafetyError as exc:
        raise HTTPException(status_code=400, detail=exc.issues)
    
    # Create audit record
    record = AuditRecord(
        timestamp=datetime.utcnow(),
        user=None,
        request_id=str(uuid4()),
        intent=plan.intent,
        plan=plan.model_dump(),
        sql=sql,
        status="compiled",
    )
    log_audit(record)
    
    return {
        "sql": sql,
        "params": params,
        "audit_id": record.request_id,
        "dialect": get_settings().db.dialect,
    }


@router.post("/plan/execute")
def plan_execute(payload: dict):
    """Execute compiled SQL and return results (read-only queries only)."""
    sql = payload.get("sql", "")
    params = payload.get("params", [])
    audit_id = payload.get("audit_id", str(uuid4()))
    
    start_time = datetime.utcnow()
    
    # Validate SQL safety
    safety_result = validate_sql_safety(sql)
    if not safety_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "SQL safety validation failed",
                "errors": [e.model_dump() for e in safety_result.errors]
            }
        )
    
    try:
        assert_sql_safe(sql)
    except SqlSafetyError as exc:
        raise HTTPException(status_code=400, detail=exc.issues)
    
    settings = get_settings()
    if not settings.db.read_only:
        raise HTTPException(status_code=403, detail="Query execution is only allowed in read-only mode")
    
    engine = get_engine()
    try:
        with engine.connect() as conn:
            # Set read-only mode for extra safety
            dialect = settings.db.dialect.lower()
            if dialect == "mysql":
                try:
                    conn.execute(text("SET SESSION TRANSACTION READ ONLY"))
                except:
                    pass
            elif dialect in ("postgres", "postgresql"):
                try:
                    conn.execute(text("SET TRANSACTION READ ONLY"))
                except:
                    pass
            
            # Convert params list to dict for SQLAlchemy
            param_dict = {p[0].replace(":", ""): p[1] for p in params} if params else {}
            
            result = conn.execute(text(sql), param_dict)
            columns = list(result.keys())
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Log execution
            record = AuditRecord(
                timestamp=datetime.utcnow(),
                user=None,
                request_id=audit_id,
                intent="execution",
                plan={},
                sql=sql,
                status="executed",
            )
            log_audit(record)
            
            return {
                "success": True,
                "columns": columns,
                "rows": rows[:500],  # Limit rows for safety
                "row_count": len(rows),
                "truncated": len(rows) > 500,
                "execution_time_ms": duration_ms,
                "audit_id": audit_id,
                "dialect": settings.db.dialect,
            }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(exc)}")


@router.post("/plan/narrate")
def plan_narrate(payload: dict):
    """Generate a natural language explanation of the query and results."""
    question = payload.get("question", "")
    sql = payload.get("sql", "")
    results = payload.get("results", {})
    plan = payload.get("plan", {})
    
    settings = get_settings()
    if not settings.openai.api_key:
        return {"narration": "Narration requires OpenAI API key to be configured.", "success": False}
    
    # Prepare summary of results
    row_count = results.get("row_count", 0)
    columns = results.get("columns", [])
    sample_rows = results.get("rows", [])[:5]
    
    prompt = f"""You are a helpful data analyst assistant. Based on the following information, provide a clear, concise explanation of the query results.

User's Question: "{question}"

Query Plan Summary:
- Fact Table: {plan.get('fact_table', 'N/A')}
- Dimensions: {plan.get('dimensions', [])}
- Metrics: {[m.get('alias', m.get('column')) for m in plan.get('metrics', [])]}
- Filters Applied: {[f"{f.get('column')} {f.get('operator')} {f.get('value')}" for f in plan.get('filters', [])]}

Results Summary:
- Total Rows: {row_count}
- Columns: {columns}
- Sample Data: {sample_rows}

Provide a natural language summary that:
1. Answers the user's original question
2. Highlights key insights from the data
3. Mentions any notable patterns or observations
4. Is concise (2-3 sentences for simple queries, up to a paragraph for complex ones)

Do not include SQL or technical details unless specifically asked."""

    try:
        client = OpenAI(api_key=settings.openai.api_key)
        completion = client.chat.completions.create(
            model=settings.openai.model,
            messages=[
                {"role": "system", "content": "You are a helpful data analyst. Provide clear, business-friendly explanations."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=300,
        )
        narration = completion.choices[0].message.content.strip()
        return {"narration": narration, "success": True}
    except Exception as exc:
        return {"narration": f"Unable to generate narration: {str(exc)}", "success": False}


@router.post("/pipeline/run")
def run_full_pipeline(payload: dict) -> PipelineResponse:
    """
    Run the complete pipeline from question to results with all steps.
    
    Pipeline Steps:
    1. Question Validation
    2. Intent Detection (LLM)
    3. Schema Load
    4. Query Planner (LLM → JSON Plan)
    5. Plan Validator (Schema + Rules)
    6. SQL Compilation (Join Resolution + SQL Builder)
    7. SQL Safety Validation
    8. Query Execution (Optional)
    9. Narration (Optional)
    """
    start_time = datetime.utcnow()
    
    question = payload.get("question", "")
    execute_query = payload.get("execute", False)
    include_narration = payload.get("narrate", False)
    
    settings = get_settings()
    steps: List[PipelineStep] = []
    
    response = PipelineResponse(
        success=False,
        question=question,
        steps=[],
        database_info={
            "dialect": settings.db.dialect,
            "host": settings.db.host,
            "database": settings.db.database,
        }
    )
    
    # ===== Step 1: Question Validation =====
    step_start = datetime.utcnow()
    try:
        validation = validate_question(question)
        if not validation.is_valid:
            steps.append(PipelineStep(
                step="question_validation",
                status="error",
                duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000),
                errors=[e.message for e in validation.errors]
            ))
            response.steps = steps
            response.validation_errors = [e.model_dump() for e in validation.errors]
            raise HTTPException(status_code=400, detail={
                "message": "Question validation failed",
                "errors": [e.model_dump() for e in validation.errors]
            })
        
        steps.append(PipelineStep(
            step="question_validation",
            status="success",
            duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000),
            warnings=[w.message for w in validation.warnings] if validation.warnings else None
        ))
        response.validation_warnings = [w.model_dump() for w in validation.warnings] if validation.warnings else None
    except HTTPException:
        raise
    except Exception as exc:
        steps.append(PipelineStep(step="question_validation", status="error", error=str(exc)))
        response.steps = steps
        raise HTTPException(status_code=400, detail=f"Question validation failed: {str(exc)}")
    
    # ===== Step 2: Intent Detection =====
    step_start = datetime.utcnow()
    try:
        intent = detect_intent(question)
        response.intent = intent
        steps.append(PipelineStep(
            step="intent_detection",
            status="success",
            duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000),
            result=intent
        ))
    except Exception as exc:
        steps.append(PipelineStep(step="intent_detection", status="error", error=str(exc)))
        response.steps = steps
        raise HTTPException(status_code=400, detail=f"Intent detection failed: {str(exc)}")
    
    # ===== Step 3: Schema Load =====
    step_start = datetime.utcnow()
    try:
        snapshot = load_cached_schema() or introspect_schema()
        mappings = get_mapping_state()
        joins = get_join_graph()
        steps.append(PipelineStep(
            step="schema_load",
            status="success",
            duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000),
            result={
                "tables_count": len(snapshot.tables),
                "mappings_count": len(mappings.tables),
                "joins_count": len(joins.joins)
            }
        ))
    except Exception as exc:
        steps.append(PipelineStep(step="schema_load", status="error", error=str(exc)))
        response.steps = steps
        raise HTTPException(status_code=400, detail=f"Schema loading failed: {str(exc)}")
    
    # ===== Step 4: Plan Generation (LLM) =====
    step_start = datetime.utcnow()
    try:
        plan = build_plan(question, snapshot, mappings, joins)
        response.plan = plan.model_dump()
        steps.append(PipelineStep(
            step="plan_generation",
            status="success",
            duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000),
            result={
                "fact_table": plan.fact_table,
                "dimensions": plan.dimensions,
                "metrics_count": len(plan.metrics),
                "filters_count": len(plan.filters)
            }
        ))
    except Exception as exc:
        steps.append(PipelineStep(step="plan_generation", status="error", error=str(exc)))
        response.steps = steps
        _save_failed_to_history(
            question=question,
            error=f"Plan generation failed: {str(exc)}",
            intent=response.intent,
            execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
        )
        raise HTTPException(status_code=400, detail=f"Plan generation failed: {str(exc)}")
    
    # ===== Step 5: Plan Validation =====
    step_start = datetime.utcnow()
    try:
        validation_result = validate_plan(plan, snapshot, mappings, joins)
        steps.append(PipelineStep(
            step="plan_validation",
            status="success",
            duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000),
            warnings=[w.message for w in validation_result.warnings] if validation_result.warnings else None
        ))
    except PlanValidationError as exc:
        steps.append(PipelineStep(
            step="plan_validation",
            status="error",
            duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000),
            errors=exc.errors
        ))
        response.steps = steps
        response.validation_errors = [e.model_dump() for e in exc.validation_result.errors] if exc.validation_result else None
        _save_failed_to_history(
            question=question,
            error=f"Plan validation failed: {exc.errors}",
            intent=response.intent,
            plan=plan.model_dump() if plan else None,
            execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
        )
        raise HTTPException(status_code=400, detail={
            "message": "Plan validation failed",
            "errors": exc.errors
        })
    
    # ===== Step 6: SQL Compilation =====
    step_start = datetime.utcnow()
    try:
        sql, params = compile_sql(plan, snapshot, joins)
        response.sql = sql
        response.params = params
        steps.append(PipelineStep(
            step="sql_compilation",
            status="success",
            duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000),
            result={"sql_length": len(sql), "params_count": len(params)}
        ))
    except Exception as exc:
        steps.append(PipelineStep(step="sql_compilation", status="error", error=str(exc)))
        response.steps = steps
        _save_failed_to_history(
            question=question,
            error=f"SQL compilation failed: {str(exc)}",
            intent=response.intent,
            plan=plan.model_dump() if plan else None,
            execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
        )
        raise HTTPException(status_code=400, detail=f"SQL compilation failed: {str(exc)}")
    
    # ===== Step 7: SQL Safety Validation =====
    step_start = datetime.utcnow()
    try:
        safety_result = validate_sql_safety(sql)
        if not safety_result.is_valid:
            steps.append(PipelineStep(
                step="safety_validation",
                status="error",
                errors=[e.message for e in safety_result.errors]
            ))
            response.steps = steps
            raise HTTPException(status_code=400, detail={
                "message": "SQL safety validation failed",
                "errors": [e.model_dump() for e in safety_result.errors]
            })
        
        assert_sql_safe(sql)
        steps.append(PipelineStep(
            step="safety_validation",
            status="success",
            duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000),
            warnings=[w.message for w in safety_result.warnings] if safety_result.warnings else None
        ))
    except SqlSafetyError as exc:
        steps.append(PipelineStep(step="safety_validation", status="error", errors=exc.issues))
        response.steps = steps
        raise HTTPException(status_code=400, detail=exc.issues)
    
    # Create audit record
    audit_id = str(uuid4())
    record = AuditRecord(
        timestamp=datetime.utcnow(),
        user=None,
        request_id=audit_id,
        intent=plan.intent,
        plan=plan.model_dump(),
        sql=sql,
        status="compiled",
    )
    log_audit(record)
    response.audit_id = audit_id
    
    # ===== Step 8: Query Execution (Optional) =====
    if execute_query:
        step_start = datetime.utcnow()
        try:
            engine = get_engine()
            with engine.connect() as conn:
                dialect = settings.db.dialect.lower()
                if dialect == "mysql":
                    try:
                        conn.execute(text("SET SESSION TRANSACTION READ ONLY"))
                    except:
                        pass
                elif dialect in ("postgres", "postgresql"):
                    try:
                        conn.execute(text("SET TRANSACTION READ ONLY"))
                    except:
                        pass
                
                param_dict = {p[0].replace(":", ""): p[1] for p in params}
                result = conn.execute(text(sql), param_dict)
                columns = list(result.keys())
                rows = [dict(zip(columns, row)) for row in result.fetchall()]
                
                response.results = {
                    "columns": columns,
                    "rows": rows[:500],
                    "row_count": len(rows),
                    "truncated": len(rows) > 500,
                }
                steps.append(PipelineStep(
                    step="query_execution",
                    status="success",
                    duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000),
                    result={"row_count": len(rows)}
                ))
        except Exception as exc:
            steps.append(PipelineStep(step="query_execution", status="error", error=str(exc)))
            response.results = {"error": str(exc)}
    
    # ===== Step 9: Narration (Optional) =====
    if include_narration and execute_query and response.results and "rows" in response.results:
        step_start = datetime.utcnow()
        try:
            narration_result = plan_narrate({
                "question": question,
                "sql": sql,
                "results": response.results,
                "plan": plan.model_dump(),
            })
            response.narration = narration_result.get("narration")
            steps.append(PipelineStep(
                step="narration",
                status="success" if narration_result.get("success") else "error",
                duration_ms=int((datetime.utcnow() - step_start).total_seconds() * 1000),
            ))
        except Exception as exc:
            steps.append(PipelineStep(step="narration", status="error", error=str(exc)))
    
    # Finalize response
    end_time = datetime.utcnow()
    response.success = True
    response.steps = steps
    response.execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
    
    # Save to history
    try:
        # Use plan's intent (human-readable) if available, otherwise use detect_intent result
        plan_intent = response.plan.get("intent") if response.plan else None
        history_intent = plan_intent or response.intent
        
        history_item = QueryHistoryItem(
            id=audit_id,
            timestamp=datetime.utcnow().isoformat(),
            database=settings.db.database,
            question=question,
            intent=history_intent,
            plan=response.plan,
            sql=response.sql,
            params=response.params,
            row_count=response.results.get("row_count") if response.results else None,
            execution_time_ms=response.execution_time_ms,
            success=True,
            status="success",
        )
        add_to_history(history_item)
    except Exception:
        pass  # Don't fail pipeline if history save fails
    
    return response
