from app.database import db
from app.services.openai_service import analyze_email
from datetime import datetime, timedelta
import asyncio

async def generate_daily_summaries():
    """
    Generate daily summaries for all users.
    Runs every morning.
    """
    print("⏰ Starting daily summary generation...")
    
    if db is None:
        print("❌ Database not initialized")
        return

    users = await db.users.find({"is_active": True}).to_list(length=None)
    
    for user in users:
        # Fetch emails from last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        emails = await db.emails.find({
            "user_id": str(user["_id"]),
            "received_at": {"$gte": yesterday}
        }).to_list(length=50)
        
        if not emails:
            continue
            
        # Create summary content
        email_texts = [f"Subject: {e.get('subject')}\nSnippet: {e.get('snippet')}" for e in emails]
        combined_text = "\n\n".join(email_texts)
        
        # Generate summary using AI (mocked for now to save tokens/complexity in cron)
        # In production, call analyze_email or a specific summary endpoint
        summary = f"You received {len(emails)} emails in the last 24 hours."
        
        # Send notification (Mock)
        print(f"📧 Sending daily summary to {user['email']}: {summary}")
        
    print("✅ Daily summaries completed")

async def check_follow_ups():
    """
    Check for emails that need follow-up.
    Runs hourly.
    """
    print("⏰ Checking for follow-ups...")
    
    if db is None:
        print("❌ Database not initialized")
        return
        
    # Logic: Find emails sent by user > 3 days ago with no reply
    # This requires tracking threads and replies, which is complex.
    # Simplified version: Find reminders due in the next hour
    
    now = datetime.utcnow()
    next_hour = now + timedelta(hours=1)
    
    reminders = await db.reminders.find({
        "due_date": {"$gte": now, "$lt": next_hour},
        "is_completed": False
    }).to_list(length=None)
    
    for reminder in reminders:
        # Get user
        user = await db.users.find_one({"_id": reminder["user_id"]})
        if user:
            print(f"🔔 Reminder for {user['email']}: {reminder['title']}")
            
    print("✅ Follow-up checks completed")
