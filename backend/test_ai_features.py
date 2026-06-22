"""Unit and integration tests for Phase 8 GenAI features.

This file tests:
1. Dynamic Quiz generation (POST /ai/generate-quiz)
2. Data-driven Study Plan generation (POST /ai/study-plan)
3. Concept Map generation (POST /ai/concept-map)
4. Answer Feedback (POST /ai/feedback)
5. Redis caching integration
6. SQL token usage logging
"""

import os
import sys
import json
import uuid
import unittest
from unittest.mock import AsyncMock, patch, MagicMock

# Set mock environment variables before imports
os.environ["OPENAI_API_KEY"] = "mock-key-for-testing"
os.environ["GENAI_MODEL"] = "gpt-4"

# Add backend and root directories to path
backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(backend_dir)
sys.path.append(backend_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from fastapi.testclient import TestClient
from main import app
from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.course import Lesson, Course
from app.models.progress import LessonProgress
from app.models.quiz import Quiz, Submission
from app.services.ai_service import AIService, RedisCache, call_llm_json
from app.schemas.ai import (
    GenerateQuizResponse,
    NewStudyPlanResponse,
    ConceptMapResponse,
    AnswerFeedbackResponse
)

# Helper mock for SQLAlchemy results
class MockResult:
    def __init__(self, scalar_val=None, scalars_list=None):
        self.scalar_val = scalar_val
        self.scalars_list = scalars_list or []

    def scalar_one_or_none(self):
        return self.scalar_val

    def scalars(self):
        class ScalarResult:
            def __init__(self, items):
                self.items = items
            def all(self):
                return self.items
            def first(self):
                return self.items[0] if self.items else None
        return ScalarResult(self.scalars_list)


# Shared Mock DB Session
class MockAsyncSession:
    def __init__(self):
        self.added_entities = []
        self.committed = False
        self.rolled_back = False
        self.execute_side_effect = None

    def add(self, entity):
        self.added_entities.append(entity)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def execute(self, statement):
        if self.execute_side_effect:
            return await self.execute_side_effect(statement)
        return MockResult()


# Shared Mock Current User
mock_user_id = uuid.uuid4()
mock_user = User(
    id=mock_user_id,
    email="test_student@example.com",
    role="student",
    is_active=True,
    is_deleted=False
)


class TestAiFeatures(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db = MockAsyncSession()
        # Clean Redis cache mock dict before each test
        self.cache_store = {}

        # Patch RedisCache methods directly
        self.redis_get_patcher = patch.object(RedisCache, "get", new_callable=AsyncMock)
        self.redis_set_patcher = patch.object(RedisCache, "set", new_callable=AsyncMock)
        
        self.mock_redis_get = self.redis_get_patcher.start()
        self.mock_redis_set = self.redis_set_patcher.start()

        # Wire Redis mocks to use self.cache_store
        async def fake_get(key):
            return self.cache_store.get(key)
        async def fake_set(key, value, expire=3600):
            self.cache_store[key] = value
            return True

        self.mock_redis_get.side_effect = fake_get
        self.mock_redis_set.side_effect = fake_set

    def tearDown(self):
        self.redis_get_patcher.stop()
        self.redis_set_patcher.stop()

    @patch("litellm.acompletion", new_callable=AsyncMock)
    async def test_call_llm_json_success(self, mock_acompletion):
        """Verifies call_llm_json successfully parses and validates a healthy LLM JSON payload."""
        mock_response_data = {
            "quiz_title": "Test Quiz",
            "difficulty": "Intermediate",
            "questions": []
        }
        
        # Configure Mock Response from LiteLLM
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content=json.dumps(mock_response_data)))
        ]
        mock_completion.get.return_value = {"total_tokens": 50}
        # Simulate completion cost helper
        with patch("litellm.completion_cost", return_value=0.0025):
            mock_acompletion.return_value = mock_completion
            
            # Temporarily restore real API key check to skip mock fallback
            with patch.dict(os.environ, {"OPENAI_API_KEY": "real-key-for-test"}):
                result, tokens, cost = await call_llm_json("Some prompt", GenerateQuizResponse)
                
                self.assertIsInstance(result, GenerateQuizResponse)
                self.assertEqual(result.quiz_title, "Test Quiz")
                self.assertEqual(tokens, 50)
                self.assertEqual(cost, 0.0025)

    async def test_generate_quiz_service(self):
        """Tests generate_quiz_genai logic with DB query handling and prompt creation."""
        lesson_id = uuid.uuid4()
        course_id = uuid.uuid4()
        
        # Setup DB execute side effect to return a lesson
        async def db_execute(stmt):
            # Check if querying Lesson
            if "lessons" in str(stmt):
                lesson = Lesson(id=lesson_id, course_id=course_id, title="Python Programming Basics", duration="30 mins")
                return MockResult(scalar_val=lesson)
            return MockResult()

        self.db.execute_side_effect = db_execute

        # Execute
        quiz_data = await AIService.generate_quiz_genai(
            db=self.db,
            lesson_id=lesson_id,
            difficulty="Beginner",
            num_questions=5,
            user_id=mock_user_id
        )

        # Assertions
        self.assertIsInstance(quiz_data, GenerateQuizResponse)
        self.assertEqual(quiz_data.quiz_title, "Python Programming Basics")
        self.assertEqual(len(quiz_data.questions), 3)  # Mock returns 3 questions
        
        # Verify SQL Token Usage Log was registered
        self.assertEqual(len(self.db.added_entities), 1)
        self.assertEqual(self.db.added_entities[0].action, "generate_quiz")
        self.assertTrue(self.db.committed)

    async def test_generate_study_plan_service_caching_and_scores(self):
        """Tests that study plan retrieves weak lessons (< 60% score) and leverages Redis caching."""
        # 1. First run (Cache Miss)
        # Setup mock db data:
        # - 1 LessonProgress (completed)
        # - 1 Submission with score 1/5 (20% - weak topic)
        # - 1 Quiz referenced by submission
        async def db_execute(stmt):
            stmt_str = str(stmt).lower()
            if "lesson_progresses" in stmt_str:
                progress = LessonProgress(user_id=mock_user_id, lesson_id=uuid.uuid4(), completed=True)
                return MockResult(scalars_list=[progress])
            elif "submissions" in stmt_str:
                submission = Submission(user_id=mock_user_id, quiz_id=uuid.uuid4(), score=1, total_questions=5)
                return MockResult(scalars_list=[submission])
            elif "quizzes" in stmt_str:
                quiz = Quiz(id=uuid.uuid4(), title="Control Flows Quiz")
                return MockResult(scalar_val=quiz)
            return MockResult()

        self.db.execute_side_effect = db_execute

        # Run Live Call
        plan_data = await AIService.generate_study_plan_genai(db=self.db, user_id=mock_user_id)
        self.assertIsInstance(plan_data, NewStudyPlanResponse)
        self.assertIn(f"study_plan:{mock_user_id}", self.cache_store) # Saved in cache!
        self.assertEqual(len(self.db.added_entities), 1) # usage logged
        
        # Reset DB usage logging states
        self.db.added_entities.clear()
        
        # 2. Second run (Cache Hit)
        cached_plan = await AIService.generate_study_plan_genai(db=self.db, user_id=mock_user_id)
        self.assertEqual(cached_plan.week_goal, plan_data.week_goal)
        self.assertEqual(len(self.db.added_entities), 0) # No new usage logged since cached

    async def test_generate_concept_map_service_caching(self):
        """Tests concept map generation and verify caching under topic keys."""
        topic = "Recursion"
        
        # Run 1: Cache Miss
        map_data = await AIService.generate_concept_map_genai(db=self.db, topic=topic, user_id=mock_user_id)
        self.assertIsInstance(map_data, ConceptMapResponse)
        self.assertIn(f"concept_map:{topic.lower()}", self.cache_store) # Saved in cache under prefixed lowercase key
        
        # Run 2: Cache Hit
        cached_map = await AIService.generate_concept_map_genai(db=self.db, topic=topic, user_id=mock_user_id)
        self.assertEqual(len(cached_map.nodes), len(map_data.nodes))

    async def test_generate_answer_feedback_validation(self):
        """Tests answer evaluation and ensures exactly 3 suggestions constraint holds."""
        feedback = await AIService.generate_answer_feedback_genai(
            db=self.db,
            question="What is recursion?",
            student_answer="A function calling itself",
            correct_answer="A programming method where a function calls itself directly or indirectly.",
            user_id=mock_user_id
        )
        self.assertIsInstance(feedback, AnswerFeedbackResponse)
        self.assertEqual(len(feedback.improvements), 3)


