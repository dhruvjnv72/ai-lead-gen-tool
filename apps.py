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
# Validate file uploaded
    if 'csv_file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['csv_file']
    
    if file.filename == '':
        return "No file selected", 400
    
    if not file.filename.endswith('.csv'):
        return "Please upload a CSV file only", 400
    
    leads = []
    content = file.read().decode('utf-8').splitlines()
    reader = csv.DictReader(content)
    
    # Validate required columns
    required_columns = {'name', 'agency', 'email', 'city', 'service'}
    if not required_columns.issubset(set(reader.fieldnames or [])):
        return f"CSV must have these columns: name, agency, email, city, service", 400
    
    for row in reader:
        leads.append(row)
    
    if len(leads) == 0:
        return "CSV file is empty", 400

    service = get_gmail_service()
    results = []

    for lead in leads:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"""You are an expert cold email writer for a lead generation agency.

                    Choose ONE of these 3 templates and fill in the details for this lead:
                    - Name: {lead['name']}
                    - Agency: {lead['agency']}
                    - City: {lead['city']}
                    - Service: {lead['service']}

                    TEMPLATE 1 - Problem/Solution:
                    Open with the biggest pain point agencies in {lead['city']} face finding clients.
                    Introduce our AI tool as the solution.
                    Give a specific result (50+ leads found automatically per week).
                    End with: "Worth a 15-minute call this week?"

                    TEMPLATE 2 - Compliment/Hook:
                    Open with a genuine compliment about {lead['service']} agencies in {lead['city']}.
                    Mention that great agencies lose time on outreach instead of doing actual work.
                    Explain how our tool handles all outreach automatically.
                    End with: "Can I show you how it works?"

                    TEMPLATE 3 - Direct/Bold:
                    Open with a bold statement: most agencies waste 20 hours/week on outreach.
                    State our tool cuts that to zero.
                    List 3 specific things it does automatically.
                    End with: "Open to seeing a quick demo?"

                    Rules:
                    - 150-200 words
                    - Friendly and conversational, not salesy
                    - Use their actual name, agency and city naturally
                    - No subject line, just the body
                    - Pick the template that fits best for {lead['service']} agencies"""
                }
            ],
            model="llama-3.3-70b-versatile",
        )

        body = chat_completion.choices[0].message.content
        subject = f"Quick idea for {lead['agency']} - worth 2 mins?"
        send_email(service, lead['email'], subject, body)
        results.append({"name": lead['name'], "agency": lead['agency'], "status": "Sent ✅"})

    return render_template('results.html', results=results)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))