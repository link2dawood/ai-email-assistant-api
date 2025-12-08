from fastapi import APIRouter
router = APIRouter()

@router.post("/create-session")
async def create_session():
    return {"message": "Billing endpoint"}