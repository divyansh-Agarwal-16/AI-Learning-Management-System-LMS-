"""Quizzes router module for the AI LMS backend.

This module exposes endpoints for fetching a course's practice quiz,
submitting completed quizzes for grading, and retrieving past submission results.
"""

from typing import List
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.quiz import QuizResponse, SubmitQuizRequest, SubmissionResponse
from app.services.course_service import CourseService

router = APIRouter(tags=["Quizzes"])
logger = structlog.get_logger()


@router.get("/courses/{course_id}/quiz", response_model=ApiResponse[QuizResponse])
async def get_quiz(course_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves the practice quiz questions linked to a course.

    Args:
        course_id (str): Reference Course slug ID.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[QuizResponse]: Standardized quiz questions structure.
    """
    logger.info("quiz_fetch_requested", course_id=course_id)
    quiz = await CourseService.get_quiz_by_course(db, course_id)
    if not quiz:
        logger.warning("quiz_fetch_failed_not_found", course_id=course_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Practice quiz not found for course '{course_id}'"
        )
    return ApiResponse(
        success=True,
        data=QuizResponse.model_validate(quiz),
        message="Quiz questions loaded successfully"
    )


@router.post("/quizzes/{quiz_id}/submit", response_model=ApiResponse[SubmissionResponse])
async def submit_quiz(
    quiz_id: int,
    request: SubmitQuizRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Grades, saves, and returns results for a quiz submission.

    Args:
        quiz_id (int): Target quiz ID.
        request (SubmitQuizRequest): Student submitted answers.
        current_user (User): Graded user session.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[SubmissionResponse]: Standardized submission score data.
    """
    logger.info("quiz_submission_attempt", user_id=current_user.id, quiz_id=quiz_id)
    submission = await CourseService.submit_quiz(db, current_user.id, quiz_id, request)
    if not submission:
        logger.warning("quiz_submission_failed_quiz_not_found", quiz_id=quiz_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz with ID '{quiz_id}' not found"
        )
    logger.info("quiz_submission_success", user_id=current_user.id, quiz_id=quiz_id, score=submission.score)
    return ApiResponse(
        success=True,
        data=SubmissionResponse.model_validate(submission),
        message="Quiz graded and submitted successfully"
    )


@router.get("/quizzes/{quiz_id}/submissions", response_model=ApiResponse[List[SubmissionResponse]])
async def get_quiz_results(
    quiz_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieves past grading transaction files for a quiz.

    Args:
        quiz_id (int): Graded quiz ID.
        current_user (User): Graded user session.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[List[SubmissionResponse]]: Graded submissions history.
    """
    logger.info("submissions_history_requested", user_id=current_user.id, quiz_id=quiz_id)
    submissions = await CourseService.get_submissions(db, current_user.id, quiz_id)
    return ApiResponse(
        success=True,
        data=[SubmissionResponse.model_validate(s) for s in submissions],
        message="Submission history loaded successfully"
    )
