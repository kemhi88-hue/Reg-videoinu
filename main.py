import re
import time
import requests
import random
import string
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

# --- Cấu hình Mail.tm API ---
API_URL = "https://api.mail.tm"

def get_mail_tm():
    # 1. Lấy danh sách domain
    domains = requests.get(f"{API_URL}/domains").json()['hydra:member']
    domain = domains[0]['domain']
    
    # 2. Tạo username và password ngẫu nhiên
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    address = f"{username}@{domain}"
    password = "Password123!"
    
    # 3. Tạo tài khoản
    payload = {"address": address, "password": password}
    requests.post(f"{API_URL}/accounts", json=payload)
    
    # 4. Lấy Token để truy cập mail
    token_resp = requests.post(f"{API_URL}/token", json=payload).json()
    token = token_resp['token']
    
    return address, token

def wait_for_otp(token):
    headers = {"Authorization": f"Bearer {token}"}
    print("--- Đang chờ mã OTP từ InVideo ---")
    
    for _ in range(20): # Đợi trong khoảng 100 giây
        time.sleep(5)
        # Lấy danh sách tin nhắn
        msgs = requests.get(f"{API_URL}/messages", headers=headers).json()['hydra:member']
        
        if msgs:
            msg_id = msgs[0]['id']
            # Đọc nội dung tin nhắn mới nhất
            msg_data = requests.get(f"{API_URL}/messages/{msg_id}", headers=headers).json()
            content = msg_data['text'] # Hoặc 'html'
            
            # Tìm mã 6 số
            match = re.search(r'\b\d{6}\b', content)
            if match:
                return match.group(0)
    return None

def run_reg():
    email, token = get_mail_tm()
    
    with sync_playwright() as p:
        # Khởi tạo trình duyệt ẩn
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page) # Che dấu vết bot

        print(f"Đang sử dụng email: {email}")
        
        # Truy cập trang đăng ký của InVideo AI
        page.goto("https://ai.invideo.io/signup")

        try:
            # Nhập email vào ô input
            page.wait_for_selector('input[type="email"]')
            page.fill('input[type="email"]', email)
            page.keyboard.press("Enter")
            
            print("Đã nhấn đăng ký, đang kiểm tra hòm thư...")
            otp = wait_for_otp(token)
            
            if otp:
                print(f"MÃ OTP CỦA BẠN LÀ: {otp}")
                # Ở đây bạn có thể viết thêm code để tự điền otp vào page
                # page.fill('input[name="otp"]', otp)
            else:
                print("Hết thời gian chờ mà không thấy mã.")
        except Exception as e:
            print(f"Lỗi: {e}")
            page.screenshot(path="error_log.png")
            
        browser.close()

if __name__ == "__main__":
    run_reg()
