from fastapi import APIRouter, Depends
from src.auth.auth_service import auth_service
from src.billing.stripe_service import stripe_service

router = APIRouter()

@router.post("/checkout")
async def create_checkout(price_id: str, user = Depends(auth_service.get_current_user)):
    url = stripe_service.create_checkout_session(user["email"], price_id)
    return {"url": url}