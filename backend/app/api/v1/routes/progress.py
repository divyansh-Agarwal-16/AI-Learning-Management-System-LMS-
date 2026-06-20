"""Progress router module for the AI LMS backend.

This module exposes endpoints for tracking individual lesson milestones and
retrieving cumulative course completion percentages.
"""

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.progress import LessonProgressRequest, LessonProgressResponse, CourseProgressResponse
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/progress", tags=["Progress"])
logger = structlog.get_logger()


@router.post("/lessons/{lesson_id}", response_model=ApiResponse[LessonProgressResponse])
async def track_lesson(
    lesson_id: str,
    request: LessonProgressRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Records completion status and time spent for a lesson.

    Args:
        lesson_id (str): Target lesson code ID.
        request (LessonProgressRequest): Study metrics.
        current_user (User): Graded User session.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[LessonProgressResponse]: Standardized lesson progress details.
    """
    logger.info(
        "track_lesson_progress_attempt",
        user_id=current_user.id,
        lesson_id=lesson_id,
        completed=request.completed,
        time_spent=request.time_spent
    )
    
    progress = await ProgressService.track_lesson_progress(
        db,
        current_user.id,
        lesson_id,
        request.completed,
        request.time_spent
    )
    if not progress:
        logger.warning("track_lesson_progress_failed_lesson_not_found", lesson_id=lesson_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson with ID '{lesson_id}' not found"
        )

    logger.info("track_lesson_progress_success", user_id=current_user.id, lesson_id=lesson_id)
    return ApiResponse(
        success=True,
        data=LessonProgressResponse.model_validate(progress),
        message="Lesson progress saved successfully"
    )


@router.get("/courses/{course_id}", response_model=ApiResponse[CourseProgressResponse])
async def get_course_progress(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves overall study status and percentage for a course.

    Args:
        course_id (str): Reference Course slug ID.
        current_user (User): Graded User session.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[CourseProgressResponse]: Standardized course progress.
    """
    logger.info("course_progress_fetch_requested", user_id=current_user.id, course_id=course_id)
    progress = await ProgressService.get_course_progress(db, current_user.id, course_id)
    
    if not progress:
        # If user is enrolled but has not started, percentage is 0.0
        return ApiResponse(
            success=True,
            data=CourseProgressResponse(
                id=0,
                user_id=current_user.id,
                course_id=course_id,
                percentage=0.0,
                status="not_started"
            ),
            message="No active progress records found, returned default zeroed state"
        )

    return ApiResponse(
        success=True,
        data=CourseProgressResponse.model_validate(progress),
        message="Course progress fetched successfully"
    )
