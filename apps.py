from flask import Flask, render_template, request, redirect, url_for
import csv
import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send():
    file = request.files['csv_file']
    leads = []
    content = file.read().decode('utf-8').splitlines()
    reader = csv.DictReader(content)
    for row in reader:
        leads.append(row)

    service = get_gmail_service()
    results = []

    for lead in leads:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"""Write a cold email to {lead['name']} who runs {lead['agency']} in {lead['city']}.
                    They specialize in {lead['service']}.
                    We offer an AI tool that automatically finds new clients for agencies.
                    Keep it under 80 words. Friendly and professional. Just the body."""
                }
            ],
            model="llama-3.3-70b-versatile",
        )

        body = chat_completion.choices[0].message.content
        subject = f"Quick question for {lead['agency']}"
        send_email(service, lead['email'], subject, body)
        results.append({"name": lead['name'], "agency": lead['agency'], "status": "Sent ✅"})

    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)