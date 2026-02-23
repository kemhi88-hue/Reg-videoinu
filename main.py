import re
import time
import requests
import random
import string
from playwright.sync_api import sync_playwright

# Thử import stealth an toàn
try:
    import playwright_stealth
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False

API_URL = "https://api.mail.tm"

def get_mail_tm():
    try:
        domains = requests.get(f"{API_URL}/domains").json()['hydra:member']
        domain = domains[0]['domain']
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        address = f"{username}@{domain}"
        password = "SecurePass123!"
        requests.post(f"{API_URL}/accounts", json={"address": address, "password": password})
        token_resp = requests.post(f"{API_URL}/token", json={"address": address, "password": password}).json()
        return address, token_resp['token']
    except Exception as e:
        print(f"Lỗi tạo mail: {e}")
        return None, None

def wait_for_otp(token):
    headers = {"Authorization": f"Bearer {token}"}
    print("--- Đang quét hộp thư Videoinu chờ mã (120s) ---")
    for _ in range(24):
        time.sleep(5)
        try:
            resp = requests.get(f"{API_URL}/messages", headers=headers).json()
            messages = resp.get('hydra:member', [])
            if messages:
                msg_id = messages[0]['id']
                msg_data = requests.get(f"{API_URL}/messages/{msg_id}", headers=headers).json()
                content = msg_data.get('text', '') or msg_data.get('intro', '')
                # Tìm mã số (Videoinu thường gửi mã 4-6 số)
                otp_match = re.search(r'\b\d{4,6}\b', content)
                if otp_match:
                    return otp_match.group(0)
        except:
            continue
    return None

def run_automation():
    email, token = get_mail_tm()
    if not email: return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        if HAS_STEALTH:
            try:
                # Cố gắng gọi hàm stealth bất kể phiên bản nào
                for method in ['stealth_sync', 'stealth_page']:
                    if hasattr(playwright_stealth, method):
                        getattr(playwright_stealth, method)(page)
                        print(f"Đã kích hoạt {method}")
                        break
            except: pass

        try:
            print(f"Truy cập https://videoinu.com/register với: {email}")
            page.goto("https://videoinu.com/register", wait_until="networkidle")
            
            # Điền Email vào form của Videoinu
            # Lưu ý: Videoinu có thể dùng selector name="email" hoặc type="email"
            page.wait_for_selector('input[name="email"], input[type="email"]', timeout=30000)
            page.fill('input[name="email"], input[type="email"]', email)
            
            # Tạo mật khẩu ngẫu nhiên
            random_pw = "InuPass" + ''.join(random.choices(string.digits, k=5))
            if page.query_selector('input[type="password"]'):
                page.fill('input[type="password"]', random_pw)
            
            # Nhấn nút gửi mã hoặc đăng ký
            # Tìm nút bấm có chứa chữ 'Send', 'Register' hoặc 'Sign up'
            submit_btn = page.query_selector('button:has-text("Send"), button:has-text("Sign up"), button[type="submit"]')
            if submit_btn:
                submit_btn.click()
            
            print("Đã gửi yêu cầu. Đang đợi mã xác nhận...")
            otp_code = wait_for_otp(token)
            
            if otp_code:
                print(f"==> MÃ XÁC NHẬN VIDEOINU: {otp_code}")
                with open("accounts_videoinu.txt", "a") as f:
                    f.write(f"Email: {email} | Pass: {random_pw} | OTP: {otp_code}\n")
                page.screenshot(path="videoinu_success.png")
            else:
                print("Lỗi: Không lấy được mã từ Videoinu.")
                page.screenshot(path="videoinu_error.png")

        except Exception as e:
            print(f"Lỗi: {e}")
            page.screenshot(path="videoinu_crash.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_automation()
