"""Quiz schemas for validating practice quiz components.

This module houses validation rules for reading quiz structures, submitting student answers,
and returning test score details.
"""

import uuid
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class QuestionResponse(BaseModel):
    """Schema representing quiz questions without correct answers.

    Attributes:
        id (uuid.UUID): Primary key ID.
        text (str): Prompt text.
        options (List[str]): Choices options text array.
    """
    id: uuid.UUID
    text: str
    options: List[str]

    model_config = {"from_attributes": True}


class QuizResponse(BaseModel):
    """Schema representing practice quizzes containing questions list.

    Attributes:
        id (uuid.UUID): Practice quiz ID.
        course_id (uuid.UUID): Course UUID mapping.
        title (str): Quiz title.
        questions (List[QuestionResponse]): Embedded questions.
    """
    id: uuid.UUID
    course_id: uuid.UUID
    title: str
    questions: List[QuestionResponse] = []

    model_config = {"from_attributes": True}


class SubmitAnswerRequest(BaseModel):
    """Schema representing one selected answer.

    Attributes:
        question_id (uuid.UUID): Question ID context target.
        selected_option_idx (int): User selected choice index.
    """
    question_id: uuid.UUID = Field(..., description="ID reference of the target Question")
    selected_option_idx: int = Field(..., ge=0, description="Selected zero-indexed choice index")


class SubmitQuizRequest(BaseModel):
    """Schema representing quiz submissions.

    Attributes:
        answers (List[SubmitAnswerRequest]): List of individual selected answers.
    """
    answers: List[SubmitAnswerRequest] = Field(..., description="List of submitted answer choices")


class SubmissionResponse(BaseModel):
    """Schema representing graded submission details.

    Attributes:
        id (uuid.UUID): Submission transaction ID.
        quiz_id (uuid.UUID): Practice quiz target ID.
        score (int): Total correct answers.
        total_questions (int): Graded questions count.
        submitted_at (datetime): Gradation timestamp.
    """
    id: uuid.UUID
    quiz_id: uuid.UUID
    score: int
    total_questions: int
    submitted_at: datetime

    model_config = {"from_attributes": True}
