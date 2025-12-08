from openai import OpenAI
from app.config import settings
import json
from typing import Dict, Any

client = OpenAI(api_key=settings.openai_api_key)

def analyze_email(email_content: str) -> Dict[str, Any]:
    """
    Analyze email content using OpenAI to determine category, importance, summary, and sentiment.
    """
    prompt = f"""
    Analyze the following email and provide a JSON response with these fields:
    - category: One of [Important, Client, Lead, Payment, Low Priority, Spam]
    - importance: Integer 0-100
    - summary: Brief 1-sentence summary
    - sentiment: One of [Positive, Neutral, Negative]

    Email Content:
    {email_content[:2000]}  # Truncate to avoid token limits
    """

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are an AI email assistant. Respond only in valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"Error analyzing email: {e}")
        return {
            "category": "Uncategorized",
            "importance": 0,
            "summary": "Could not analyze email",
            "sentiment": "Neutral"
        }

def generate_reply(email_content: str, tone: str = "professional") -> str:
    """
    Generate a reply to the email with the specified tone.
    """
    prompt = f"""
    Draft a {tone} reply to the following email. 
    Keep it concise and relevant.

    Email Content:
    {email_content[:2000]}
    """

    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are a helpful email assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error generating reply: {str(e)}"
