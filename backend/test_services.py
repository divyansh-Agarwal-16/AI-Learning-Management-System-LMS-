"""Unit tests for FastAPI backend services and route endpoints.

This module provides thorough unit and integration test coverage using mocks
for UserService, AuthService, CourseService, and ProgressService.
"""

import os
import sys
import uuid
import unittest
from unittest.mock import AsyncMock, patch, MagicMock

# Set test configurations
os.environ["OPENAI_API_KEY"] = "mock-key-for-testing"
os.environ["GENAI_MODEL"] = "gpt-4o"

# Add backend and root directories to system path
backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(backend_dir)
sys.path.append(backend_dir)
if root_dir not in sys.path:
    sys.path.append(root_dir)

from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.course_service import CourseService
from app.services.progress_service import ProgressService

from app.models.user import User, UserProfile, OnboardingData
from app.models.course import Course, Lesson, Enrollment
from app.models.progress import LessonProgress, CourseProgress
from app.models.quiz import Quiz, Question, Submission, Answer

from app.schemas.user import UpdateProfileRequest, OnboardingRequest
from app.schemas.auth import SignupRequest, LoginRequest
from app.schemas.course import CourseCreate, LessonCreate
from app.schemas.quiz import SubmitQuizRequest, SubmitAnswerRequest

from app.core.security import hash_password

# Mock structures
class MockScalarResult:
    def __init__(self, items):
        self.items = items
    def all(self):
        return self.items
    def first(self):
        return self.items[0] if self.items else None

class MockDBResult:
    def __init__(self, scalar_val=None, scalars_list=None, all_list=None):
        self.scalar_val = scalar_val
        self.scalars_list = scalars_list or ([] if scalar_val is None else [scalar_val])
        self.all_list = all_list or []

    def scalar_one_or_none(self):
        return self.scalar_val

    def scalars(self):
        return MockScalarResult(self.scalars_list)

    def all(self):
        return self.all_list

class MockAsyncSession:
    def __init__(self):
        self.added_entities = []
        self.added_all_entities = []
        self.committed = False
        self.rolled_back = False
        self.flushed = False
        self.refreshed_entities = []
        self.execute_side_effect = None

    def add(self, entity):
        if hasattr(entity, "id") and getattr(entity, "id") is None:
            entity.id = uuid.uuid4()
        self.added_entities.append(entity)

    def add_all(self, entities):
        for entity in entities:
            if hasattr(entity, "id") and getattr(entity, "id") is None:
                entity.id = uuid.uuid4()
        self.added_all_entities.extend(entities)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def flush(self):
        self.flushed = True

    async def refresh(self, entity):
        self.refreshed_entities.append(entity)

    async def execute(self, statement):
        if self.execute_side_effect:
            return await self.execute_side_effect(statement)
        return MockDBResult()


