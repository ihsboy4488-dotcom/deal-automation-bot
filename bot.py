import os
import requests
import hmac
import hashlib
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ===================================================
# 🔑 [직접 입력 구간] 쿠팡 및 지메일 정보를 여기에 바로 넣으세요
# ===================================================
COUPANG_ACCESS_KEY = "42800da7-2349-4510-9125-3ea8be9f9fa9"
COUPANG_SECRET_KEY = "50ebea131cf2a08d989317ef2f1c3afa80a848b8"

GMAIL_ADDRESS = "ihsboy4488@gmail.com"
GMAIL_APP_PW = "epml hwte hzaa fbet"

# 수신자 목록 (본인 메일 및 동료 관리자 메일들을 쉼표로 구분)
RECEIVER_LIST = [GMAIL_ADDRESS] # 예: ["내메일@gmail.com", "동료메일@gmail.com"]

# 구글 클라우드 고정 IP 서버 주소 (토스 API 우회용)
GCP_TOSS_PROXY = "http://34.44.7.69:8000/make-toss-message"
# ===================================================

def get_coupang_link(url):
    method = "POST"
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    
    datetime = time.strftime('%y%m%d') + 'T' + time.strftime('%H%M%S') + 'Z'
    message = datetime + method + path.replace("?", "")
    signature = hmac.new(bytes(COUPANG_SECRET_KEY, "utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    
    headers = {
        "Authorization": f"CEA algorithm=HmacSHA256, access-key={COUPANG_ACCESS_KEY}, signed-date={datetime}, signature={signature}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(f"https://api-gateway.coupang.com{path}", json={"coupangUrls": [url]}, headers=headers)
        if response.status_code == 200:
            return response.json().get("data")[0].get("shortenUrl")
    except Exception as e:
        print(f"Coupang link error: {e}")
    return url

def get_toss_monetized_link(original_url, product_title, custom_comment):
    try:
        payload = {
            "url": original_url,
            "title": product_title,
            "comment": custom_comment
        }
        response = requests.post(GCP_TOSS_PROXY, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json().get("formatted_message")
    except Exception as e:
        print(f"Toss link error: {e}")
    return None

def send_email(subject, content):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_ADDRESS
    msg['To'] = ", ".join(RECEIVER_LIST)
    msg['Subject'] = subject
    msg.attach(MIMEText(content, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_ADDRESS, GMAIL_APP_PW)
        server.sendmail(GMAIL_ADDRESS, RECEIVER_LIST, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Email failed: {e}")

def main():
    print("Starting deal automation...")
    
    hotdeals = [
        {
            "name": "Sample Product",
            "toss_price": 24000, "coupang_price": 28000,
            "toss_url": "https://shopping.toss.im/...",
            "coupang_url": "https://www.coupang.com/vp/...",
            "comment": "🔥 Hot Deal!"
        }
    ]

    final_mail_content = "Today's Best Deals:\n\n"

    for deal in hotdeals:
        if deal["toss_price"] <= deal["coupang_price"]:
            formatted_msg = get_toss_monetized_link(
                deal["toss_url"], 
                deal["name"], 
                deal["comment"]
            )
            if formatted_msg:
                final_mail_content += formatted_msg + "\n\n"
        else:
            short_link = get_coupang_link(deal["coupang_url"])
            final_mail_content += f"{deal['comment']}\n{deal['name']}\n👉 Price: {deal['coupang_price']:,} KRW (Coupang)\n{short_link}\n\n"

    send_email("[Automation] Daily Deals", final_mail_content)

if __name__ == "__main__":
    main()
