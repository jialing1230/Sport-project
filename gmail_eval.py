# gmail_eval.py
import base64
import json
import os
from pathlib import Path
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# 環境變數（Base64 / 路徑 都支援）
CLIENT_SECRET_B64 = os.getenv("GMAIL_CLIENT_SECRET_B64")
TOKEN_B64 = os.getenv("GMAIL_TOKEN_B64")
HEADLESS = os.getenv("GMAIL_HEADLESS", "false").lower() in ("1", "true", "yes")

# 可選：把更新後的 token 寫回這個路徑（建議掛一個可寫資料夾）
PERSIST_TOKEN_PATH = os.getenv("GMAIL_PERSIST_TOKEN_PATH")

# 備援：如果你仍想用檔案路徑，也支援（非必填）
CLIENT_SECRET_PATH = os.getenv("GMAIL_CLIENT_SECRET_PATH", "client_secret.json")
TOKEN_PATH = os.getenv("GMAIL_TOKEN_PATH", "token.json")


def _decode_b64_json(value: str):
    if not value:
        return None
    try:
        txt = base64.b64decode(value).decode("utf-8")
        return json.loads(txt)
    except Exception:
        return None


def _ensure_parent(path_str: str):
    if not path_str:
        return
    Path(path_str).parent.mkdir(parents=True, exist_ok=True)


def _write_token_if_needed(creds: Credentials):
    """把最新憑證寫回檔案（若指定了 PERSIST_TOKEN_PATH 或 TOKEN_PATH）"""
    path = PERSIST_TOKEN_PATH or TOKEN_PATH
    if not path:
        return
    _ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(creds.to_json())


def _load_service():
    creds = None

    # 1) 先試著從環境變數的 Base64 token 載入
    token_info = _decode_b64_json(TOKEN_B64)
    if token_info:
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)

    # 2) 再用檔案 token.json（若存在）
    if (not creds) and os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    # 3) 若無或無效 → 嘗試 refresh / 重新授權
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            # 有 refresh_token 就刷新
            creds.refresh(Request())
            _write_token_if_needed(creds)
        else:
            # 需要初次授權：先從 Base64 讀 client_secret，沒有再用檔案
            client_config = _decode_b64_json(CLIENT_SECRET_B64)
            if client_config:
                flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)

            if HEADLESS:
                # 沒瀏覽器的環境（容器/伺服器），走 console flow
                creds = flow.run_console()
            else:
                # 本機開瀏覽器
                creds = flow.run_local_server(port=0)

            _write_token_if_needed(creds)

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