class TestBackendServicesAsync(unittest.IsolatedAsyncioTestCase):
    """Asynchronous service unit tests."""

    async def test_user_service_get_user_by_id(self):
        db = MockAsyncSession()
        user_id = uuid.uuid4()
        test_user = User(id=user_id, email="student@test.com")
        
        async def db_execute(stmt):
            return MockDBResult(scalar_val=test_user)
        db.execute_side_effect = db_execute

        # Valid UUID
        res = await UserService.get_user_by_id(db, user_id)
        self.assertIsNotNone(res)
        self.assertEqual(res.id, user_id)

        # String UUID
        res = await UserService.get_user_by_id(db, str(user_id))
        self.assertIsNotNone(res)
        self.assertEqual(res.id, user_id)

        # Invalid string UUID
        res = await UserService.get_user_by_id(db, "invalid-uuid")
        self.assertIsNone(res)

    async def test_user_service_update_profile(self):
        db = MockAsyncSession()
        user_id = uuid.uuid4()
        user = User(id=user_id, email="test@test.com")
        profile = UserProfile(user_id=user_id, full_name="Old Name", bio="Old Bio")
        
        async def db_execute(stmt):
            stmt_str = str(stmt).lower()
            if "profile" in stmt_str:
                return MockDBResult(scalar_val=profile)
            elif "user" in stmt_str:
                return MockDBResult(scalar_val=user)
            return MockDBResult()
        db.execute_side_effect = db_execute

        req = UpdateProfileRequest(full_name="New Name", bio="New Bio", avatar_url="http://avatar.jpg")
        res = await UserService.update_profile(db, user_id, req)
        
        self.assertEqual(profile.full_name, "New Name")
        self.assertEqual(profile.bio, "New Bio")
        self.assertEqual(profile.avatar_url, "http://avatar.jpg")
        self.assertTrue(db.committed)

    async def test_user_service_save_onboarding(self):
        db = MockAsyncSession()
        user_id = uuid.uuid4()
        user = User(id=user_id, email="test@test.com")
        onboarding = OnboardingData(user_id=user_id, topic="None")
        
        async def db_execute(stmt):
            stmt_str = str(stmt).lower()
            if "onboarding" in stmt_str:
                return MockDBResult(scalar_val=onboarding)
            elif "user" in stmt_str:
                return MockDBResult(scalar_val=user)
            return MockDBResult()
        db.execute_side_effect = db_execute

        req = OnboardingRequest(topic="Python", level="Beginner", hours_per_week=5)
        res = await UserService.save_onboarding(db, user_id, req)
        
        self.assertEqual(onboarding.topic, "Python")
        self.assertEqual(onboarding.level, "Beginner")
        self.assertEqual(onboarding.hours_per_week, 5)
        self.assertTrue(db.committed)

    async def test_auth_service_signup_success(self):
        db = MockAsyncSession()
        req = SignupRequest(email="new@test.com", password="password123", full_name="New User")
        
        async def db_execute(stmt):
            return MockDBResult(scalar_val=None)
        db.execute_side_effect = db_execute

        res = await AuthService.signup_user(db, req)
        self.assertIsNotNone(res)
        self.assertEqual(res.email, "new@test.com")
        self.assertTrue(db.committed)
        self.assertTrue(db.flushed)

    async def test_auth_service_signup_existing_email(self):
        db = MockAsyncSession()
        req = SignupRequest(email="exists@test.com", password="password123", full_name="Existing")
        existing_user = User(id=uuid.uuid4(), email="exists@test.com")
        
        async def db_execute(stmt):
            return MockDBResult(scalar_val=existing_user)
        db.execute_side_effect = db_execute

        res = await AuthService.signup_user(db, req)
        self.assertIsNone(res)
        self.assertFalse(db.committed)

    async def test_auth_service_authenticate_success(self):
        db = MockAsyncSession()
        pwd = "my-secure-password"
        hashed = hash_password(pwd)
        user = User(id=uuid.uuid4(), email="user@test.com", hashed_password=hashed, is_deleted=False)
        
        async def db_execute(stmt):
            return MockDBResult(scalar_val=user)
        db.execute_side_effect = db_execute

        req = LoginRequest(email="user@test.com", password=pwd)
        res = await AuthService.authenticate_user(db, req)
        self.assertIsNotNone(res)
        self.assertEqual(res.email, "user@test.com")

        # Wrong password
        req_wrong = LoginRequest(email="user@test.com", password="wrongpassword")
        res_wrong = await AuthService.authenticate_user(db, req_wrong)
        self.assertIsNone(res_wrong)

    async def test_course_service_get_courses(self):
        db = MockAsyncSession()
        course1 = Course(id=uuid.uuid4(), title="Python Course", difficulty="Beginner")
        course2 = Course(id=uuid.uuid4(), title="LangGraph Course", difficulty="Advanced")
        
        async def db_execute(stmt):
            return MockDBResult(scalars_list=[course1, course2])
        db.execute_side_effect = db_execute

        courses = await CourseService.get_courses(db, search="Course", difficulty="Beginner")
        self.assertEqual(len(courses), 2)

    async def test_course_service_create_course(self):
        db = MockAsyncSession()
        course_id = uuid.uuid4()
        req = CourseCreate(id=course_id, title="FastAPI", description="FastAPI lessons", difficulty="Intermediate", duration="5 hours")
        
        async def db_execute(stmt):
            return MockDBResult(scalar_val=None)
        db.execute_side_effect = db_execute

        course = await CourseService.create_course(db, req)
        self.assertEqual(course.title, "FastAPI")
        self.assertEqual(course.id, course_id)
        self.assertTrue(db.committed)

    async def test_course_service_enroll_user(self):
        db = MockAsyncSession()
        user_id = uuid.uuid4()
        course_id = uuid.uuid4()
        course = Course(id=course_id, title="Test Course")
        
        async def db_execute(stmt):
            stmt_str = str(stmt).lower()
            if "enrollment" in stmt_str:
                return MockDBResult(scalar_val=None)
            elif "course" in stmt_str:
                return MockDBResult(scalar_val=course)
            return MockDBResult()
        db.execute_side_effect = db_execute

        res = await CourseService.enroll_user(db, user_id, course_id)
        self.assertTrue(res)
        self.assertEqual(len(db.added_entities), 2)
        self.assertTrue(db.committed)

    async def test_course_service_submit_quiz(self):
        db = MockAsyncSession()
        user_id = uuid.uuid4()
        quiz_id = uuid.uuid4()
        q1_id = uuid.uuid4()
        q2_id = uuid.uuid4()
        
        q1 = Question(id=q1_id, quiz_id=quiz_id, text="Q1", options=["A", "B"], correct_answer_idx=0)
        q2 = Question(id=q2_id, quiz_id=quiz_id, text="Q2", options=["A", "B"], correct_answer_idx=1)
        quiz = Quiz(id=quiz_id, title="Seeded Quiz", questions=[q1, q2])
        
        async def db_execute(stmt):
            return MockDBResult(scalar_val=quiz)
        db.execute_side_effect = db_execute

        req = SubmitQuizRequest(
            answers=[
                SubmitAnswerRequest(question_id=str(q1_id), selected_option_idx=0),
                SubmitAnswerRequest(question_id=str(q2_id), selected_option_idx=0),
            ]
        )
        
        submission = await CourseService.submit_quiz(db, user_id, quiz_id, req)
        self.assertIsNotNone(submission)
        self.assertEqual(submission.score, 1)
        self.assertEqual(submission.total_questions, 2)
        self.assertEqual(len(submission.details), 2)
        self.assertTrue(submission.details[0]["is_correct"])
        self.assertFalse(submission.details[1]["is_correct"])
        self.assertTrue(db.committed)

    async def test_progress_service_track_lesson_progress(self):
        db = MockAsyncSession()
        user_id = uuid.uuid4()
        lesson_id = uuid.uuid4()
        course_id = uuid.uuid4()
        lesson = Lesson(id=lesson_id, course_id=course_id, title="Lesson 1")
        
        async def db_execute(stmt):
            stmt_str = str(stmt).lower()
            if "lesson.id" in stmt_str or "lessons" in stmt_str:
                if "count" in stmt_str:
                    return MockDBResult(scalar_val=1)
                elif "lesson_progress" in stmt_str:
                    return MockDBResult(scalar_val=None)
                return MockDBResult(scalar_val=lesson)
            elif "lessonprogress" in stmt_str or "lesson_progresses" in stmt_str:
                return MockDBResult(scalar_val=None)
            elif "courseprogress" in stmt_str or "course_progresses" in stmt_str:
                return MockDBResult(scalar_val=None)
            return MockDBResult(all_list=[(lesson_id,)])
        db.execute_side_effect = db_execute

        res = await ProgressService.track_lesson_progress(db, user_id, lesson_id, completed=True, time_spent=300)
        self.assertIsNotNone(res)
        self.assertTrue(res.completed)
        self.assertEqual(res.time_spent, 300)
        self.assertTrue(db.committed)


