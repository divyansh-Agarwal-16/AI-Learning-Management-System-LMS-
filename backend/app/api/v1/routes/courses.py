"""Courses router module for the AI LMS backend.

This module exposes endpoints for browsing the course catalog, retrieving course
lessons, creating new courses/lessons, and enrolling in courses.
"""

import uuid
from typing import List, Optional
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.base import ApiResponse
from app.schemas.course import CourseCreate, CourseResponse, LessonCreate, LessonResponse
from app.services.course_service import CourseService

router = APIRouter(prefix="/courses", tags=["Courses"])
logger = structlog.get_logger()


@router.get("", response_model=ApiResponse[List[CourseResponse]])
async def list_courses(
    search: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves and filters the course catalog list.

    Args:
        search (Optional[str]): Text search filter.
        difficulty (Optional[str]): Difficulty level filter.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[List[CourseResponse]]: Standardized course catalog list.
    """
    logger.info("list_courses_requested", search=search, difficulty=difficulty)
    courses = await CourseService.get_courses(db, search, difficulty)
    return ApiResponse(
        success=True,
        data=[CourseResponse.model_validate(c) for c in courses],
        message="Course catalog fetched successfully"
    )


@router.get("/{course_id}", response_model=ApiResponse[CourseResponse])
async def get_course(course_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Retrieves detailed information and lessons for a specific course.

    Args:
        course_id (uuid.UUID): UUID identifier key.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[CourseResponse]: Standardized course details response.
    """
    logger.info("course_details_requested", course_id=course_id)
    course = await CourseService.get_course_by_id(db, course_id)
    if not course:
        logger.warning("course_details_not_found", course_id=course_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{course_id}' not found"
        )
    return ApiResponse(
        success=True,
        data=CourseResponse.model_validate(course),
        message="Course details fetched successfully"
    )


@router.post("", response_model=ApiResponse[CourseResponse], status_code=status.HTTP_201_CREATED)
async def create_course(
    request: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Registers a new Course catalog.

    Args:
        request (CourseCreate): Course values.
        current_user (User): Graded User authorization.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[CourseResponse]: Standardized created course details response.
    """
    logger.info("course_create_attempt", user_id=current_user.id, course_id=request.id)
    
    # Restrict course creation to admins if role is verified
    if current_user.role != "admin":
         logger.warning("course_create_forbidden", user_id=current_user.id)
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="Only administrators can register new courses"
         )

    course = await CourseService.create_course(db, request)
    logger.info("course_create_success", course_id=course.id)
    return ApiResponse(
        success=True,
        data=CourseResponse.model_validate(course),
        message="Course registered successfully"
    )


@router.post("/{course_id}/lessons", response_model=ApiResponse[LessonResponse], status_code=status.HTTP_201_CREATED)
async def create_lesson(
    course_id: uuid.UUID,
    request: LessonCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Appends a new lesson to an existing Course catalog.

    Args:
        course_id (uuid.UUID): Course UUID identifier key.
        request (LessonCreate): Lesson values.
        current_user (User): Graded User authorization.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[LessonResponse]: Standardized created lesson details response.
    """
    logger.info("lesson_create_attempt", user_id=current_user.id, course_id=course_id, lesson_id=request.id)
    
    if current_user.role != "admin":
         raise HTTPException(
             status_code=status.HTTP_403_FORBIDDEN,
             detail="Only administrators can append lessons to courses"
         )

    lesson = await CourseService.create_lesson(db, course_id, request)
    if not lesson:
         raise HTTPException(
             status_code=status.HTTP_404_NOT_FOUND,
             detail=f"Target Course '{course_id}' not found"
         )
    logger.info("lesson_create_success", course_id=course_id, lesson_id=lesson.id)
    return ApiResponse(
        success=True,
        data=LessonResponse.model_validate(lesson),
        message="Lesson appended successfully"
    )


@router.post("/{course_id}/enroll", response_model=ApiResponse[bool])
async def enroll_course(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enrolls the active user in a specific Course.

    Args:
        course_id (uuid.UUID): Course UUID.
        current_user (User): Graded User session.
        db (AsyncSession): Active database session.

    Returns:
        ApiResponse[bool]: Standardized success response.
    """
    logger.info("course_enrollment_attempt", user_id=current_user.id, course_id=course_id)
    enrolled = await CourseService.enroll_user(db, current_user.id, course_id)
    if not enrolled:
        logger.warning("course_enrollment_failed", user_id=current_user.id, course_id=course_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with ID '{course_id}' not found"
        )
    logger.info("course_enrollment_success", user_id=current_user.id, course_id=course_id)
    return ApiResponse(
        success=True,
        data=True,
        message="Enrolled in course successfully"
    )
