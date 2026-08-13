from fastapi import APIRouter

from app.api.v1 import admin, api_keys, auth, chat, documents, feedback, folders, settings, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(folders.router, prefix="/folders", tags=["Folders"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
