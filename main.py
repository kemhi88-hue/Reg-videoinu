import re
import time
import requests
import random
import string
from playwright.sync_api import sync_playwright
# SỬA DÒNG NÀY:
from playwright_stealth import stealth_page

# ... các hàm get_mail_tm và wait_for_otp giữ nguyên ...

def run_automation():
    email, token = get_mail_tm()
    if not email:
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # SỬA DÒNG NÀY: Sử dụng stealth_page thay vì stealth_sync
        stealth_page(page)

        print(f"Bắt đầu đăng ký tài khoản: {email}")
        
        # ... các bước còn lại giữ nguyên ...
