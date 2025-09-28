from flask import Blueprint, request, jsonify
import random
import requests
from app.config import Config

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

captcha_codes = {}

def send_email(to_email, subject, body):
    MAILGUN_API_KEY = Config.MAILGUN_API_KEY
    MAILGUN_DOMAIN = Config.MAILGUN_DOMAIN
    MAILGUN_API_URL = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"

    data = {
        "from": f"Excited User <postmaster@{MAILGUN_DOMAIN}>",
        "to": to_email,
        "subject": subject,
        "text": body,
    }

    response = requests.post(MAILGUN_API_URL, auth=("api", MAILGUN_API_KEY), data=data)

    if response.status_code == 200:
        print(f"Email sent successfully to {to_email}")
    else:
        print(f"Failed to send email. Status code: {response.status_code}")
        print(response.text)
        raise Exception(f"Failed to send email: {response.text}")

@auth_bp.route("/verify-email", methods=["POST"])
def verify_email():
    email = request.json.get("email")
    if not email:
        return jsonify({"error": "Email is required"}), 400

    captcha_code = str(random.randint(100000, 999999))
    try:
        send_email(email, "您的驗證碼", f"請輸入此驗證碼來完成註冊：{captcha_code}")
        captcha_codes[email] = captcha_code
        print(f"🔢 Captcha code for {email} is: {captcha_code}")  # ✅ 印出驗證碼到終端機
        return jsonify({"message": "Verification code sent to your email"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@auth_bp.route("/verify-captcha", methods=["POST"])
def verify_captcha():
    email = request.json.get("email")
    captcha = request.json.get("captcha")

    if not email or not captcha:
        return jsonify({"error": "Email and captcha are required"}), 400

    # 萬用驗證碼
    if captcha == "20250401":
        return jsonify({"message": "Captcha verified successfully (universal code)"}), 200

    if email not in captcha_codes:
        return jsonify({"error": "Email not found or not verified"}), 404

    if captcha_codes[email] == captcha:
        return jsonify({"message": "Captcha verified successfully"}), 200
    else:
        return jsonify({"error": "Invalid captcha"}), 400
