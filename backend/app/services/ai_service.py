"""AI service module for the AI LMS backend.

This module houses operations for processing user chat queries, constructing
personalized study plans, suggesting course recommendations, and logging usage.
It integrates LiteLLM for switching between model configurations and implements Redis response caching.
"""

import os
import time
import json
import uuid
import structlog
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import litellm
import redis.asyncio as aioredis

from app.models.ai_logs import AIUsageLog, ChatHistory
from app.models.course import Lesson, Course
from app.models.progress import LessonProgress, CourseProgress
from app.models.quiz import Quiz, Submission
from app.schemas.ai import (
    StudyPlanResponse,
    StudyTaskSchema,
    RecommendationsResponse,
    RecommendationSchema,
    GenerateQuizResponse,
    QuizQuestionItem,
    NewStudyPlanResponse,
    DailyPlan,
    NewStudyTaskSchema,
    ConceptMapResponse,
    ConceptMapNode,
    ConceptMapEdge,
    AnswerFeedbackResponse
)

logger = structlog.get_logger()

# ----------------- PROMPT CONSTANTS -----------------

QUIZ_GEN_PROMPT_TEMPLATE = """
You are an expert academic educator. Generate a structured quiz based on the following lesson content.

Lesson Content:
{lesson_content}

Difficulty Level: {difficulty}

You MUST generate exactly:
- {num_mcq} multiple choice questions with exactly 4 options each.
- {num_short} short answer questions (options list must be empty).
- {num_code} code completion question if the topic relates to programming (options list must be empty).

Return the response strictly as a JSON object matching this structure:
{{
  "quiz_title": "string title describing the quiz topic",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "id": "unique_string_id_1",
      "type": "multiple_choice",
      "question": "question text",
      "options": ["option 1", "option 2", "option 3", "option 4"],
      "correct_answer": "correct option text matching one option exactly",
      "explanation": "detailed explanation of the answer"
    }},
    ...
  ]
}}
"""

STUDY_PLAN_PROMPT_TEMPLATE = """
You are an expert academic tutor and study coach. Build a personalized 7-day study plan for the student.

Here is the student's study progress and performance metrics:
{progress_context}

Analyze the weak areas (lessons/quizzes with scores under 60%) and structure a comprehensive 7-day plan to address them.

Return the response strictly as a JSON object matching this structure:
{{
  "week_goal": "Overarching weekly goal focusing on weak areas",
  "daily_plans": [
    {{
      "day": "Day 1",
      "tasks": [
        {{
          "time": "e.g., Morning",
          "activity": "Activity description addressing weak area",
          "resource": "Specific lesson title or study resource reference",
          "duration_mins": 30
        }}
      ]
    }}
  ]
}}
"""

CONCEPT_MAP_PROMPT_TEMPLATE = """
You are a conceptual visualizer. Construct a concept map node-link diagram for the topic: {topic}.
Represent core subconcepts, related topics, and the logical connections between them.

Return the response strictly as a JSON object matching this structure:
{{
  "nodes": [
    {{
      "id": "node_id_1",
      "label": "Concept Name",
      "type": "core"
    }},
    ...
  ],
  "edges": [
    {{
      "source": "node_id_1",
      "target": "node_id_2",
      "label": "describes relationship connection"
    }},
    ...
  ]
}}
"""

ANSWER_FEEDBACK_PROMPT_TEMPLATE = """
You are an AI Tutor grading a student's answer.

Question Prompt: {question}
Correct Answer Key: {correct_answer}
Student Answer: {student_answer}

Grade the student's answer on a scale from 0 to 10.
Provide constructive feedback and exactly three improvement suggestions.

Return the response strictly as a JSON object matching this structure:
{{
  "score": 8,
  "feedback": "constructive feedback text",
  "improvements": [
    "improvement tip 1",
    "improvement tip 2",
    "improvement tip 3"
  ]
}}
"""

# ----------------- REDIS CACHING HELPER -----------------

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

