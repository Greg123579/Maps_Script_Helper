"""
Copy this file to secrets.py and paste your API keys.
  cp secrets.example.py secrets.py
secrets.py is gitignored and never committed.
"""
GOOGLE_API_KEY = ""  # e.g. AIza...
OPENAI_API_KEY = ""  # e.g. sk-...
ADMIN_PASSWORD = ""  # for /admin.html (Reset User Data, Deploy Fresh)

# Password reset email (SMTP)
# Leave empty to disable; users will see "Email not configured" when requesting reset.
SMTP_HOST = ""       # e.g. smtp.gmail.com, smtp.sendgrid.net
SMTP_PORT = 587
SMTP_USER = ""
SMTP_PASSWORD = ""   # App password for Gmail; API key for SendGrid
SMTP_FROM = ""       # e.g. noreply@yourdomain.com
APP_BASE_URL = ""    # e.g. https://maps.yourdomain.com (for reset link in email)
