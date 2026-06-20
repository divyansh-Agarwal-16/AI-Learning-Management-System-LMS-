"""Progress tracking service module for the AI LMS backend.

This module houses operations for recording lesson completion status,
saving study times, and recalculating course completion metrics.
"""

import uuid
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
        user_id: uuid.UUID,
        lesson_id: uuid.UUID,
        completed: bool,
        time_spent: int
    ) -> Optional[LessonProgress]:
        """Updates or registers a lesson progress entry and triggers course progress update.

        Args:
            db (AsyncSession): Active database session.
            user_id (uuid.UUID): Core user referencing key ID.
            lesson_id (uuid.UUID): Reference target Lesson ID.
            completed (bool): Completion state flag.
            time_spent (int): Timing spent on the lesson (in seconds).

        Returns:
            Optional[LessonProgress]: Updated LessonProgress object.
        """
        user_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        lesson_uuid = uuid.UUID(str(lesson_id)) if not isinstance(lesson_id, uuid.UUID) else lesson_id

        # Fetch lesson details to find course_id
        res_lesson = await db.execute(select(Lesson).where(Lesson.id == lesson_uuid))
        lesson = res_lesson.scalars().first()
        if not lesson:
            return None

        # Check if record exists
        stmt = select(LessonProgress).where(
            LessonProgress.user_id == user_uuid,
            LessonProgress.lesson_id == lesson_uuid
        )
        res = await db.execute(stmt)
        progress = res.scalars().first()

        if not progress:
            progress = LessonProgress(
                user_id=user_uuid,
                lesson_id=lesson_uuid,
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
        await ProgressService.recalculate_course_progress(db, user_uuid, lesson.course_id)

        return progress

    @staticmethod
    async def recalculate_course_progress(
        db: AsyncSession,
        user_id: uuid.UUID,
        course_id: uuid.UUID
    ) -> float:
        """Recalculates student course completion percentage based on lesson statuses.

        Args:
            db (AsyncSession): Active database session.
            user_id (uuid.UUID): Student User ID.
            course_id (uuid.UUID): Target Course ID.

        Returns:
            float: Cumulative course completion percentage (0.0 to 100.0).
        """
        user_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        course_uuid = uuid.UUID(str(course_id)) if not isinstance(course_id, uuid.UUID) else course_id

        # Get all lessons associated with the course
        res_lessons = await db.execute(select(Lesson.id).where(Lesson.course_id == course_uuid))
        lesson_ids = [row[0] for row in res_lessons.all()]
        
        if not lesson_ids:
            return 0.0

        # Query completed lesson count
        stmt = (
            select(func.count(LessonProgress.id))
            .where(
                LessonProgress.user_id == user_uuid,
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
            .where(CourseProgress.user_id == user_uuid, CourseProgress.course_id == course_uuid)
        )
        course_progress = res_progress.scalars().first()

        if not course_progress:
            course_progress = CourseProgress(
                user_id=user_uuid,
                course_id=course_uuid,
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
        user_id: uuid.UUID,
        course_id: uuid.UUID
    ) -> Optional[CourseProgress]:
        """Fetches the CourseProgress configuration status for a student.

        Args:
            db (AsyncSession): Active database session.
            user_id (uuid.UUID): Student User ID.
            course_id (uuid.UUID): Reference Course UUID.

        Returns:
            Optional[CourseProgress]: Course progress DB object, if exists.
        """
        user_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        course_uuid = uuid.UUID(str(course_id)) if not isinstance(course_id, uuid.UUID) else course_id

        res = await db.execute(
            select(CourseProgress)
            .where(CourseProgress.user_id == user_uuid, CourseProgress.course_id == course_uuid)
        )
        return res.scalars().first()