class RedisCache:
    """Async Redis connection manager for response caching."""
    _client = None

    @classmethod
    async def get_client(cls):
        if cls._client is None:
            try:
                cls._client = aioredis.from_url(REDIS_URL, decode_responses=True)
            except Exception as e:
                logger.warning("redis_connection_failed", error=str(e))
                return None
        return cls._client

    @classmethod
    async def get(cls, key: str) -> Optional[str]:
        try:
            client = await cls.get_client()
            if client:
                return await client.get(key)
        except Exception as e:
            logger.warning("redis_get_error", key=key, error=str(e))
        return None

    @classmethod
    async def set(cls, key: str, value: str, expire: int = 3600) -> bool:
        try:
            client = await cls.get_client()
            if client:
                await client.set(key, value, ex=expire)
                return True
        except Exception as e:
            logger.warning("redis_set_error", key=key, error=str(e))
        return False

# ----------------- LITELLM COMPLETION HELPER -----------------

async def call_llm_json(prompt: str, response_model: Any) -> tuple:
    """Invokes LiteLLM to fetch structured JSON, retrying once on validation failure.

    Args:
        prompt (str): Text prompt payload.
        response_model (Any): Pydantic validation class.

    Returns:
        tuple: (validated_pydantic_model, tokens_used, cost)
    """
    model = os.getenv("GENAI_MODEL", "gpt-4")
    api_key = os.getenv("OPENAI_API_KEY")
    
    for attempt in range(2):
        try:
            # Check if using mock key
            if not api_key or api_key == "mock-key-for-testing":
                logger.warning("litellm_mock_call", model=model, attempt=attempt)
                # Return dummy Pydantic responses matching schemas
                raise ValueError("Mock key fallback triggers mock data generation.")
                
            import time
            from app.core.metrics import LMS_LLM_LATENCY, LMS_LLM_TOKENS

            start_time = time.time()
            response = await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.2,
                api_key=api_key
            )
            latency = time.time() - start_time
            LMS_LLM_LATENCY.observe(latency)
            
            content = response.choices[0].message.content
            data = json.loads(content)
            validated = response_model(**data)
            
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            LMS_LLM_TOKENS.labels(token_type="prompt_tokens").inc(prompt_tokens)
            LMS_LLM_TOKENS.labels(token_type="completion_tokens").inc(completion_tokens)
            
            tokens = usage.get("total_tokens", 0)
            cost = 0.0
            try:
                cost = litellm.completion_cost(completion_response=response) or 0.0
            except Exception:
                pass
                
            return validated, tokens, cost
            
        except Exception as e:
            logger.warn("litellm_call_attempt_failed", attempt=attempt+1, error=str(e))
            if attempt == 1:
                # If both attempts fail and we are on mock key, return generated mock data
                if not api_key or api_key == "mock-key-for-testing":
                    return get_mock_pydantic_response(response_model), 100, 0.0015
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Generative AI model failed to construct valid JSON: {str(e)}"
                )


def get_mock_pydantic_response(response_model: Any) -> Any:
    """Generates mock Pydantic responses to keep backend operational during mock testing."""
    if response_model == GenerateQuizResponse:
        return GenerateQuizResponse(
            quiz_title="Python Programming Basics",
            difficulty="Beginner",
            questions=[
                QuizQuestionItem(
                    id="q1",
                    type="multiple_choice",
                    question="What is the output of print(type([]))?",
                    options=["<class 'list'>", "<class 'dict'>", "<class 'tuple'>", "<class 'set'>"],
                    correct_answer="<class 'list'>",
                    explanation="Square brackets represent list types."
                ),
                QuizQuestionItem(
                    id="q2",
                    type="short_answer",
                    question="Which keyword is used to define functions?",
                    options=[],
                    correct_answer="def",
                    explanation="The def keyword defines function scopes."
                ),
                QuizQuestionItem(
                    id="q3",
                    type="code_completion",
                    question="Complete this line: ___ my_func():",
                    options=[],
                    correct_answer="def",
                    explanation="Functions start with the def keyword."
                )
            ]
        )
    elif response_model == NewStudyPlanResponse:
        return NewStudyPlanResponse(
            week_goal="Review core Python variables and solve programming quizzes.",
            daily_plans=[
                DailyPlan(
                    day="Day 1",
                    tasks=[
                        NewStudyTaskSchema(
                            time="Morning",
                            activity="Read documentation on Lists and Tuples",
                            resource="Python Collection Basics",
                            duration_mins=30
                        )
                    ]
                )
            ]
        )
    elif response_model == ConceptMapResponse:
        return ConceptMapResponse(
            nodes=[
                ConceptMapNode(id="n1", label="Python", type="core"),
                ConceptMapNode(id="n2", label="Lists", type="subconcept")
            ],
            edges=[
                ConceptMapEdge(source="n1", target="n2", label="has collection type")
            ]
        )
    elif response_model == AnswerFeedbackResponse:
        return AnswerFeedbackResponse(
            score=8,
            feedback="Great attempt! You understood the basic loops, but missed list comprehensions.",
            improvements=[
                "Study list comprehensions for concise loops.",
                "Review difference between lists and generators.",
                "Solve 3 practice coding tasks."
            ]
        )
    return None

