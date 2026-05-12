import os
import csv
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from groq import Groq

from dotenv import load_dotenv

load_dotenv()
# Gmail API setup
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def send_email(service, to, subject, body):
    message = MIMEText(body)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()
    print(f"✅ Email sent to {to}")

# Groq AI setup
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("=" * 50)
print("   AI EMAIL SENDER - Fully Automatic")
print("=" * 50)

# Read leads
leads = []
with open("leads.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        leads.append(row)

print(f"\n✅ Found {len(leads)} leads!")
print("⏳ Generating and sending emails...\n")

# Connect Gmail
service = get_gmail_service()

for lead in leads:
    # Generate email with AI
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""Write a cold email to {lead['name']} who runs {lead['agency']} in {lead['city']}.
                They specialize in {lead['service']}.
                We offer an AI tool that automatically finds new clients for agencies.
                Keep it under 80 words. Friendly and professional. Just the body, no subject line."""
            }
        ],
        model="llama-3.3-70b-versatile",
    )

    body = chat_completion.choices[0].message.content
    subject = f"Quick question for {lead['agency']}"

    # Send email
    send_email(service, lead['email'], subject, body)

print("\n🎉 All emails sent successfully!")