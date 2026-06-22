"""AI router module for the AI LMS backend.

This module exposes endpoints for student AI Tutor quizzes, study plan generation,
concept maps, and grading/feedback logic. All routes are rate-limited to 10 requests per minute.
"""

import uuid
import structlog
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.ai import (
    GenerateQuizRequest,
    GenerateQuizResponse,
    NewStudyPlanRequest,
    NewStudyPlanResponse,
    ConceptMapRequest,
    ConceptMapResponse,
    AnswerFeedbackRequest,
    AnswerFeedbackResponse
)
from app.services.ai_service import AIService

logger = structlog.get_logger()


# Rate limiter key resolver using JWT sub (User ID) or IP fallback
def resolve_user_or_ip_key(request: Request) -> str:
    """Resolves rate limit keys by decoding user ID from JWT or IP address.

    Args:
        request (Request): The incoming request context.

    Returns:
        str: Unique key identifier.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            from jose import jwt
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                return f"user_{user_id}"
        except Exception:
            pass
    return get_remote_address(request)


# Limiter instance
limiter = Limiter(key_func=resolve_user_or_ip_key)
router = APIRouter(prefix="/ai", tags=["AI Integration"])


@router.post("/generate-quiz", response_model=ApiResponse[GenerateQuizResponse])
@limiter.limit("10/minute")
async def generate_quiz(
    request: Request,
    body: GenerateQuizRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates a structured practice quiz for a lesson.

    Args:
        request (Request): Request context.
        body (GenerateQuizRequest): Request options.
        current_user (User): Graded User session.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[GenerateQuizResponse]: Generated quiz metadata and questions.
    """
    logger.info("ai_generate_quiz_requested", user_id=current_user.id, lesson_id=body.lesson_id)
    quiz_data = await AIService.generate_quiz_genai(
        db=db,
        lesson_id=body.lesson_id,
        difficulty=body.difficulty,
        num_questions=body.num_questions,
        user_id=current_user.id
    )
    return ApiResponse(
        success=True,
        data=quiz_data,
        message="Quiz generated successfully"
    )


@router.post("/study-plan", response_model=ApiResponse[NewStudyPlanResponse])
@limiter.limit("10/minute")
async def get_study_plan(
    request: Request,
    body: NewStudyPlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates a personalized 7-day study plan based on user scoring progress.

    Args:
        request (Request): Request context.
        body (NewStudyPlanRequest): Student user request parameter context.
        current_user (User): Graded User session.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[NewStudyPlanResponse]: Personalized weekly plan.
    """
    logger.info("ai_study_plan_requested", user_id=current_user.id, target_user_id=body.user_id)
    plan = await AIService.generate_study_plan_genai(db=db, user_id=body.user_id)
    return ApiResponse(
        success=True,
        data=plan,
        message="AI study plan generated successfully"
    )


@router.post("/concept-map", response_model=ApiResponse[ConceptMapResponse])
@limiter.limit("10/minute")
async def get_concept_map(
    request: Request,
    body: ConceptMapRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates a concept map network mapping core nodes and edge relationships.

    Args:
        request (Request): Request context.
        body (ConceptMapRequest): Target map topic keyword.
        current_user (User): Graded User session.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[ConceptMapResponse]: Nodes and edges mapping.
    """
    logger.info("ai_concept_map_requested", user_id=current_user.id, topic=body.topic)
    concept_map = await AIService.generate_concept_map_genai(db=db, topic=body.topic, user_id=current_user.id)
    return ApiResponse(
        success=True,
        data=concept_map,
        message="Concept map generated successfully"
    )


@router.post("/feedback", response_model=ApiResponse[AnswerFeedbackResponse])
@limiter.limit("10/minute")
async def get_answer_feedback(
    request: Request,
    body: AnswerFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Evaluates student's answer submission, returning a score, constructive feedback, and improvements.

    Args:
        request (Request): Request context.
        body (AnswerFeedbackRequest): Student answer and correct answer keys context.
        current_user (User): Graded User session.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[AnswerFeedbackResponse]: Score, feedback, and 3 improvement suggestions.
    """
    logger.info("ai_answer_feedback_requested", user_id=current_user.id)
    feedback = await AIService.generate_answer_feedback_genai(
        db=db,
        question=body.question,
        student_answer=body.student_answer,
        correct_answer=body.correct_answer,
        user_id=current_user.id
    )
    return ApiResponse(
        success=True,
        data=feedback,
        message="Feedback generated successfully"
    )
