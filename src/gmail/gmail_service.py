from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from src.config import settings
from src.prisma.database import get_db
from datetime import datetime, timedelta

import base64
from email.mime.text import MIMEText
import httpx
import logging

# Setup logger
logger = logging.getLogger("GmailService")

class GmailService:
    async def refresh_access_token(self, user):
        """
        Refresh the Google access token using the refresh token.
        Updates the user document with the new token.
        Returns the new access token or None if refresh fails.
        """
        refresh_token = user.get("google_refresh_token")
        if not refresh_token:
            logger.error(f"No refresh token available for user {user.get('email')}")
            return None
        
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(token_url, data=token_data)
            
            if res.status_code != 200:
                logger.error(f"Token refresh failed: {res.text}")
                return None
            
            tokens = res.json()
            new_access_token = tokens.get("access_token")
            expires_in = tokens.get("expires_in", 3600)
            token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Update user in database
            db = get_db()
            await db.users.update_one(
                {"_id": user["_id"]},
                {"$set": {
                    "google_access_token": new_access_token,
                    "token_expires_at": token_expires_at
                }}
            )
            
            logger.info(f"Successfully refreshed token for user {user.get('email')}")
            return new_access_token
            
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
    
    async def get_valid_token(self, user):
        """
        Get a valid access token, refreshing if necessary.
        Returns the token or None if unable to get a valid token.
        """
        token = user.get("google_access_token")
        token_expires_at = user.get("token_expires_at")
        
        # Check if token is expired or about to expire (within 5 minutes)
        if token_expires_at:
            if isinstance(token_expires_at, str):
                # Parse string to datetime if needed
                from dateutil import parser
                token_expires_at = parser.parse(token_expires_at)
            
            time_until_expiry = token_expires_at - datetime.utcnow()
            if time_until_expiry.total_seconds() < 300:  # Less than 5 minutes
                logger.info(f"Token expired or expiring soon for {user.get('email')}, refreshing...")
                token = await self.refresh_access_token(user)
        
        return token
    async def fetch_emails(self, user, max_results=10):
        """
        Fetch emails from Gmail API and return structured data.
        Does NOT save to DB directly; helper method for controller.
        """
        # Get valid token (will refresh if needed)
        token = await self.get_valid_token(user)
        if not token:
            logger.error(f"No valid access token for user {user.get('email')}")
            return []

        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with httpx.AsyncClient() as client:
                # 1. List Messages
                list_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults={max_results}&q=in:inbox"
                res = await client.get(list_url, headers=headers)
                
                if res.status_code != 200:
                    logger.error(f"Error fetching email list: {res.status_code} - {res.text}")
                    return []
                    
                messages_meta = res.json().get("messages", [])
                
                if not messages_meta:
                    logger.info(f"No messages found for user {user.get('email')}")
                    return []
                
                emails = []
                
                # 2. Fetch Details for each
                for msg_meta in messages_meta:
                    msg_id = msg_meta["id"]
                    detail_url = f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}"
                    detail_res = await client.get(detail_url, headers=headers)
                    
                    if detail_res.status_code == 200:
                        data = detail_res.json()
                        
                        # Extract Headers
                        payload = data.get("payload", {})
                        headers_list = payload.get("headers", [])
                        
                        subject = next((h["value"] for h in headers_list if h["name"] == "Subject"), "(No Subject)")
                        sender = next((h["value"] for h in headers_list if h["name"] == "From"), "Unknown")
                        date_str = next((h["value"] for h in headers_list if h["name"] == "Date"), "")
                        
                        # Extract Body (Simplistic snippet)
                        snippet = data.get("snippet", "")
                        
                        # Store minimal data
                        email_obj = {
                            "gmail_id": msg_id,
                            "thread_id": data.get("threadId"),
                            "subject": subject,
                            "from": sender, # Original header value
                            "from_name": sender.split("<")[0].strip().replace('"', ''),
                            "snippet": snippet,
                            "received_at": date_str, # In real app, parse this to datetime
                            "body": snippet, # Full body parsing is complex (multipart), using snippet for MVP
                            "is_read": "UNREAD" not in data.get("labelIds", [])
                        }
                        emails.append(email_obj)
                    else:
                        logger.warning(f"Failed to fetch message {msg_id}: {detail_res.status_code}")
                
                logger.info(f"Successfully fetched {len(emails)} emails for user {user.get('email')}")
                return emails
                
        except Exception as e:
            logger.error(f"Exception in fetch_emails for user {user.get('email')}: {e}")
            return []

    async def send_email(self, user, to_email, subject, body):
        """
        Send an email using Gmail API.
        """
        # Get valid token (will refresh if needed)
        token = await self.get_valid_token(user)
        if not token:
            logger.error(f"No valid access token for user {user.get('email')}")
            raise Exception("Unable to send email: No valid access token. Please re-authenticate.")

        message = MIMEText(body)
        message['to'] = to_email
        message['subject'] = subject
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {"raw": raw_message}
        
        try:
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload)
                
            if res.status_code != 200:
                logger.error(f"Gmail Send Failed: {res.status_code} - {res.text}")
                raise Exception(f"Gmail Send Failed: {res.text}")
                
            logger.info(f"Email sent successfully for user {user.get('email')}")
            return res.json()
            
        except Exception as e:
            logger.error(f"Exception in send_email: {e}")
            raise

gmail_service = GmailService()