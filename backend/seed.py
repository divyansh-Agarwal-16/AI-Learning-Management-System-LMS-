"""Database seeding script for the AI LMS backend.

Truncates all existing tables and seeds standard mock data:
- 1 test user (test@test.com / password123) with profile and onboarding
- 3 courses (Python, LlamaIndex, LangGraph) with 5 lessons each
- 2 quizzes (Python, LlamaIndex) with 5 questions each
"""

import asyncio
import sys
import os
import uuid

# Add parent path to import app package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserProfile, OnboardingData
from app.models.course import Course, Lesson
from app.models.quiz import Quiz, Question


# Course UUID constants
PYTHON_COURSE_UUID = uuid.UUID("e4b3c004-94c6-47b2-84c1-cd54cfc0bf7a")
LLAMA_COURSE_UUID = uuid.UUID("9d3f82a1-fa4c-4a30-8a8b-3e5f2a1b1c3c")
LANGGRAPH_COURSE_UUID = uuid.UUID("8b3f92d4-fc3a-4a25-9b2c-4f5f8b9b2c2d")


async def seed_data():
    print(f"Connecting to database at: {settings.DATABASE_URL}")
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with SessionLocal() as db:
        print("Truncating old tables (cascading)...")
        # Run truncation inside a transaction
        tables = [
            "answers",
            "submissions",
            "questions",
            "quizzes",
            "lesson_progresses",
            "course_progresses",
            "enrollments",
            "chat_histories",
            "ai_usage_logs",
            "onboarding_data",
            "user_profiles",
            "users",
            "lessons",
            "courses"
        ]
        for table in tables:
            await db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
        await db.commit()
        print("Truncation complete.")

        print("Seeding test user...")
        hashed_pwd = hash_password("password123")
        test_user = User(
            email="test@test.com",
            hashed_password=hashed_pwd,
            role="student",
            is_active=True
        )
        db.add(test_user)
        await db.flush()  # Obtain user ID UUID

        test_profile = UserProfile(
            user_id=test_user.id,
            full_name="Demo Student",
            bio="A student eager to learn Python, LlamaIndex, and LangGraph.",
            avatar_url="https://api.dicebear.com/7.x/adventurer/svg?seed=DemoStudent"
        )
        test_onboarding = OnboardingData(
            user_id=test_user.id,
            topic="Programming",
            level="Beginner",
            hours_per_week=5.0
        )
        db.add(test_profile)
        db.add(test_onboarding)

        print("Seeding courses...")
        # 1. Python Basics
        course_python = Course(
            id=PYTHON_COURSE_UUID,
            title="Python Programming Basics",
            description="Master variables, collections, loops, and OOP concepts in Python.",
            difficulty="Beginner",
            duration="5.5 hrs"
        )
        db.add(course_python)

        # 2. LlamaIndex
        course_llama = Course(
            id=LLAMA_COURSE_UUID,
            title="Building RAG Pipelines with LlamaIndex",
            description="Learn index construction, vector retrieval models, and contextual LLM generation.",
            difficulty="Intermediate",
            duration="4.5 hrs"
        )
        db.add(course_llama)

        # 3. LangGraph
        course_lang = Course(
            id=LANGGRAPH_COURSE_UUID,
            title="Multi-Agent Coordination with LangGraph",
            description="Master state graphs, cognitive agent routing loops, and human-in-the-loop triggers.",
            difficulty="Advanced",
            duration="6.0 hrs"
        )
        db.add(course_lang)

        await db.flush()

        print("Seeding lessons...")
        # Python lessons
        python_lessons = [
            ("Introduction to Python", "10 mins", 1),
            ("Variables, Expressions and Operators", "25 mins", 2),
            ("Control Flow: Loops and Branches", "30 mins", 3),
            ("Data Structures: Lists, Tuples, Dicts", "45 mins", 4),
            ("Object-Oriented Programming (OOP) in Python", "60 mins", 5),
        ]
        for title, dur, idx in python_lessons:
            db.add(Lesson(
                course_id=PYTHON_COURSE_UUID,
                title=title,
                duration=dur,
                order=idx
            ))

        # LlamaIndex lessons
        llama_lessons = [
            ("Introduction to Retrieval-Augmented Generation", "15 mins", 1),
            ("Loading & Chunking Documents", "25 mins", 2),
            ("Vector Indexing & Embedding Configuration", "35 mins", 3),
            ("Querying Vector Stores & Response Synthesis", "40 mins", 4),
            ("Custom Retrievers & Postprocessors", "45 mins", 5),
        ]
        for title, dur, idx in llama_lessons:
            db.add(Lesson(
                course_id=LLAMA_COURSE_UUID,
                title=title,
                duration=dur,
                order=idx
            ))

        # LangGraph lessons
        lang_lessons = [
            ("Introduction to Stateful Multi-Agent Workflows", "15 mins", 1),
            ("Defining States, Nodes, and Entry Points", "30 mins", 2),
            ("Cognitive Routing with Conditional Edges", "35 mins", 3),
            ("State Persistence, Checkpointing, and Short-term Memory", "45 mins", 4),
            ("Human-in-the-loop Editing and Time Travel", "50 mins", 5),
        ]
        for title, dur, idx in lang_lessons:
            db.add(Lesson(
                course_id=LANGGRAPH_COURSE_UUID,
                title=title,
                duration=dur,
                order=idx
            ))

        await db.flush()

        print("Seeding quizzes...")
        # Quiz 1: Python Basics Quiz
        quiz_python = Quiz(
            course_id=PYTHON_COURSE_UUID,
            title="Python Programming Basics Quiz"
        )
        db.add(quiz_python)
        await db.flush()

        python_questions = [
            ("What is the output of print(type([]))?", ["<class 'list'>", "<class 'dict'>", "<class 'tuple'>", "<class 'set'>"], 0),
            ("Which keyword is used to define a function in Python?", ["func", "def", "function", "lambda"], 1),
            ("How do you start a comment in Python?", ["//", "/*", "#", "--"], 2),
            ("Which of these is a mutable data type in Python?", ["tuple", "str", "int", "list"], 3),
            ("What is the default return value of a function that doesn't return anything?", ["Null", "None", "false", "0"], 1)
        ]
        for text_q, opts, correct in python_questions:
            db.add(Question(
                quiz_id=quiz_python.id,
                text=text_q,
                options=opts,
                correct_answer_idx=correct
            ))

        # Quiz 2: LlamaIndex Quiz
        quiz_llama = Quiz(
            course_id=LLAMA_COURSE_UUID,
            title="RAG Pipelines & LlamaIndex Quiz"
        )
        db.add(quiz_llama)
        await db.flush()

        llama_questions = [
            ("What does RAG stand for?", ["Random Access Generation", "Retrieval-Augmented Generation", "Recursive Agent Graph", "Read-Analyze-Generate"], 1),
            ("What is the primary function of a VectorStoreIndex?", ["To store text files directly", "To generate embeddings and index node text vectors for semantic search", "To train new neural network weights", "To serialize JSON data"], 1),
            ("In LlamaIndex, what represents a parsed chunk of a document?", ["Leaf", "Node", "Index", "Query"], 1),
            ("Which component handles combining matching context nodes with the prompt in LlamaIndex?", ["Retriever", "Response Synthesizer", "Storage Context", "Document Agent"], 1),
            ("Which LLM is used by default if none is configured in LlamaIndex?", ["GPT-3.5-Turbo / GPT-4", "Claude 3", "LLaMA 3", "Gemini 1.5 Pro"], 0)
        ]
        for text_q, opts, correct in llama_questions:
            db.add(Question(
                quiz_id=quiz_llama.id,
                text=text_q,
                options=opts,
                correct_answer_idx=correct
            ))

        await db.commit()
        print("Database seeded successfully with test records!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_data())
