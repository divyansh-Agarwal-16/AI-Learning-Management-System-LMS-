"""Database verification script for the AI LMS backend.

Checks connection, asserts that all 14 tables exist in metadata,
counts rows in seeded tables, and audits relations between entities.
"""

import asyncio
import sys
import os

# Add parent path to import app package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import Base
from app.models.user import User
from app.models.course import Course, Lesson
from app.models.quiz import Quiz, Question


async def run_diagnostics():
    print(f"Connecting to database at: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    try:
        # Check basic connection
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1;"))
            print("Successfully connected to the PostgreSQL database.")

        # Check tables existence in metadata
        metadata_tables = Base.metadata.tables.keys()
        print(f"\nMetadata schema registers {len(metadata_tables)} tables:")
        for t in sorted(metadata_tables):
            print(f"  - {t}")
        
        assert len(metadata_tables) == 14, f"Expected 14 tables, found {len(metadata_tables)}"
        print("Metadata assertion passed (14 tables registered).")

        # Query seeded rows and count them
        async with SessionLocal() as db:
            print("\nAuditing seeded table rows...")
            
            # 1. Users
            res_users = await db.execute(select(User).options(selectinload(User.profile), selectinload(User.onboarding)))
            users = res_users.scalars().all()
            print(f"Users seeded: {len(users)}")
            assert len(users) >= 1, "Expected at least 1 user to be seeded"
            
            # Check user relations (profile and onboarding)
            test_user = users[0]
            print(f"  First user profile details: ID={test_user.id}, email={test_user.email}")
            assert test_user.profile is not None, "Profile relation not loaded!"
            assert test_user.onboarding is not None, "Onboarding relation not loaded!"
            print(f"  Relations check: Profile full_name='{test_user.profile.full_name}', Onboarding topic='{test_user.onboarding.topic}'")

            # 2. Courses & Lessons
            res_courses = await db.execute(select(Course).options(selectinload(Course.lessons)))
            courses = res_courses.scalars().all()
            print(f"Courses seeded: {len(courses)}")
            assert len(courses) == 3, f"Expected 3 courses, found {len(courses)}"
            
            total_lessons = 0
            for c in courses:
                print(f"  Course '{c.title}' (ID={c.id}) has {len(c.lessons)} lessons:")
                total_lessons += len(c.lessons)
                for l in c.lessons:
                    print(f"    - Lesson order {l.order}: {l.title} (ID={l.id})")
            assert total_lessons == 15, f"Expected 15 lessons in total, found {total_lessons}"

            # 3. Quizzes & Questions
            res_quizzes = await db.execute(select(Quiz).options(selectinload(Quiz.questions)))
            quizzes = res_quizzes.scalars().all()
            print(f"Quizzes seeded: {len(quizzes)}")
            assert len(quizzes) == 2, f"Expected 2 quizzes, found {len(quizzes)}"

            total_questions = 0
            for q in quizzes:
                print(f"  Quiz '{q.title}' (ID={q.id}) has {len(q.questions)} questions:")
                total_questions += len(q.questions)
                for ques in q.questions:
                    print(f"    - Question ID={ques.id}: {ques.text[:30]}...")
            assert total_questions == 10, f"Expected 10 questions in total, found {total_questions}"

            print("\nDatabase diagnostic audits complete! All schema tests passed.")

    except Exception as e:
        print(f"\nVerification audit FAILED: {str(e)}")
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_diagnostics())
