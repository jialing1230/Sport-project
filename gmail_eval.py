# gmail_eval.py
import base64
import os
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

def _load_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def send_eval_mail(to_email, activity_title, eval_link):
    service = _load_service()
    subject = f"請評價活動：「{activity_title}」"
    html = f"""
    <h2>感謝參加「{activity_title}」</h2>
    <p>活動已結束，邀請你留下評價：</p>
    <p><a href="{eval_link}" target="_blank">👉 點這裡評價</a></p>
    """

    msg = MIMEText(html, "html", "utf-8")
    msg["To"] = to_email
    msg["Subject"] = subject
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()

    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    print(f"✅ 已寄給 {to_email}")
