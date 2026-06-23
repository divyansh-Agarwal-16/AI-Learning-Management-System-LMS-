"""Course service module for the AI LMS backend.

This module houses operations for listing courses, fetching course details,
creating courses/lessons, handling student enrollments, and grading quizzes.
"""

import uuid
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.course import Course, Lesson, Enrollment
from app.models.progress import CourseProgress
from app.models.quiz import Quiz, Question, Submission, Answer
from app.schemas.course import CourseCreate, LessonCreate
from app.schemas.quiz import SubmitQuizRequest


def to_uuid(val) -> Optional[uuid.UUID]:
    """Helper utility converting strings or existing UUID objects to uuid.UUID.

    Args:
        val (Any): Input ID payload.

    Returns:
        Optional[uuid.UUID]: Parsed UUID object, or None if invalid.
    """
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except ValueError:
        return None


class CourseService:
    """Course catalog query, creation, and quiz business operations."""

    @staticmethod
    async def get_courses(
        db: AsyncSession,
        search: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Course]:
        """Queries and filters active courses from the database.

        Args:
            db (AsyncSession): Active database session.
            search (Optional[str]): Filtering search query for title/description.
            difficulty (Optional[str]): Filtering level category.

        Returns:
            List[Course]: Filtered database Course list.
        """
        stmt = select(Course).options(selectinload(Course.lessons)).where(Course.is_deleted == False)
        
        filters = []
        if search:
            filters.append(
                or_(
                    Course.title.ilike(f"%{search}%"),
                    Course.description.ilike(f"%{search}%")
                )
            )
        if difficulty:
            filters.append(Course.difficulty.ilike(difficulty))

        if filters:
            stmt = stmt.where(*filters)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_course_by_id(db: AsyncSession, course_id: uuid.UUID) -> Optional[Course]:
        """Fetches a detailed course with lessons preloaded.

        Args:
            db (AsyncSession): Active database session.
            course_id (uuid.UUID): Reference Course UUID.

        Returns:
            Optional[Course]: Detailed database Course, or None.
        """
        course_uuid = to_uuid(course_id)
        if not course_uuid:
            return None

        result = await db.execute(
            select(Course)
            .where(Course.id == course_uuid, Course.is_deleted == False)
            .options(selectinload(Course.lessons))
        )
        return result.scalars().first()

    @staticmethod
    async def create_course(db: AsyncSession, request: CourseCreate) -> Course:
        """Registers a new Course in the catalog.

        Args:
            db (AsyncSession): Active database session.
            request (CourseCreate): Catalog values for course.

        Returns:
            Course: The registered Course database object.
        """
        course_uuid = to_uuid(request.id) if request.id else uuid.uuid4()
        if not course_uuid:
            course_uuid = uuid.uuid4()

        existing = await CourseService.get_course_by_id(db, course_uuid)
        if existing:
            return existing

        course = Course(
            id=course_uuid,
            title=request.title,
            description=request.description,
            difficulty=request.difficulty,
            duration=request.duration
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)
        return course

    @staticmethod
    async def create_lesson(db: AsyncSession, course_id: uuid.UUID, request: LessonCreate) -> Optional[Lesson]:
        """Appends a new lesson to an existing Course catalog.

        Args:
            db (AsyncSession): Active database session.
            course_id (uuid.UUID): Targeted Course UUID.
            request (LessonCreate): Values for lesson creation.

        Returns:
            Optional[Lesson]: Created database Lesson, or None if course doesn't exist.
        """
        course_uuid = to_uuid(course_id)
        if not course_uuid:
            return None

        course = await CourseService.get_course_by_id(db, course_uuid)
        if not course:
            return None

        lesson_uuid = to_uuid(request.id) if request.id else uuid.uuid4()
        if not lesson_uuid:
            lesson_uuid = uuid.uuid4()

        res = await db.execute(select(Lesson).where(Lesson.id == lesson_uuid))
        existing = res.scalars().first()
        if existing:
            return existing

        lesson = Lesson(
            id=lesson_uuid,
            course_id=course_uuid,
            title=request.title,
            duration=request.duration,
            videoUrl=request.videoUrl,
            pdfUrl=request.pdfUrl,
            order=request.order
        )
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)
        return lesson

    @staticmethod
    async def enroll_user(db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID) -> bool:
        """Enrolls a student inside a Course catalog.

        Args:
            db (AsyncSession): Active database session.
            user_id (uuid.UUID): Core user referencing key UUID.
            course_id (uuid.UUID): Target Course UUID.

        Returns:
            bool: True if enrolled successfully, False otherwise.
        """
        user_uuid = to_uuid(user_id)
        course_uuid = to_uuid(course_id)
        if not user_uuid or not course_uuid:
            return False

        course = await CourseService.get_course_by_id(db, course_uuid)
        if not course:
            return False

        is_enrolled = await CourseService.is_user_enrolled(db, user_uuid, course_uuid)
        if is_enrolled:
            return True

        enrollment = Enrollment(user_id=user_uuid, course_id=course_uuid)
        progress = CourseProgress(user_id=user_uuid, course_id=course_uuid, percentage=0.0, status="in_progress")
        
        db.add(enrollment)
        db.add(progress)
        await db.commit()
        return True

    @staticmethod
    async def is_user_enrolled(db: AsyncSession, user_id: uuid.UUID, course_id: uuid.UUID) -> bool:
        """Verifies if a user is enrolled in a course.

        Args:
            db (AsyncSession): Active database session.
            user_id (uuid.UUID): Student User UUID.
            course_id (uuid.UUID): Target Course UUID.

        Returns:
            bool: True if enrolled, False otherwise.
        """
        user_uuid = to_uuid(user_id)
        course_uuid = to_uuid(course_id)
        if not user_uuid or not course_uuid:
            return False

        result = await db.execute(
            select(Enrollment)
            .where(Enrollment.user_id == user_uuid, Enrollment.course_id == course_uuid)
        )
        return result.scalars().first() is not None

    @staticmethod
    async def get_quiz_by_course(db: AsyncSession, course_id: uuid.UUID) -> Optional[Quiz]:
        """Fetches the practice quiz associated with a course.

        Args:
            db (AsyncSession): Active database session.
            course_id (uuid.UUID): Reference Course UUID.

        Returns:
            Optional[Quiz]: The associated Quiz database object, if exists.
        """
        course_uuid = to_uuid(course_id)
        if not course_uuid:
            return None

        result = await db.execute(
            select(Quiz)
            .where(Quiz.course_id == course_uuid)
            .options(selectinload(Quiz.questions))
        )
        return result.scalars().first()

    @staticmethod
    async def get_quiz_by_id(db: AsyncSession, quiz_id: uuid.UUID) -> Optional[Quiz]:
        """Fetches a quiz by its primary key ID with questions loaded.

        Args:
            db (AsyncSession): Active database session.
            quiz_id (uuid.UUID): Quiz UUID.

        Returns:
            Optional[Quiz]: The Quiz database object, if exists.
        """
        quiz_uuid = to_uuid(quiz_id)
        if not quiz_uuid:
            return None

        result = await db.execute(
            select(Quiz)
            .where(Quiz.id == quiz_uuid)
            .options(selectinload(Quiz.questions))
        )
        return result.scalars().first()

    @staticmethod
    async def create_quiz(db: AsyncSession, course_id: uuid.UUID, title: str) -> Quiz:
        """Registers a practice Quiz module.

        Args:
            db (AsyncSession): Active database session.
            course_id (uuid.UUID): Reference Course UUID.
            title (str): Quiz title.

        Returns:
            Quiz: The registered Quiz database object.
        """
        course_uuid = to_uuid(course_id)
        if not course_uuid:
            return None

        existing = await CourseService.get_quiz_by_course(db, course_uuid)
        if existing:
            return existing

        quiz = Quiz(course_id=course_uuid, title=title)
        db.add(quiz)
        await db.commit()
        await db.refresh(quiz)
        return quiz

    @staticmethod
    async def add_quiz_question(
        db: AsyncSession,
        quiz_id: uuid.UUID,
        text: str,
        options: List[str],
        correct_idx: int
    ) -> Question:
        """Adds a question to a practice quiz.

        Args:
            db (AsyncSession): Active database session.
            quiz_id (uuid.UUID): Target quiz UUID.
            text (str): Question prompt text.
            options (List[str]): Choices options.
            correct_idx (int): Correct index.

        Returns:
            Question: The created database Question object.
        """
        quiz_uuid = to_uuid(quiz_id)
        if not quiz_uuid:
            raise ValueError("Invalid quiz_id UUID specification")

        question = Question(
            quiz_id=quiz_uuid,
            text=text,
            options=options,
            correct_answer_idx=correct_idx
        )
        db.add(question)
        await db.commit()
        await db.refresh(question)
        return question

    @staticmethod
    async def submit_quiz(
        db: AsyncSession,
        user_id: uuid.UUID,
        quiz_id: uuid.UUID,
        request: SubmitQuizRequest
    ) -> Optional[Submission]:
        """Grades, submits, and logs a practice quiz.

        Args:
            db (AsyncSession): Active database session.
            user_id (uuid.UUID): Core user referencing key UUID.
            quiz_id (uuid.UUID): Target graded quiz UUID.
            request (SubmitQuizRequest): Student submitted answers.

        Returns:
            Optional[Submission]: Completed database Submission record, or None.
        """
        user_uuid = to_uuid(user_id)
        quiz_uuid = to_uuid(quiz_id)
        if not user_uuid or not quiz_uuid:
            return None

        # Fetch quiz and pre-load correct answers
        result = await db.execute(
            select(Quiz)
            .where(Quiz.id == quiz_uuid)
            .options(selectinload(Quiz.questions))
        )
        quiz = result.scalars().first()
        if not quiz:
            return None

        # Build map of questions
        question_map = {q.id: q for q in quiz.questions}
        total_questions = len(quiz.questions)
 
        # Grade student answers
        score = 0
        answers_to_create = []
        details_list = []
 
        # Create submission wrapper first
        submission = Submission(
            user_id=user_uuid,
            quiz_id=quiz_uuid,
            score=0,
            total_questions=total_questions
        )
        db.add(submission)
        await db.flush()  # Extract submission ID before child records are saved
 
        for ans in request.answers:
            ans_question_uuid = to_uuid(ans.question_id)
            if not ans_question_uuid:
                continue
 
            question_obj = question_map.get(ans_question_uuid)
            if not question_obj:
                continue
 
            correct_idx = question_obj.correct_answer_idx
            is_correct = (ans.selected_option_idx == correct_idx)
            if is_correct:
                score += 1
            
            # Record individual answer transaction
            db_answer = Answer(
                submission_id=submission.id,
                question_id=ans_question_uuid,
                selected_option_idx=ans.selected_option_idx
            )
            answers_to_create.append(db_answer)
 
            options = question_obj.options
            correct_text = options[correct_idx] if 0 <= correct_idx < len(options) else "Unknown"
            selected_text = options[ans.selected_option_idx] if 0 <= ans.selected_option_idx < len(options) else "Unknown"
 
            details_list.append({
                "question_id": ans_question_uuid,
                "selected_option_idx": ans.selected_option_idx,
                "correct_option_idx": correct_idx,
                "is_correct": is_correct,
                "question_text": question_obj.text,
                "correct_answer_text": correct_text,
                "selected_answer_text": selected_text
            })
 
        # Save updates
        submission.score = score
        db.add_all(answers_to_create)
        await db.commit()
        await db.refresh(submission)
        
        # Attach details for Pydantic mapping
        submission.details = details_list
        return submission

    @staticmethod
    async def get_submissions(db: AsyncSession, user_id: uuid.UUID, quiz_id: uuid.UUID) -> List[Submission]:
        """Fetches past quiz submissions for a user.

        Args:
            db (AsyncSession): Active database session.
            user_id (uuid.UUID): Student user UUID.
            quiz_id (uuid.UUID): Target quiz UUID.

        Returns:
            List[Submission]: List of submissions.
        """
        user_uuid = to_uuid(user_id)
        quiz_uuid = to_uuid(quiz_id)
        if not user_uuid or not quiz_uuid:
            return []

        result = await db.execute(
            select(Submission)
            .where(Submission.user_id == user_uuid, Submission.quiz_id == quiz_uuid)
            .order_by(Submission.submitted_at.desc())
        )
        return list(result.scalars().all())
