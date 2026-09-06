# API Routers Package barrel file
from fastapi import APIRouter

from app.api.applications import router as applications_router
from app.api.auth import router as auth_router
from app.api.graph import router as graph_router
from app.api.jobs import router as jobs_router
from app.api.profile import router as profile_router
from app.api.tailor import router as tailor_router
from app.api.vault import router as vault_router
from app.api.autonomy import router as autonomy_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(profile_router, prefix="/profile", tags=["profile"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(tailor_router, prefix="/tailor", tags=["tailor"])
api_router.include_router(applications_router, prefix="/applications", tags=["applications"])
api_router.include_router(vault_router, prefix="/vault", tags=["vault"])
api_router.include_router(graph_router, prefix="/graph", tags=["graph"])
api_router.include_router(autonomy_router, prefix="/autonomy", tags=["autonomy"])
