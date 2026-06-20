"""Quiz schemas for validating practice quiz components.

This module houses validation rules for reading quiz structures, submitting student answers,
and returning test score details.
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class QuestionResponse(BaseModel):
    """Schema representing quiz questions without correct answers.

    Attributes:
        id (int): Primary key ID.
        text (str): Prompt text.
        options (List[str]): Choices options text array.
    """
    id: int
    text: str
    options: List[str]

    model_config = {"from_attributes": True}


class QuizResponse(BaseModel):
    """Schema representing practice quizzes containing questions list.

    Attributes:
        id (int): Practice quiz ID.
        course_id (str): Course slug mapping.
        title (str): Quiz title.
        questions (List[QuestionResponse]): Embedded questions.
    """
    id: int
    course_id: str
    title: str
    questions: List[QuestionResponse] = []

    model_config = {"from_attributes": True}


class SubmitAnswerRequest(BaseModel):
    """Schema representing one selected answer.

    Attributes:
        question_id (int): Question ID context target.
        selected_option_idx (int): User selected choice index.
    """
    question_id: int = Field(..., description="ID reference of the target Question")
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
        id (int): Submission transaction ID.
        quiz_id (int): Practice quiz target ID.
        score (int): Total correct answers.
        total_questions (int): Graded questions count.
        submitted_at (datetime): Gradation timestamp.
    """
    id: int
    quiz_id: int
    score: int
    total_questions: int
    submitted_at: datetime

    model_config = {"from_attributes": True}
