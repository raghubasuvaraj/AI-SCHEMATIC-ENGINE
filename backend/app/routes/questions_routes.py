"""
API routes for sample questions management.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
from typing import Optional
from backend.app.services.questions_service import (
    get_sample_questions,
    get_all_questions,
    generate_ai_questions,
    generate_data_aware_questions,
    export_questions_to_text,
)

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("", summary="Get all sample questions")
def list_questions(include_ai: bool = False, include_data_analysis: bool = True, ai_count: int = 10):
    """
    Get sample questions for the AP query engine.
    
    - include_ai: If true, also generate AI-based questions
    - include_data_analysis: If true, analyze database for data-aware questions (default: true)
    - ai_count: Number of AI questions to generate (default: 10)
    """
    try:
        return get_all_questions(include_ai=include_ai, include_data_analysis=include_data_analysis, ai_count=ai_count)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze-data", summary="Generate questions based on actual database data")
def analyze_data_questions():
    """Analyze database tables and generate questions based on real data values."""
    try:
        questions = generate_data_aware_questions()
        return {"total": len(questions), "questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predefined", summary="Get only predefined sample questions")
def list_predefined_questions():
    """Get the list of predefined sample questions."""
    questions = get_sample_questions()
    return {"total": len(questions), "questions": questions}


@router.post("/generate-ai", summary="Generate AI-powered sample questions")
def generate_questions(count: int = 10):
    """Generate additional questions using AI based on the database schema."""
    try:
        questions = generate_ai_questions(count)
        return {"total": len(questions), "questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export", summary="Export questions as text", response_class=PlainTextResponse)
def export_questions(include_ai: bool = False):
    """Export all questions as formatted text."""
    try:
        data = get_all_questions(include_ai=include_ai)
        text = export_questions_to_text(data["questions"])
        return PlainTextResponse(content=text, media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

