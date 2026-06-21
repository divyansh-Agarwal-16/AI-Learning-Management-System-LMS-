import sys
from pathlib import Path
from fastapi import APIRouter

from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.users import router as users_router
from app.api.v1.routes.courses import router as courses_router
from app.api.v1.routes.progress import router as progress_router
from app.api.v1.routes.quizzes import router as quizzes_router

# Configure sys.path to resolve agents import if launched from backend directory
root_path = Path(__file__).parent.parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path))

from agents.api import router as ai_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(courses_router)
api_router.include_router(progress_router)
api_router.include_router(quizzes_router)
api_router.include_router(ai_router)
