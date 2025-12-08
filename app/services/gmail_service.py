from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from app.config import settings
from app.models import EmailInDB
from datetime import datetime
import base64
from bs4 import BeautifulSoup

def get_gmail_credentials(user):
    """Reconstruct credentials from user tokens"""
    return Credentials(
        token=user["access_token"],
        refresh_token=user["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"]
    )

async def fetch_emails(user, db, limit=50):
    """Fetch emails from Gmail and save to DB"""
    creds = get_gmail_credentials(user)
    service = build('gmail', 'v1', credentials=creds)
    
    # List messages
    results = service.users().messages().list(userId='me', maxResults=limit).execute()
    messages = results.get('messages', [])
    
    fetched_count = 0
    
    for msg in messages:
        # Check if email already exists
        existing = await db.emails.find_one({"gmail_id": msg['id']})
        if existing:
            continue
            
        # Get full message details
        msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()
        
        payload = msg_detail.get('payload', {})
        headers = payload.get('headers', [])
        
        # Extract headers
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(No Subject)')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
        # Parse date (simplified)
        try:
            date = datetime.strptime(date_str.split(' +')[0].split(' -')[0], '%a, %d %b %Y %H:%M:%S')
        except:
            date = datetime.utcnow()
            
        # Extract body
        body = ""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode()
                        break
        elif 'body' in payload:
            data = payload['body'].get('data')
            if data:
                body = base64.urlsafe_b64decode(data).decode()
                
        # Create email object
        email_data = {
            "gmail_id": msg['id'],
            "thread_id": msg['threadId'],
            "sender": sender,
            "sender_email": sender, # Simplified extraction
            "recipients": [], # TODO: Extract recipients
            "subject": subject,
            "body": body,
            "snippet": msg_detail.get('snippet'),
            "date": date,
            "received_at": datetime.utcnow(),
            "is_read": 'UNREAD' not in msg_detail.get('labelIds', []),
            "labels": msg_detail.get('labelIds', [])
        }
        
        await db.emails.insert_one(email_data)
        fetched_count += 1
        
    return fetched_count
