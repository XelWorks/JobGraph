# API Routers Package barrel file
from app.api.auth import router as auth_router
from app.api.profile import router as profile_router
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(profile_router, prefix="/profile", tags=["profile"])
