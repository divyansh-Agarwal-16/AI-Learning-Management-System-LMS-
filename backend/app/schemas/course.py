"""Course schemas validating course resources and lesson models.

This module houses validation rules for reading course indexes, adding course content,
and cataloging lesson assets.
"""

import uuid
from typing import List, Optional
from pydantic import BaseModel, Field


class LessonCreate(BaseModel):
    """Schema validating lesson input elements during creation.

    Attributes:
        id (Optional[uuid.UUID]): UUID identifier for lesson.
        title (str): Lesson name.
        duration (str): Approximate run timing.
        videoUrl (Optional[str]): Video stream path.
        pdfUrl (Optional[str]): Document reference link.
        order (int): Ordering index.
    """
    id: Optional[uuid.UUID] = Field(None, description="UUID identifier for lesson")
    title: str = Field(..., max_length=255)
    duration: str = Field(..., max_length=50)
    videoUrl: Optional[str] = Field(None, max_length=512)
    pdfUrl: Optional[str] = Field(None, max_length=512)
    order: int = Field(0, ge=0)


class LessonResponse(BaseModel):
    """Schema validating returned lesson payload database states.

    Attributes:
        id (uuid.UUID): Lesson UUID ID.
        course_id (uuid.UUID): Reference course key.
        title (str): Lesson name.
        duration (str): Run timing.
        videoUrl (Optional[str]): Video link.
        pdfUrl (Optional[str]): Document link.
        order (int): Index number.
        completed (bool): User-specific completion status indicator.
    """
    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    duration: str
    videoUrl: Optional[str] = None
    pdfUrl: Optional[str] = None
    order: int
    completed: bool = False

    model_config = {"from_attributes": True}


class CourseCreate(BaseModel):
    """Schema validating courses during database input creation.

    Attributes:
        id (Optional[uuid.UUID]): Course UUID.
        title (str): Course name.
        description (Optional[str]): Description.
        difficulty (str): Syllabus difficulty.
        duration (str): Overall duration estimate.
    """
    id: Optional[uuid.UUID] = Field(None, description="UUID identifier for course")
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    difficulty: str = Field(..., max_length=50)
    duration: str = Field(..., max_length=50)


class CourseResponse(BaseModel):
    """Schema validating returned course catalog payloads.

    Attributes:
        id (uuid.UUID): Course identifier key.
        title (str): Course name.
        description (Optional[str]): Detailed description.
        difficulty (str): Level rating.
        duration (str): Timing summary.
        lessons (List[LessonResponse]): Embedded sorted lesson list.
    """
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    difficulty: str
    duration: str
    lessons: List[LessonResponse] = []

    model_config = {"from_attributes": True}
