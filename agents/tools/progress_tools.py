"""Progress Tools module for the Multi-Agent System.

Provides tools to check student study progress and recommend the next logical lesson.
"""

import uuid
import structlog
from pathlib import Path
import sys
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Configure sys.path to resolve root and backend directory imports
root_path = Path(__file__).parent.parent.parent
backend_path = root_path / "backend"
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))
if str(backend_path) not in sys.path:
    sys.path.append(str(backend_path))

from app.models.course import Lesson, Course
from app.models.progress import CourseProgress, LessonProgress

logger = structlog.get_logger()


async def get_user_progress(user_id: str, course_id: str, db: AsyncSession) -> Dict[str, Any]:
    """Retrieves user course metrics: percentage complete, completed counts, and current status.

    Args:
        user_id (str): User UUID string.
        course_id (str): Course UUID string.
        db (AsyncSession): Active database transaction session.

    Returns:
        Dict[str, Any]: Statistics containing percentage, total, and completed lesson counts.
    """
    logger.info("tool_get_user_progress_start", user_id=user_id, course_id=course_id)
    
    try:
        u_uuid = uuid.UUID(user_id)
        c_uuid = uuid.UUID(course_id)
        
        # 1. Fetch CourseProgress record
        cp_stmt = select(CourseProgress).where(
            CourseProgress.user_id == u_uuid,
            CourseProgress.course_id == c_uuid
        )
        cp_res = await db.execute(cp_stmt)
        cp = cp_res.scalar_one_or_none()
        
        # 2. Count lessons in this course
        lessons_stmt = select(Lesson).where(Lesson.course_id == c_uuid)
        lessons_res = await db.execute(lessons_stmt)
        lessons = lessons_res.scalars().all()
        total_lessons = len(lessons)
        
        # 3. Count completed lessons
        completed_stmt = select(LessonProgress).join(Lesson).where(
            Lesson.course_id == c_uuid,
            LessonProgress.user_id == u_uuid,
            LessonProgress.completed == True
        )
        completed_res = await db.execute(completed_stmt)
        completed_lessons = len(completed_res.scalars().all())
        
        # Calculate parameters
        percentage = 0.0
        if total_lessons > 0:
            percentage = round((completed_lessons / total_lessons) * 100.0, 2)
            
        status = "not_started"
        if cp:
            status = cp.status
            # Sync percentage if database is out of sync
            percentage = cp.percentage
        elif completed_lessons > 0:
            status = "in_progress"
            
        progress_data = {
            "percentage": percentage,
            "status": status,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons
        }
        
        logger.info("tool_get_user_progress_success", progress=progress_data)
        return progress_data
        
    except Exception as e:
        logger.error("tool_get_user_progress_failed", error=str(e))
        return {
            "percentage": 0.0,
            "status": "error",
            "total_lessons": 0,
            "completed_lessons": 0,
            "error": str(e)
        }


async def recommend_next_lesson(user_id: str, course_id: str, db: AsyncSession) -> Optional[Dict[str, Any]]:
    """Identifies the first uncompleted lesson in the sorted course lessons order.

    Args:
        user_id (str): Student User UUID.
        course_id (str): Target Course UUID.
        db (AsyncSession): Active database session context.

    Returns:
        Optional[Dict[str, Any]]: Details of the recommended lesson, or None if course is fully completed.
    """
    logger.info("tool_recommend_next_lesson_start", user_id=user_id, course_id=course_id)
    
    try:
        u_uuid = uuid.UUID(user_id)
        c_uuid = uuid.UUID(course_id)
        
        # 1. Query all course lessons sorted by order index
        lessons_stmt = select(Lesson).where(Lesson.course_id == c_uuid).order_by(Lesson.order)
        lessons_res = await db.execute(lessons_stmt)
        lessons = lessons_res.scalars().all()
        
        if not lessons:
            logger.warning("tool_recommend_next_lesson_no_lessons", course_id=course_id)
            return None
            
        # 2. Query completed lesson IDs for this user
        completed_stmt = select(LessonProgress.lesson_id).join(Lesson).where(
            Lesson.course_id == c_uuid,
            LessonProgress.user_id == u_uuid,
            LessonProgress.completed == True
        )
        completed_res = await db.execute(completed_stmt)
        completed_ids = set(completed_res.scalars().all())
        
        # 3. Find first uncompleted lesson
        for lesson in lessons:
            if lesson.id not in completed_ids:
                rec = {
                    "id": str(lesson.id),
                    "title": lesson.title,
                    "order": lesson.order,
                    "duration": lesson.duration,
                    "videoUrl": lesson.videoUrl,
                    "pdfUrl": lesson.pdfUrl
                }
                logger.info("tool_recommend_next_lesson_recommendation", lesson_title=lesson.title)
                return rec
                
        # All lessons are complete
        logger.info("tool_recommend_next_lesson_all_complete")
        return None
        
    except Exception as e:
        logger.error("tool_recommend_next_lesson_failed", error=str(e))
        return None