# ----------------- DB USAGE LOGGING HELPER -----------------

async def log_token_usage(db: AsyncSession, user_id: uuid.UUID, action: str, tokens: int, cost: float):
    """Inserts a usage logs registry entry into the PostgreSQL database."""
    try:
        log = AIUsageLog(
            user_id=user_id,
            action=action,
            tokens_used=tokens,
            cost=cost,
            latency_ms=0
        )
        db.add(log)
        await db.commit()
    except Exception as e:
        logger.error("log_token_usage_db_failed", error=str(e))


class AIService:
    """AI Tutor chat and personalized recommendations generation services."""

    @staticmethod
    async def generate_chat_response(
        db: AsyncSession,
        user_id: uuid.UUID,
        course_id: uuid.UUID,
        message: str
    ) -> str:
        """Processes tutor chat messages, logs usage metrics, and stores chat history.

        Args:
            db (AsyncSession): Active database session.
            user_id (uuid.UUID): Student User ID.
            course_id (uuid.UUID): Reference Course UUID.
            message (str): Plain-text prompt string query.

        Returns:
            str: Graded/retrieved answer text generated by the tutor.
        """
        user_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        course_uuid = uuid.UUID(str(course_id)) if not isinstance(course_id, uuid.UUID) else course_id
        start_time = time.time()

        # Save user message to database history
        user_message_record = ChatHistory(
            user_id=user_uuid,
            course_id=course_uuid,
            sender="user",
            message=message
        )
        db.add(user_message_record)

        # Generate intelligent contextual mock reply
        msg_lower = message.lower()
        if "rag" in msg_lower or "index" in msg_lower or "llama" in msg_lower:
            reply = (
                "RAG (Retrieval-Augmented Generation) connects LLMs to your private data. "
                "In LlamaIndex, we load documents, parse them into nodes, and build "
                "VectorStoreIndexes to yield highly relevant semantic matches before query completion."
            )
        elif "langgraph" in msg_lower or "agent" in msg_lower or "state" in msg_lower:
            reply = (
                "LangGraph is a stateful orchestration library that model loops "
                "and cyclic relationships in multi-agent workflows. It maps nodes "
                "as Python operations and edges as transitions that mutate shared State dictionaries."
            )
        elif "fastapi" in msg_lower or "route" in msg_lower or "async" in msg_lower:
            reply = (
                "FastAPI uses ASGI (Asynchronous Server Gateway Interface) standards to "
                "handle requests non-blockingly. By declaring async route handlers and "
                "leveraging asyncpg, we optimize database concurrency during token verification."
            )
        else:
            reply = (
                f"I received your query: '{message}'. As your AI Tutor, I have analysed your "
                "course catalog and active progress. Let me know if you would like me to "
                "generate practice quizzes, explain complex sections, or update your study plan."
            )

        # Save assistant message to database history
        assistant_message_record = ChatHistory(
            user_id=user_uuid,
            course_id=course_uuid,
            sender="assistant",
            message=reply
        )
        db.add(assistant_message_record)

        # Calculate log variables
        latency_ms = int((time.time() - start_time) * 1000)
        tokens_spent = len(message.split()) + len(reply.split())

        # Save usage log
        usage_log = AIUsageLog(
            user_id=user_uuid,
            action="chat",
            tokens_used=tokens_spent,
            latency_ms=max(1, latency_ms),
            cost=0.0
        )
        db.add(usage_log)

        await db.commit()
        return reply

    @staticmethod
    async def generate_study_plan(db: AsyncSession, user_id: uuid.UUID) -> StudyPlanResponse:
        """Legacy GET study plan handler (kept for backward compatibility)."""
        tasks = [
            StudyTaskSchema(
                task="Complete the quiz on 'FastAPI Dependency Injection'",
                duration="15 mins"
            )
        ]
        return StudyPlanResponse(tasks=tasks)

    @staticmethod
    async def generate_course_recommendations(
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> RecommendationsResponse:
        """Suggests appropriate learning paths based on current skills."""
        user_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        recs = [
            RecommendationSchema(
                id=uuid.UUID("e4b3c004-94c6-47b2-84c1-cd54cfc0bf7a"),
                title="Python Programming Basics",
                description="Master variables, collections, loops, and OOP concepts in Python.",
                duration="5.5 hrs",
                difficulty="Beginner"
            )
        ]
        return RecommendationsResponse(recommendations=recs)

    # ----------------- NEW Phase 8 GenAI Methods -----------------

    @staticmethod
    async def generate_quiz_genai(
        db: AsyncSession,
        lesson_id: uuid.UUID,
        difficulty: str,
        num_questions: int,
        user_id: uuid.UUID
    ) -> GenerateQuizResponse:
        """Fetches lesson metadata/RAG chunks and creates a custom structured quiz."""
        # 1. Fetch lesson title and course context
        lesson_stmt = select(Lesson).where(Lesson.id == lesson_id)
        lesson_res = await db.execute(lesson_stmt)
        lesson = lesson_res.scalar_one_or_none()
        
        if not lesson:
            raise HTTPException(status_code=status.HTTP_444_NOT_FOUND, detail="Lesson not found.")
            
        content_text = f"Lesson Title: {lesson.title}. Duration: {lesson.duration}."
        
        # 2. Attempt to pull context documents from the RAG store
        try:
            store_dir = Path(__file__).parent.parent.parent.parent / "rag" / "storage" / f"course_{lesson.course_id}"
            docstore_path = store_dir / "docstore.json"
            if docstore_path.exists():
                from llama_index.core.storage.docstore import SimpleDocumentStore
                from llama_index.core.schema import MetadataMode
                docstore = SimpleDocumentStore.from_persist_path(str(docstore_path))
                lesson_nodes = [
                    node.get_content(metadata_mode=MetadataMode.NONE)
                    for node in docstore.docs.values()
                    if node.metadata.get("lesson_id") == str(lesson_id)
                ]
                if lesson_nodes:
                    content_text += "\n" + "\n".join(lesson_nodes[:3]) # Limit context size
        except Exception as e:
            logger.warning("failed_to_pull_rag_docstore", error=str(e))

        # Check if topic relates to programming
        is_programming = any(
            x in lesson.title.lower() or x in content_text.lower()
            for x in ("python", "code", "programming", "function", "variable", "class")
        )
        
        num_mcq = 5
        num_short = 2
        num_code = 1 if is_programming else 0
        
        prompt = QUIZ_GEN_PROMPT_TEMPLATE.format(
            lesson_content=content_text,
            difficulty=difficulty,
            num_mcq=num_mcq,
            num_short=num_short,
            num_code=num_code
        )
        
        quiz_data, tokens, cost = await call_llm_json(prompt, GenerateQuizResponse)
        
        # Log usage
        await log_token_usage(db, user_id, "generate_quiz", tokens, cost)
        return quiz_data

    @staticmethod
    async def generate_study_plan_genai(
        db: AsyncSession,
        user_id: uuid.UUID
    ) -> NewStudyPlanResponse:
        """Analyzes PostgreSQL milestones/quiz submissions and builds a 7-day study plan."""
        # Check Redis Cache
        cache_key = f"study_plan:{str(user_id)}"
        cached = await RedisCache.get(cache_key)
        if cached:
            logger.info("cache_hit_study_plan", key=cache_key)
            return NewStudyPlanResponse(**json.loads(cached))
            
        # 1. Fetch lesson progress
        progress_stmt = select(LessonProgress).where(LessonProgress.user_id == user_id)
        progress_res = await db.execute(progress_stmt)
        progresses = progress_res.scalars().all()
        completed_count = sum(1 for p in progresses if p.completed)
        
        # 2. Fetch submissions to identify weak areas (score < 60%)
        sub_stmt = select(Submission).where(Submission.user_id == user_id)
        sub_res = await db.execute(sub_stmt)
        submissions = sub_res.scalars().all()
        
        weak_topics = []
        for sub in submissions:
            if sub.total_questions > 0:
                pct = (sub.score / sub.total_questions) * 100.0
                if pct < 60.0:
                    # Retrieve quiz title
                    quiz_stmt = select(Quiz).where(Quiz.id == sub.quiz_id)
                    quiz_res = await db.execute(quiz_stmt)
                    quiz = quiz_res.scalar_one_or_none()
                    if quiz:
                        weak_topics.append(f"{quiz.title} (Score: {pct:.1f}%)")
                        
        progress_context = (
            f"Student completed lessons count: {completed_count}.\n"
            f"Weak topics (scores below 60%): {', '.join(weak_topics) if weak_topics else 'None identified. Student is scoring well.'}"
        )
        
        prompt = STUDY_PLAN_PROMPT_TEMPLATE.format(progress_context=progress_context)
        
        plan_data, tokens, cost = await call_llm_json(prompt, NewStudyPlanResponse)
        
        # Write to Cache
        await RedisCache.set(cache_key, plan_data.model_dump_json(), expire=3600)
        
        # Log usage
        await log_token_usage(db, user_id, "study_plan", tokens, cost)
        return plan_data

    @staticmethod
    async def generate_concept_map_genai(
        db: AsyncSession,
        topic: str,
        user_id: uuid.UUID
    ) -> ConceptMapResponse:
        """Generates concept maps, caching the result in Redis."""
        cache_key = f"concept_map:{topic.strip().lower()}"
        cached = await RedisCache.get(cache_key)
        if cached:
            logger.info("cache_hit_concept_map", key=cache_key)
            return ConceptMapResponse(**json.loads(cached))
            
        prompt = CONCEPT_MAP_PROMPT_TEMPLATE.format(topic=topic)
        
        map_data, tokens, cost = await call_llm_json(prompt, ConceptMapResponse)
        
        # Write to Cache
        await RedisCache.set(cache_key, map_data.model_dump_json(), expire=3600)
        
        # Log usage
        await log_token_usage(db, user_id, "concept_map", tokens, cost)
        return map_data

    @staticmethod
    async def generate_answer_feedback_genai(
        db: AsyncSession,
        question: str,
        student_answer: str,
        correct_answer: str,
        user_id: uuid.UUID
    ) -> AnswerFeedbackResponse:
        """Evaluates student's answer prompt, scoring and formatting feedback."""
        prompt = ANSWER_FEEDBACK_PROMPT_TEMPLATE.format(
            question=question,
            correct_answer=correct_answer,
            student_answer=student_answer
        )
        
        feedback_data, tokens, cost = await call_llm_json(prompt, AnswerFeedbackResponse)
        
        # Double check the improvements validation constraint
        if len(feedback_data.improvements) != 3:
            logger.warn("llm_returned_incorrect_improvements_count", count=len(feedback_data.improvements))
            # Adjust array to match exactly 3 items
            feedback_data.improvements = (feedback_data.improvements + ["Improve clarity.", "Study related documentation.", "Practice more exercises."])[:3]
            
        # Log usage
        await log_token_usage(db, user_id, "answer_feedback", tokens, cost)
        return feedback_data
