import re
import time
import os
import hashlib
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

load_dotenv()

# Cấu hình API Temp-Mail (Sử dụng RapidAPI)
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
API_HOST = "privatix-temp-mail-v1.p.rapidapi.com"

def get_email_hash(email):
    return hashlib.md5(email.encode()).hexdigest()

def fetch_otp(email_hash):
    url = f"https://{API_HOST}/request/mail/id/{email_hash}/"
    headers = {"X-RapidAPI-Key": RAPID_API_KEY, "X-RapidAPI-Host": API_HOST}
    
    print("... Đang kiểm tra hòm thư ...")
    for _ in range(15):  # Thử lại trong 75 giây
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                content = data[0].get('mail_text', '') or data[0].get('mail_html', '')
                match = re.search(r'\b\d{6}\b', content)
                if match:
                    return match.group(0)
        time.sleep(5)
    return None

def register():
    # Lấy email ngẫu nhiên từ API
    headers = {"X-RapidAPI-Key": RAPID_API_KEY, "X-RapidAPI-Host": API_HOST}
    email_resp = requests.get(f"https://{API_HOST}/request/domains/", headers=headers)
    email = f"user_{int(time.time())}{email_resp.json()[0]}"
    e_hash = get_email_hash(email)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Chạy ẩn
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        stealth_sync(page) # Chế độ ẩn danh bot

        print(f"Bắt đầu đăng ký với: {email}")
        page.goto("https://ai.invideo.io/signup") # Link gốc hoặc link videoinu

        # Logic điền form (Tùy biến theo Selector của web)
        page.fill('input[type="email"]', email)
        page.click('button[type="submit"]') 
        
        print("Đang đợi mã OTP từ Temp-Mail...")
        otp = fetch_otp(e_hash)

        if otp:
            print(f"Tìm thấy mã OTP: {otp}")
            # Điền mã OTP vào ô nhập (VD: các ô input code)
            # page.fill('input#otp-input', otp)
            # page.click('button#verify')
            print("Đăng ký hoàn tất!")
        else:
            print("Không nhận được mã OTP. Thử lại sau.")
        
        browser.close()

if __name__ == "__main__":
    if not RAPID_API_KEY:
        print("Vui lòng cấu hình RAPID_API_KEY trong file .env")
    else:
        register()