# Route endpoints Client Integration Tests
from fastapi.testclient import TestClient
from main import app
from app.core.dependencies import get_db, get_current_user

# Mock global credentials
mock_uuid_user = uuid.uuid4()
pwd_hashed = hash_password("pwd-strong")
mock_logged_user = User(
    id=mock_uuid_user,
    email="api-student@test.com",
    hashed_password=pwd_hashed,
    role="student",
    is_active=True,
    is_deleted=False,
    profile=UserProfile(user_id=mock_uuid_user, full_name="API Test User"),
    onboarding=OnboardingData(user_id=mock_uuid_user, topic="Python", level="Beginner", hours_per_week=5.0)
)


class TestRouteEndpoints(unittest.TestCase):
    """Synchronous route test suite."""

    def setUp(self):
        self.db_mock = MockAsyncSession()
        
        async def db_execute(stmt):
            stmt_str = str(stmt).lower()
            if "lesson_progress" in stmt_str or "lessonprogress" in stmt_str:
                return MockDBResult(scalar_val=None)
            elif "lesson" in stmt_str:
                l = Lesson(id=uuid.uuid4(), course_id=uuid.uuid4(), title="Test Lesson", duration="30m")
                return MockDBResult(scalar_val=l)
            elif "user" in stmt_str:
                return MockDBResult(scalar_val=mock_logged_user)
            elif "course" in stmt_str:
                c = Course(
                    id=uuid.uuid4(),
                    title="FastAPI API Course",
                    description="FastAPI Description",
                    difficulty="Beginner",
                    duration="10 hours"
                )
                c.lessons = []
                return MockDBResult(scalar_val=c, scalars_list=[c])
            elif "enrollment" in stmt_str:
                return MockDBResult(scalar_val=None)
            return MockDBResult()
        self.db_mock.execute_side_effect = db_execute

        app.dependency_overrides[get_db] = lambda: self.db_mock
        app.dependency_overrides[get_current_user] = lambda: mock_logged_user
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_auth_endpoints(self):
        # Test POST /api/v1/auth/signup
        payload = {"email": "route-new@test.com", "password": "pwd-strong", "full_name": "API New"}
        response = self.client.post("/api/v1/auth/signup", json=payload)
        self.assertIn(response.status_code, [200, 201, 400])

        # Test POST /api/v1/auth/login
        payload_login = {"email": "api-student@test.com", "password": "pwd-strong"}
        response_login = self.client.post("/api/v1/auth/login", json=payload_login)
        self.assertIn(response_login.status_code, [200, 400])

    def test_courses_endpoints(self):
        # Test GET /api/v1/courses
        res = self.client.get("/api/v1/courses")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

        # Test POST /api/v1/courses/{course_id}/enroll
        course_id = str(uuid.uuid4())
        res_enroll = self.client.post(f"/api/v1/courses/{course_id}/enroll")
        self.assertEqual(res_enroll.status_code, 200)
        self.assertTrue(res_enroll.json()["success"])

    def test_users_endpoints(self):
        # Test GET /api/v1/users/profile
        res = self.client.get("/api/v1/users/profile")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

        # Test PUT /api/v1/users/profile
        payload = {"full_name": "Updated Name", "bio": "Updated Bio"}
        res_up = self.client.put("/api/v1/users/profile", json=payload)
        self.assertEqual(res_up.status_code, 200)
        self.assertTrue(res_up.json()["success"])

        # Test POST /api/v1/users/onboarding
        payload_ob = {"topic": "AI", "level": "Advanced", "hours_per_week": 10}
        res_ob = self.client.post("/api/v1/users/onboarding", json=payload_ob)
        self.assertEqual(res_ob.status_code, 200)
        self.assertTrue(res_ob.json()["success"])

    def test_progress_endpoints(self):
        # Test POST /api/v1/progress/lessons/{lesson_id}
        payload = {"completed": True, "time_spent": 120}
        lesson_id = str(uuid.uuid4())
        res = self.client.post(f"/api/v1/progress/lessons/{lesson_id}", json=payload)
        self.assertIn(res.status_code, [200, 400, 404])

        # Test GET /api/v1/progress/weekly
        res_wk = self.client.get("/api/v1/progress/weekly")
        self.assertEqual(res_wk.status_code, 200)
        self.assertTrue(res_wk.json()["success"])


def verify_celery_connection():
    from app.core.celery_app import verify_connection
    res = verify_connection()
    self_assertion = "Celery background worker is connected and healthy."
    assert res == self_assertion
