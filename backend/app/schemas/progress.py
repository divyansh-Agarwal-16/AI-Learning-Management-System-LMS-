"""Progress schemas validating lesson and course milestone tracking.

This module houses validation rules for updating lesson progress states
and responding with overall course progress statistics.
"""

import uuid
from pydantic import BaseModel, Field


class LessonProgressRequest(BaseModel):
    """Schema validating lesson study activity submission.

    Attributes:
        completed (bool): True if student completed the lesson.
        time_spent (int): Active timing duration spent on lesson in seconds.
    """
    completed: bool = Field(..., description="Lesson completion state status")
    time_spent: int = Field(..., ge=0, description="Active timing duration spent on lesson in seconds")


class LessonProgressResponse(BaseModel):
    """Schema validating returned lesson tracking database states.

    Attributes:
        id (uuid.UUID): Primary key UUID.
        user_id (uuid.UUID): Graded student reference key.
        lesson_id (uuid.UUID): Target lesson code ID.
        completed (bool): Completion state.
        time_spent (int): Cumulative study timing.
    """
    id: uuid.UUID
    user_id: uuid.UUID
    lesson_id: uuid.UUID
    completed: bool
    time_spent: int

    model_config = {"from_attributes": True}


class CourseProgressResponse(BaseModel):
    """Schema validating overall course completion statistics.

    Attributes:
        id (uuid.UUID): Progress record UUID.
        user_id (uuid.UUID): Student reference UUID.
        course_id (uuid.UUID): Reference Course UUID.
        percentage (float): Cumulative calculated percentage (0.0 to 100.0).
        status (str): Study status (not_started, in_progress, completed).
    """
    id: uuid.UUID
    user_id: uuid.UUID
    course_id: uuid.UUID
    percentage: float
    status: str

    model_config = {"from_attributes": True}
