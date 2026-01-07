from fastapi import APIRouter
from src.auth.auth_controller import router as auth_router
from src.email.email_controller import router as email_router
from src.email.email_actions_controller import router as email_actions_router
from src.gmail.gmail_controller import router as gmail_router
from src.ai.ai_controller import router as ai_router
from src.reminders.reminders_controller import router as reminders_router
from src.billing.billing_controller import router as billing_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
api_router.include_router(email_router, prefix="/emails", tags=["Emails"])
api_router.include_router(email_actions_router, prefix="/emails", tags=["Email Actions"])
api_router.include_router(gmail_router, prefix="/gmail", tags=["Gmail"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI"])
api_router.include_router(reminders_router, prefix="/reminders", tags=["Reminders"])
api_router.include_router(billing_router, prefix="/billing", tags=["Billing"])