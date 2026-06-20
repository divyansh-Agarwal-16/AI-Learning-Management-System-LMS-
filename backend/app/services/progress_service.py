"""Progress tracking service module for the AI LMS backend.

This module houses operations for recording lesson completion status,
saving study times, and recalculating course completion metrics.
"""

from typing import Optional
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.course import Lesson
from app.models.progress import LessonProgress, CourseProgress


class ProgressService:
    """Lesson progress tracking and course completion calculations."""

    @staticmethod
    async def track_lesson_progress(
        db: AsyncSession,
        user_id: int,
        lesson_id: str,
        completed: bool,
        time_spent: int
    ) -> Optional[LessonProgress]:
        """Updates or registers a lesson progress entry and triggers course progress update.

        Args:
            db (AsyncSession): Active database session.
            user_id (int): Core user referencing key ID.
            lesson_id (str): Reference target Lesson ID.
            completed (bool): Completion state flag.
            time_spent (int): Timing spent on the lesson (in seconds).

        Returns:
            Optional[LessonProgress]: Updated LessonProgress object.
        """
        # Fetch lesson details to find course_id
        res_lesson = await db.execute(select(Lesson).where(Lesson.id == lesson_id))
        lesson = res_lesson.scalars().first()
        if not lesson:
            return None

        # Check if record exists
        stmt = select(LessonProgress).where(
            LessonProgress.user_id == user_id,
            LessonProgress.lesson_id == lesson_id
        )
        res = await db.execute(stmt)
        progress = res.scalars().first()

        if not progress:
            progress = LessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                completed=completed,
                time_spent=time_spent
            )
            db.add(progress)
        else:
            progress.completed = completed
            progress.time_spent += time_spent

        await db.commit()
        await db.refresh(progress)

        # Recalculate course percentage
        await ProgressService.recalculate_course_progress(db, user_id, lesson.course_id)

        return progress

    @staticmethod
    async def recalculate_course_progress(
        db: AsyncSession,
        user_id: int,
        course_id: str
    ) -> float:
        """Recalculates student course completion percentage based on lesson statuses.

        Args:
            db (AsyncSession): Active database session.
            user_id (int): Student User ID.
            course_id (str): Target Course ID.

        Returns:
            float: Cumulative course completion percentage (0.0 to 100.0).
        """
        # Get all lessons associated with the course
        res_lessons = await db.execute(select(Lesson.id).where(Lesson.course_id == course_id))
        lesson_ids = [row[0] for row in res_lessons.all()]
        
        if not lesson_ids:
            return 0.0

        # Query completed lesson count
        stmt = (
            select(func.count(LessonProgress.id))
            .where(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id.in_(lesson_ids),
                LessonProgress.completed == True
            )
        )
        res_completed = await db.execute(stmt)
        completed_count = res_completed.scalar() or 0

        # Calculate percentage
        percentage = round((completed_count / len(lesson_ids)) * 100.0, 2)

        # Get or create CourseProgress record
        res_progress = await db.execute(
            select(CourseProgress)
            .where(CourseProgress.user_id == user_id, CourseProgress.course_id == course_id)
        )
        course_progress = res_progress.scalars().first()

        if not course_progress:
            course_progress = CourseProgress(
                user_id=user_id,
                course_id=course_id,
                percentage=percentage,
                status="in_progress"
            )
            db.add(course_progress)
        else:
            course_progress.percentage = percentage
            if percentage >= 100.0:
                course_progress.status = "completed"
            elif percentage > 0.0:
                course_progress.status = "in_progress"
            else:
                course_progress.status = "not_started"

        await db.commit()
        return percentage

    @staticmethod
    async def get_course_progress(
        db: AsyncSession,
        user_id: int,
        course_id: str
    ) -> Optional[CourseProgress]:
        """Fetches the CourseProgress configuration status for a student.

        Args:
            db (AsyncSession): Active database session.
            user_id (int): Student User ID.
            course_id (str): Reference Course slug ID.

        Returns:
            Optional[CourseProgress]: Course progress DB object, if exists.
        """
        res = await db.execute(
            select(CourseProgress)
            .where(CourseProgress.user_id == user_id, CourseProgress.course_id == course_id)
        )
        return res.scalars().first()