class TestAiRoutesIntegration(unittest.TestCase):
    def setUp(self):
        # Override dependencies globally on app
        self.db_mock = MockAsyncSession()
        
        # Stub database queries to return successful resources
        async def db_execute(stmt):
            stmt_str = str(stmt).lower()
            if "lessons" in stmt_str:
                lesson = Lesson(id=uuid.uuid4(), course_id=uuid.uuid4(), title="Test Lesson", duration="10m")
                return MockResult(scalar_val=lesson)
            return MockResult()
        self.db_mock.execute_side_effect = db_execute

        app.dependency_overrides[get_db] = lambda: self.db_mock
        app.dependency_overrides[get_current_user] = lambda: mock_user

        # Create Client
        self.client = TestClient(app)

        # Mock RedisCache inside service to prevent hitting connection failures during requests
        self.redis_get_patcher = patch.object(RedisCache, "get", new_callable=AsyncMock, return_value=None)
        self.redis_set_patcher = patch.object(RedisCache, "set", new_callable=AsyncMock, return_value=True)
        self.redis_get_patcher.start()
        self.redis_set_patcher.start()

    def tearDown(self):
        app.dependency_overrides.clear()
        self.redis_get_patcher.stop()
        self.redis_set_patcher.stop()

    def test_post_generate_quiz_route(self):
        """Verifies POST /api/v1/ai/generate-quiz returns wrapped GenerateQuizResponse JSON."""
        lesson_id = str(uuid.uuid4())
        payload = {
            "lesson_id": lesson_id,
            "difficulty": "Beginner",
            "num_questions": 5
        }
        response = self.client.post("/api/v1/ai/generate-quiz", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["data"]["difficulty"], "Beginner")
        self.assertIn("questions", data["data"])

    def test_post_study_plan_route(self):
        """Verifies POST /api/v1/ai/study-plan returns wrapped NewStudyPlanResponse JSON."""
        payload = {
            "user_id": str(mock_user_id)
        }
        response = self.client.post("/api/v1/ai/study-plan", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("week_goal", data["data"])
        self.assertIn("daily_plans", data["data"])

    def test_post_concept_map_route(self):
        """Verifies POST /api/v1/ai/concept-map returns wrapped ConceptMapResponse JSON."""
        payload = {
            "topic": "FastAPI Dependency Injection"
        }
        response = self.client.post("/api/v1/ai/concept-map", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("nodes", data["data"])
        self.assertIn("edges", data["data"])

    def test_post_feedback_route(self):
        """Verifies POST /api/v1/ai/feedback returns wrapped AnswerFeedbackResponse JSON."""
        payload = {
            "question": "What is Python?",
            "student_answer": "A programming language.",
            "correct_answer": "An interpreted, high-level, general-purpose programming language."
        }
        response = self.client.post("/api/v1/ai/feedback", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["data"]["improvements"]), 3)
        self.assertGreaterEqual(data["data"]["score"], 0)


if __name__ == "__main__":
    unittest.main()
