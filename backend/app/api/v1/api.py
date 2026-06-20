"""API V1 Router definition grouping all core route operations.

This module combines authentication, profiles, courses, progress tracking, quizzes,
and rate-limited AI sub-routers under a unified '/api/v1' path namespace.
"""

from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.courses import router as courses_router
from app.api.v1.routes.progress import router as progress_router
from app.api.v1.routes.quizzes import router as quizzes_router
from app.api.v1.routes.ai import router as ai_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(courses_router)
api_router.include_router(progress_router)
api_router.include_router(quizzes_router)
api_router.include_router(ai_router)
