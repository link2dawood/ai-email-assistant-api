from openai import AsyncOpenAI
from src.config import settings
import json
import logging

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=settings.openai_api_key)

class AIService:
    async def analyze_text(self, text: str):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Classify this email (Category, Sentiment, Summary). JSON format."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI Analysis Error: {e}")
            return {"error": str(e)}

    async def generate_reply(self, text: str, tone: str):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": f"Write a {tone} reply."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI Generation Error: {e}")
            raise e # Let the controller handle it or return a safe error

ai_service = AIService()