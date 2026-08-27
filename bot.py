import hmac
import hashlib
import requests
import urllib.parse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
import os
from bs4 import BeautifulSoup

# ==========================================
# 🔑 보안 설정 (깃허브 비밀고문에서 가져옴)
# ==========================================
ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY")
SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY")
MY_EMAIL = os.environ.get("MY_EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")

# 쿠팡 키워드 리스트
COUPANG_KEYWORDS = ["한우 구이용", "생수 특가", "햇반 최저가", "냉동만두 특가"]

# 토스 타겟 키워드
TARGET_ITEMS = ["수세미", "세제", "물티슈", "생수", "밀키트", "김치", "행주", "지퍼락", "기저귀", "피자", "만두", "간식"]
MUST_INCLUDE_KEYWORDS = ["특가", "최저가", "반값", "할인", "무료배송", "1+1", "원플원", "균일가", "세일"]

def send_to_my_gmail(subject, content):
    try:
        msg = MIMEMultipart()
        msg['From'] = MY_EMAIL
        msg['To'] = MY_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(MY_EMAIL, APP_PASSWORD)
        server.sendmail(MY_EMAIL, MY_EMAIL, msg.as_string())
        server.quit()
        print(f"📧 [지메일 전송 성공] {subject}")
    except Exception as e:
        print(f"❌ 지메일 전송 실패: {e}")

# 1. 쿠팡 파트너스 실행 함수
def run_coupang_bot():
    print("🚀 [쿠팡 봇] 핫딜 수집 시작...")
    domain = "https://api-gateway.coupang.com"
    
    def generate_coupang_signature(method, uri, secret_key, access_key):
        now = datetime.now(timezone.utc)
        formatted_time = now.strftime("%y%m%d") + "T" + now.strftime("%H%M%S") + "Z"
        parts = uri.split("?")
        path = parts[0]
        query = parts[1] if len(parts) > 1 else ""
        message = formatted_time + method + path + query
        signature = hmac.new(secret_key.strip().encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
        return f"CEA algorithm=HmacSHA256, access-key={access_key}, signed-date={formatted_time}, signature={signature}"

    for keyword in COUPANG_KEYWORDS:
        encoded_keyword = urllib.parse.quote(keyword)
        path_and_query = f"/v2/providers/affiliate_open_api/apis/openapi/products/search?keyword={encoded_keyword}&limit=1"
        url = domain + path_and_query
        authorization = generate_coupang_signature("GET", path_and_query, SECRET_KEY, ACCESS_KEY)
        
        headers = {"Authorization": authorization, "Content-Type": "application/json;charset=UTF-8"}
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json().get("data", {}).get("productData", [])
                if data:
                    item = data[0]
                    price_str = f"{item.get('productPrice'):,}원"
                    ment = f"""✱ 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.

🛒 "이 가격 실화인가요?" 쿠팡 최저가 핫딜 떴습니다! 🏃💨

🔥 **{item.get('productName')}**
💰 할인가: **{price_str}**

인터넷 최저가나 마트 가격과 비교해 봐도 메리트 있네요. 품절 되기 전에 확인해 보세요! 👇
🔗 구매 링크: {item.get('productUrl')}"""
                    send_to_my_gmail(f"[쿠팡 핫딜] {keyword} 특가 도착!", ment)
        except Exception as e:
            print(f"❌ 쿠팡 에러: {e}")

# 2. 토스쇼핑 핫딜 스캐너 함수
def run_toss_bot():
    print("🚀 [토스 봇] 핫딜 수집 시작...")
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Accept-Language": "ko-KR,ko;q=0.9"
    }
    url = "https://sharelink.toss.im/home"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            elements = soup.select("span, div, a")
            count = 0
            for el in elements:
                text = el.text.strip()
                if len(text) > 8 and "http" not in text and "토스" not in text:
                    if any(item in text for item in TARGET_ITEMS) or any(kw in text for kw in MUST_INCLUDE_KEYWORDS):
                        count += 1
                        ment = f"""✱ 이 포스팅은 토스쇼핑 쉐어링크 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.

🛒 "다이소나 쿠팡보다 더 싼가요?" 역대급 신규 특가 포착! 🏃💨

🔥 상품명: {text}

주부 눈에 딱 들어온 알뜰 가성비 아이템입니다. 품절 되기 전에 확인해 보세요! 👇
🔗 [토스 앱에서 쉐어링크 복사해서 붙여넣기 하세요!]"""
                        send_to_my_gmail(f"[토스 신규 찐특가] {text[:15]}...", ment)
                        if count >= 2: # 깃허브 실행 시 너무 많이 오지 않게 상위 2개 제한
                            break
    except Exception as e:
        print(f"❌ 토스 에러: {e}")

if __name__ == "__main__":
    run_coupang_bot()
    run_toss_bot()