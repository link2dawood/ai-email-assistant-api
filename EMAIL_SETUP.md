# Email Configuration Setup Guide

## Gmail SMTP Configuration

To enable actual email sending for password reset functionality, you need to configure Gmail SMTP settings.

### Step 1: Enable 2-Factor Authentication

1. Go to your Google Account settings: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification**
3. Follow the prompts to enable 2FA if not already enabled

### Step 2: Generate App Password

1. Go to **Security** → **2-Step Verification** → **App passwords**
   - Or visit directly: https://myaccount.google.com/apppasswords
2. Select **Mail** as the app
3. Select **Other (Custom name)** as the device
4. Enter "AI Email Assistant" as the name
5. Click **Generate**
6. **Copy the 16-character password** (you won't be able to see it again)

### Step 3: Update .env File

Add the following to your `backend/.env` file:

```env
# Email Configuration
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_FROM_NAME=AI Email Assistant
```

**Replace**:
- `your-email@gmail.com` with your actual Gmail address
- `your-16-char-app-password` with the app password from Step 2

### Step 4: Restart Backend Server

After updating the `.env` file, restart your backend server for changes to take effect:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
cd backend
.\.venv\Scripts\uvicorn src.main:app --reload
```

## Testing

### With SMTP Configured

1. Navigate to `http://localhost:3000/auth/forgot-password`
2. Enter your Gmail address
3. Click "Send Reset Link"
4. Check your Gmail inbox for the password reset email
5. Click the link in the email to reset your password

### Without SMTP Configured (Fallback)

If SMTP credentials are not configured, the system will:
- Log the reset link to the backend console
- Continue to work normally
- Not throw any errors

You can still test the password reset flow by copying the link from the backend logs.

## Troubleshooting

### "Failed to send email" Error

**Possible causes**:
1. **Incorrect credentials**: Double-check your email and app password
2. **2FA not enabled**: Gmail requires 2FA to use app passwords
3. **Less secure app access**: Make sure you're using an app password, not your regular password
4. **Firewall blocking SMTP**: Port 587 must be open

### Email Not Received

1. Check your spam/junk folder
2. Verify the email address is correct
3. Check backend logs for any error messages
4. Ensure SMTP credentials are properly set in `.env`

## Security Notes

- **Never commit** your `.env` file to version control
- The `.env` file is already in `.gitignore`
- App passwords are safer than using your main password
- Reset links expire after 30 minutes
- Each reset token can only be used once
