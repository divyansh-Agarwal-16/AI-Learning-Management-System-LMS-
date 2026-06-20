"""AI router module for the AI LMS backend.

This module exposes endpoints for student AI Tutor streaming/chat queries,
generating daily study schedules, and suggesting dynamic learning paths.
All routes are rate-limited to 10 requests per minute per user.
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
from app.schemas.ai import ChatRequest, ChatResponse, StudyPlanResponse, RecommendationsResponse
from app.services.ai_service import AIService

# Setup Slowapi rate limiter key resolver using JWT sub (User ID) or IP fallback
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
logger = structlog.get_logger()


@router.post("/chat", response_model=ApiResponse[ChatResponse])
@limiter.limit("10/minute")
async def chat(
    request: Request,
    body: ChatRequest,
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Answers a course-related query, rate-limited by user context.

    Args:
        request (Request): Mandatory request parameter for slowapi.
        body (ChatRequest): Prompts query input details.
        course_id (uuid.UUID): Reference Course UUID.
        current_user (User): Graded User session.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[ChatResponse]: Standardized chat response.
    """
    logger.info("ai_chat_requested", user_id=current_user.id, course_id=course_id)
    reply = await AIService.generate_chat_response(db, current_user.id, course_id, body.message)
    return ApiResponse(
        success=True,
        data=ChatResponse(reply=reply),
        message="AI Tutor response generated successfully"
    )


@router.get("/study-plan", response_model=ApiResponse[StudyPlanResponse])
@limiter.limit("10/minute")
async def get_study_plan(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generates personalized study task milestones, rate-limited.

    Args:
        request (Request): Mandatory request context.
        current_user (User): Graded User session.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[StudyPlanResponse]: Standardized study milestones.
    """
    logger.info("ai_study_plan_requested", user_id=current_user.id)
    plan = await AIService.generate_study_plan(db, current_user.id)
    return ApiResponse(
        success=True,
        data=plan,
        message="AI study plan generated successfully"
    )


@router.get("/recommendations", response_model=ApiResponse[RecommendationsResponse])
@limiter.limit("10/minute")
async def get_recommendations(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Recommends courses matching the user profile skills, rate-limited.

    Args:
        request (Request): Mandatory request context.
        current_user (User): Graded User session.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[RecommendationsResponse]: Standardized course recommendations list.
    """
    logger.info("ai_recommendations_requested", user_id=current_user.id)
    recs = await AIService.generate_course_recommendations(db, current_user.id)
    return ApiResponse(
        success=True,
        data=recs,
        message="AI recommendations generated successfully"
    )
