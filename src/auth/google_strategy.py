import httpx
from src.config import settings
from fastapi import HTTPException

class GoogleStrategy:
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO = "https://www.googleapis.com/oauth2/v1/userinfo"

    async def exchange_code_for_token(self, code: str):
        """Exchanges the auth code for an access token"""
        async with httpx.AsyncClient() as client:
            data = {
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": "http://localhost:8000/api/v1/auth/google/callback",
                "grant_type": "authorization_code",
            }
            response = await client.post(self.GOOGLE_TOKEN_URL, data=data)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid Google Code")
            return response.json()

    async def get_user_info(self, access_token: str):
        """Fetches user profile using access token"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.GOOGLE_USER_INFO,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch user info")
            return response.json()

google_strategy = GoogleStrategy()