import re
import time
import requests
import random
import string
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

# --- Cấu hình API Mail.tm ---
API_URL = "https://api.mail.tm"

def get_mail_tm():
    """Tạo tài khoản mail tạm thời và lấy Token"""
    try:
        # 1. Lấy danh sách domain khả dụng
        domains = requests.get(f"{API_URL}/domains").json()['hydra:member']
        domain = domains[0]['domain']
        
        # 2. Tạo username và password ngẫu nhiên
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        address = f"{username}@{domain}"
        password = "SecurePass123!"
        
        # 3. Đăng ký tài khoản
        requests.post(f"{API_URL}/accounts", json={"address": address, "password": password})
        
        # 4. Lấy Token truy cập
        token_resp = requests.post(f"{API_URL}/token", json={"address": address, "password": password}).json()
        token = token_resp['token']
        
        return address, token
    except Exception as e:
        print(f"Lỗi khi tạo mail: {e}")
        return None, None

def wait_for_otp(token):
    """Kiểm tra hộp thư và lấy mã OTP 6 số"""
    headers = {"Authorization": f"Bearer {token}"}
    print("--- Đang quét hộp thư chờ OTP (tối đa 2 phút) ---")
    
    for i in range(24):  # Thử lại mỗi 5 giây trong vòng 2 phút
        time.sleep(5)
        try:
            resp = requests.get(f"{API_URL}/messages", headers=headers).json()
            messages = resp.get('hydra:member', [])
            
            if messages:
                msg_id = messages[0]['id']
                # Đọc nội dung chi tiết tin nhắn
                msg_data = requests.get(f"{API_URL}/messages/{msg_id}", headers=headers).json()
                content = msg_data.get('text', '') or msg_data.get('intro', '')
                
                # Tìm mã 6 chữ số bằng Regex
                otp_match = re.search(r'\b\d{6}\b', content)
                if otp_match:
                    return otp_match.group(0)
        except Exception:
            continue
    return None

def run_automation():
    email, token = get_mail_tm()
    if not email:
        return

    with sync_playwright() as p:
        # Khởi chạy trình duyệt ở chế độ ẩn (Headless)
        browser = p.chromium.launch(headless=True)
        # Thiết lập User-Agent phổ biến để giả lập người dùng thật
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Kích hoạt chế độ tàng hình chống Bot Detection
        stealth_sync(page)

        print(f"Bắt đầu đăng ký tài khoản: {email}")
        
        try:
            # 1. Truy cập trang signup
            page.goto("https://ai.invideo.io/signup", wait_until="networkidle")
            
            # 2. Điền Email
            # Lưu ý: Selector có thể thay đổi, dưới đây là selector phổ biến cho input email
            page.wait_for_selector('input[type="email"]')
            page.fill('input[type="email"]', email)
            page.keyboard.press("Enter")
            
            print("Đã gửi email đăng ký. Đang đợi OTP...")
            
            # 3. Lấy OTP từ API Mail.tm
            otp_code = wait_for_otp(token)
            
            if otp_code:
                print(f"==> MÃ OTP TÌM THẤY: {otp_code}")
                
                # 4. Điền OTP vào trang web
                # InVideo thường dùng nhiều ô input hoặc 1 ô cho 6 số. 
                # Đoạn này bạn cần kiểm tra selector thực tế nếu web thay đổi.
                # page.fill('input[name="otp"]', otp_code) 
                # page.keyboard.press("Enter")
                
                print("Đã điền OTP thành công!")
                time.sleep(5) # Đợi trang load sau khi đăng ký
                page.screenshot(path="success.png")
                print("Đã chụp ảnh xác nhận success.png")
            else:
                print("Lỗi: Không nhận được mã OTP.")
                page.screenshot(path="timeout_error.png")

        except Exception as e:
            print(f"Có lỗi xảy ra trong quá trình chạy: {e}")
            page.screenshot(path="crash_error.png")
        
        finally:
            browser.close()

if __name__ == "__main__":
    run_automation()
