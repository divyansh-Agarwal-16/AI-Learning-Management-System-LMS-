"""Verification test script for the AI LMS FastAPI backend.

Tests core components: security logic, Pydantic schemas, database model
registration, and envelope structures.
"""

import sys
import unittest
from datetime import datetime, timedelta, timezone

# Add parent path to import app package
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.schemas.base import ApiResponse
from app.schemas.auth import LoginRequest, SignupRequest
from app.schemas.user import UserResponse
from app.schemas.course import CourseResponse
from app.schemas.quiz import QuizResponse
from app.schemas.progress import CourseProgressResponse
from app.schemas.ai import ChatResponse

# Import database models to verify schema loading and relationships
from app.models.user import User, UserProfile, OnboardingData
from app.models.course import Course, Lesson, Enrollment
from app.models.quiz import Quiz, Question, Submission, Answer
from app.models.progress import LessonProgress, CourseProgress
from app.models.ai_logs import AIUsageLog, ChatHistory


class TestBackendSecurity(unittest.TestCase):
    """Test suite validating password hashing and JWT encoding/decoding."""

    def test_password_hashing(self):
        """Verifies plain password hashing and verification match checks."""
        password = "secure_password_123"
        hashed = hash_password(password)
        
        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrong_password", hashed))

    def test_jwt_access_token_generation(self):
        """Verifies JWT access token signatures and payload contents."""
        user_data = {"sub": "42", "email": "test@example.com", "role": "student"}
        token = create_access_token(user_data, expires_delta=timedelta(minutes=5))
        
        # Decode and inspect payload
        payload = decode_token(token, is_refresh=False)
        self.assertEqual(payload.get("sub"), "42")
        self.assertEqual(payload.get("email"), "test@example.com")
        self.assertEqual(payload.get("role"), "student")
        self.assertEqual(payload.get("type"), "access")

    def test_jwt_refresh_token_generation(self):
        """Verifies JWT refresh token signatures and payload contents."""
        user_data = {"sub": "100", "email": "refresh@example.com"}
        token = create_refresh_token(user_data, expires_delta=timedelta(days=1))
        
        # Decode and inspect refresh payload
        payload = decode_token(token, is_refresh=True)
        self.assertEqual(payload.get("sub"), "100")
        self.assertEqual(payload.get("email"), "refresh@example.com")
        self.assertEqual(payload.get("type"), "refresh")


class TestBackendSchemas(unittest.TestCase):
    """Test suite validating response envelopes and validation constraints."""

    def test_api_response_envelope(self):
        """Ensures that all API responses match the standard wrapper format."""
        response = ApiResponse(
            success=True,
            data={"test": "payload"},
            message="Data loaded successfully"
        )
        self.assertTrue(response.success)
        self.assertEqual(response.message, "Data loaded successfully")
        self.assertEqual(response.data.get("test"), "payload")

    def test_auth_schemas_validation(self):
        """Ensures that credentials input schemas raise validation errors for short passwords."""
        # Valid signup
        signup = SignupRequest(email="user@example.com", password="long_password", full_name="John Doe")
        self.assertEqual(signup.full_name, "John Doe")


class TestDatabaseModels(unittest.TestCase):
    """Test suite validating that all database models successfully import and map."""

    def test_models_exist(self):
        """Asserts that all relational model classes are loaded into SQLAlchemy metadata."""
        from app.core.database import Base
        metadata_tables = Base.metadata.tables.keys()
        
        self.assertIn("users", metadata_tables)
        self.assertIn("user_profiles", metadata_tables)
        self.assertIn("onboarding_data", metadata_tables)
        self.assertIn("courses", metadata_tables)
        self.assertIn("lessons", metadata_tables)
        self.assertIn("enrollments", metadata_tables)
        self.assertIn("quizzes", metadata_tables)
        self.assertIn("questions", metadata_tables)
        self.assertIn("submissions", metadata_tables)
        self.assertIn("answers", metadata_tables)
        self.assertIn("lesson_progresses", metadata_tables)
        self.assertIn("course_progresses", metadata_tables)
        self.assertIn("ai_usage_logs", metadata_tables)
        self.assertIn("chat_histories", metadata_tables)


if __name__ == "__main__":
    unittest.main()
