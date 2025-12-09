from openai import OpenAI
from src.config import settings
import json

client = OpenAI(api_key=settings.openai_api_key)

class AIService:
    def analyze_text(self, text: str):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Classify this email (Category, Sentiment, Summary). JSON format."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return {"error": str(e)}

    def generate_reply(self, text: str, tone: str):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"Write a {tone} reply."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content

ai_service = AIService()