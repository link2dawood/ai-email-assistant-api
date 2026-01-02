"""
Email Service Module
Handles sending emails via SMTP (Gmail)
"""

import logging
from typing import Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP"""

    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_user = settings.smtp_user
        self.smtp_password = settings.smtp_password
        self.email_from = settings.email_from
        self.email_from_name = settings.email_from_name

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            plain_content: Plain text fallback (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        # Check if SMTP is configured
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Falling back to console logging.")
            self._log_email_to_console(to_email, subject, html_content)
            return False

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.email_from_name} <{self.email_from}>"
            message["To"] = to_email

            # Add plain text version if provided
            if plain_content:
                part1 = MIMEText(plain_content, "plain")
                message.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_content, "html")
            message.attach(part2)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.smtp_server,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            # Fallback to console logging
            self._log_email_to_console(to_email, subject, html_content)
            return False

    def _log_email_to_console(self, to_email: str, subject: str, content: str):
        """Log email details to console when SMTP is not available"""
        logger.info("=" * 50)
        logger.info("EMAIL (Console Fallback)")
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Content: {content}")
        logger.info("=" * 50)

    async def send_password_reset_email(self, to_email: str, reset_link: str) -> bool:
        """
        Send password reset email with branded template
        
        Args:
            to_email: Recipient email address
            reset_link: Password reset link
            
        Returns:
            bool: True if email sent successfully
        """
        subject = "Reset Your Password - AI Email Assistant"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .container {{
                    background-color: #ffffff;
                    border-radius: 8px;
                    padding: 40px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .header h1 {{
                    color: #7c3aed;
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    margin-bottom: 30px;
                }}
                .button {{
                    display: inline-block;
                    padding: 14px 28px;
                    background-color: #7c3aed;
                    color: #ffffff !important;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .button:hover {{
                    background-color: #6d28d9;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    font-size: 12px;
                    color: #6b7280;
                    text-align: center;
                }}
                .warning {{
                    background-color: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 12px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 AI Email Assistant</h1>
                </div>
                
                <div class="content">
                    <h2>Reset Your Password</h2>
                    <p>Hello,</p>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    
                    <div style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #7c3aed;">{reset_link}</p>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong> This link will expire in 30 minutes. If you didn't request this password reset, please ignore this email.
                    </div>
                </div>
                
                <div class="footer">
                    <p>This is an automated email from AI Email Assistant. Please do not reply to this email.</p>
                    <p>&copy; 2026 AI Email Assistant. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_content = f"""
        Reset Your Password - AI Email Assistant
        
        Hello,
        
        We received a request to reset your password. Click the link below to create a new password:
        
        {reset_link}
        
        This link will expire in 30 minutes.
        
        If you didn't request this password reset, please ignore this email.
        
        ---
        AI Email Assistant
        """
        
        return await self.send_email(to_email, subject, html_content, plain_content)


# Create global email service instance
email_service = EmailService()
