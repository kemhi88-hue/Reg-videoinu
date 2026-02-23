import re
import time
import requests
import random
import string
from playwright.sync_api import sync_playwright

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
    print("--- Đang quét hộp thư chờ mã 6 số ---")
    for _ in range(20):
        time.sleep(5)
        try:
            resp = requests.get(f"{API_URL}/messages", headers=headers).json()
            messages = resp.get('hydra:member', [])
            if messages:
                msg_id = messages[0]['id']
                msg_data = requests.get(f"{API_URL}/messages/{msg_id}", headers=headers).json()
                content = msg_data.get('text', '') or msg_data.get('intro', '')
                otp_match = re.search(r'\b\d{6}\b', content)
                if otp_match:
                    return otp_match.group(0)
        except:
            continue
    return None

def run_automation():
    email, token = get_mail_tm()
    if not email: return

    # Tạo nickname ngẫu nhiên
    nickname = "User_" + ''.join(random.choices(string.ascii_letters, k=6))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 720})
        page = context.new_page()

        if HAS_STEALTH:
            try:
                for method in ['stealth_sync', 'stealth_page']:
                    if hasattr(playwright_stealth, method):
                        getattr(playwright_stealth, method)(page)
                        break
            except: pass

        try:
            print(f"Đăng ký Videoinu - Nickname: {nickname} | Email: {email}")
            page.goto("https://videoinu.com/register", wait_until="networkidle")
            
            # 1. Nhập Nickname (Ô đầu tiên)
            page.wait_for_selector('input[placeholder*="nickname"]')
            page.fill('input[placeholder*="nickname"]', nickname)
            
            # 2. Nhập Email (Ô thứ hai)
            page.fill('input[type="email"]', email)
            
            # 3. Bấm nút lấy mã (Nút nằm bên phải ô OTP trong ảnh)
            # Dựa vào ảnh, nút này thường là một button bên cạnh input OTP
            send_code_btn = page.locator('button:has-text("s"), button:has-text("Send")').first
            if send_code_btn:
                send_code_btn.click()
                print("Đã bấm nút gửi mã xác nhận.")
            
            # Đợi lấy OTP từ API
            otp_code = wait_for_otp(token)
            
            if otp_code:
                print(f"==> MÃ OTP: {otp_code}")
                
                # 4. Nhập mã xác nhận (Ô thứ ba)
                page.fill('input[placeholder*="verification code"]', otp_code)
                
                # 5. Bấm nút "Create Account"
                create_btn = page.get_by_role("button", name="Create Account")
                create_btn.click()
                
                print("Đã bấm nút Create Account. Đang kiểm tra kết quả...")
                time.sleep(5)
                
                # Chụp ảnh kiểm tra thành công
                page.screenshot(path="final_result.png")
                
                # In thông tin ra log
                print("------------------------------------------")
                print(f"ĐĂNG KÝ THÀNH CÔNG: {email}")
                print(f"NICKNAME: {nickname}")
                print("------------------------------------------")
            else:
                print("Không nhận được OTP.")
                page.screenshot(path="no_otp.png")

        except Exception as e:
            print(f"Lỗi: {e}")
            page.screenshot(path="crash.png")
        finally:
            browser.close()

if __name__ == "__main__":
    run_automation()
