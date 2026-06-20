"""Course service module for the AI LMS backend.

This module houses operations for listing courses, fetching course details,
creating courses/lessons, handling student enrollments, and grading quizzes.
"""

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


class CourseService:
    """Course catalog query, creation, and quiz business operations."""

    @staticmethod
    async def get_courses(
        db: AsyncSession,
        search: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[Course]:
        """Queries and filters courses from the database.

        Args:
            db (AsyncSession): Active database session.
            search (Optional[str]): Filtering search query for title/description.
            difficulty (Optional[str]): Filtering level category.

        Returns:
            List[Course]: Filtered database Course list.
        """
        stmt = select(Course).options(selectinload(Course.lessons))
        
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
    async def get_course_by_id(db: AsyncSession, course_id: str) -> Optional[Course]:
        """Fetches a detailed course with lessons preloaded.

        Args:
            db (AsyncSession): Active database session.
            course_id (str): Reference Course slug ID.

        Returns:
            Optional[Course]: Detailed database Course, or None.
        """
        result = await db.execute(
            select(Course)
            .where(Course.id == course_id)
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
        existing = await CourseService.get_course_by_id(db, request.id)
        if existing:
            return existing

        course = Course(
            id=request.id,
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
    async def create_lesson(db: AsyncSession, course_id: str, request: LessonCreate) -> Optional[Lesson]:
        """Appends a new lesson to an existing Course catalog.

        Args:
            db (AsyncSession): Active database session.
            course_id (str): Targeted Course slug ID.
            request (LessonCreate): Values for lesson creation.

        Returns:
            Optional[Lesson]: Created database Lesson, or None if course doesn't exist.
        """
        course = await CourseService.get_course_by_id(db, course_id)
        if not course:
            return None

        res = await db.execute(select(Lesson).where(Lesson.id == request.id))
        existing = res.scalars().first()
        if existing:
            return existing

        lesson = Lesson(
            id=request.id,
            course_id=course_id,
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
    async def enroll_user(db: AsyncSession, user_id: int, course_id: str) -> bool:
        """Enrolls a student inside a Course catalog.

        Args:
            db (AsyncSession): Active database session.
            user_id (int): Core user referencing key ID.
            course_id (str): Target Course slug ID.

        Returns:
            bool: True if enrolled successfully, False otherwise.
        """
        course = await CourseService.get_course_by_id(db, course_id)
        if not course:
            return False

        is_enrolled = await CourseService.is_user_enrolled(db, user_id, course_id)
        if is_enrolled:
            return True

        enrollment = Enrollment(user_id=user_id, course_id=course_id)
        progress = CourseProgress(user_id=user_id, course_id=course_id, percentage=0.0, status="in_progress")
        
        db.add(enrollment)
        db.add(progress)
        await db.commit()
        return True

    @staticmethod
    async def is_user_enrolled(db: AsyncSession, user_id: int, course_id: str) -> bool:
        """Verifies if a user is enrolled in a course.

        Args:
            db (AsyncSession): Active database session.
            user_id (int): Student User ID.
            course_id (str): Target Course slug ID.

        Returns:
            bool: True if enrolled, False otherwise.
        """
        result = await db.execute(
            select(Enrollment)
            .where(Enrollment.user_id == user_id, Enrollment.course_id == course_id)
        )
        return result.scalars().first() is not None

    @staticmethod
    async def get_quiz_by_course(db: AsyncSession, course_id: str) -> Optional[Quiz]:
        """Fetches the practice quiz associated with a course.

        Args:
            db (AsyncSession): Active database session.
            course_id (str): Reference Course slug ID.

        Returns:
            Optional[Quiz]: The associated Quiz database object, if exists.
        """
        result = await db.execute(
            select(Quiz)
            .where(Quiz.course_id == course_id)
            .options(selectinload(Quiz.questions))
        )
        return result.scalars().first()

    @staticmethod
    async def create_quiz(db: AsyncSession, course_id: str, title: str) -> Quiz:
        """Registers a practice Quiz module.

        Args:
            db (AsyncSession): Active database session.
            course_id (str): Reference Course slug ID.
            title (str): Quiz title.

        Returns:
            Quiz: The registered Quiz database object.
        """
        existing = await CourseService.get_quiz_by_course(db, course_id)
        if existing:
            return existing

        quiz = Quiz(course_id=course_id, title=title)
        db.add(quiz)
        await db.commit()
        await db.refresh(quiz)
        return quiz

    @staticmethod
    async def add_quiz_question(
        db: AsyncSession,
        quiz_id: int,
        text: str,
        options: List[str],
        correct_idx: int
    ) -> Question:
        """Adds a question to a practice quiz.

        Args:
            db (AsyncSession): Active database session.
            quiz_id (int): Target quiz ID.
            text (str): Question prompt text.
            options (List[str]): Choices options.
            correct_idx (int): Correct index.

        Returns:
            Question: The created database Question object.
        """
        question = Question(
            quiz_id=quiz_id,
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
        user_id: int,
        quiz_id: int,
        request: SubmitQuizRequest
    ) -> Optional[Submission]:
        """Grades, submits, and logs a practice quiz.

        Args:
            db (AsyncSession): Active database session.
            user_id (int): Core user referencing key ID.
            quiz_id (int): Target graded quiz ID.
            request (SubmitQuizRequest): Student submitted answers.

        Returns:
            Optional[Submission]: Completed database Submission record, or None.
        """
        # Fetch quiz and pre-load correct answers
        result = await db.execute(
            select(Quiz)
            .where(Quiz.id == quiz_id)
            .options(selectinload(Quiz.questions))
        )
        quiz = result.scalars().first()
        if not quiz:
            return None

        # Build map of correct answers
        correct_map = {q.id: q.correct_answer_idx for q in quiz.questions}
        total_questions = len(quiz.questions)

        # Grade student answers
        score = 0
        answers_to_create = []

        # Create submission wrapper first
        submission = Submission(
            user_id=user_id,
            quiz_id=quiz_id,
            score=0,
            total_questions=total_questions
        )
        db.add(submission)
        await db.flush()  # Extract submission ID before child records are saved

        for ans in request.answers:
            correct_idx = correct_map.get(ans.question_id)
            if correct_idx is not None and ans.selected_option_idx == correct_idx:
                score += 1
            
            # Record individual answer transaction
            db_answer = Answer(
                submission_id=submission.id,
                question_id=ans.question_id,
                selected_option_idx=ans.selected_option_idx
            )
            answers_to_create.append(db_answer)

        # Save updates
        submission.score = score
        db.add_all(answers_to_create)
        await db.commit()
        await db.refresh(submission)
        return submission

    @staticmethod
    async def get_submissions(db: AsyncSession, user_id: int, quiz_id: int) -> List[Submission]:
        """Fetches past quiz submissions for a user.

        Args:
            db (AsyncSession): Active database session.
            user_id (int): Student user ID.
            quiz_id (int): Target quiz ID.

        Returns:
            List[Submission]: List of submissions.
        """
        result = await db.execute(
            select(Submission)
            .where(Submission.user_id == user_id, Submission.quiz_id == quiz_id)
            .order_by(Submission.submitted_at.desc())
        )
        return list(result.scalars().all())
