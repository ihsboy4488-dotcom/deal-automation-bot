import os
import requests
import hmac
import hashlib
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. 환경 변수 설정 (GitHub Secrets에서 가져옴)
# ==========================================
COUPANG_ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY")
COUPANG_SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY")

GMAIL_ADDRESS = os.environ.get("MY_EMAIL")
GMAIL_APP_PW = os.environ.get("APP_PASSWORD")

# 수신자 목록 (다중 발송 지원: 쉼표로 구분된 메일들을 리스트로 변환)
RECEIVER_EMAILS_STR = os.environ.get("RECEIVER_EMAILS", GMAIL_ADDRESS)
RECEIVER_LIST = [email.strip() for email in RECEIVER_EMAILS_STR.split(",")]

# 구글 클라우드 고정 IP 서버 주소 (토스 API 우회용)
GCP_TOSS_PROXY = "http://34.44.7.69:8000/make-toss-message"


# ==========================================
# 2. 쿠팡 파트너스 링크 변환 함수
# ==========================================
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
        print(f"쿠팡 링크 변환 오류: {e}")
    return url


# ==========================================
# 3. 토스 셰어링크 변환 함수 (고정 IP 서버 경유)
# ==========================================
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
        print(f"토스 링크 변환 오류: {e}")
    return None


# ==========================================
# 4. 메일 발송 함수 (다중 수신자 지원)
# ==========================================
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
        print("모든 수신자에게 메일 발송 성공!")
    except Exception as e:
        print(f"메일 발송 실패: {e}")


# ==========================================
# 5. 메인 가격 비교 및 핫딜 조립 로직
# ==========================================
def 메인():
    print("핫딜 수집 및 가격 비교 시작...")
    
    # [예시 데이터] 실제 크롤링 혹은 대상 상품 리스트로 대체하여 사용하세요
    hotdeals = [
        {
            "name": "프리미엄 한돈 세트",
            "toss_price": 24000, "coupang_price": 28000,
            "toss_url": "https://shopping.toss.im/...",
            "coupang_url": "https://www.coupang.com/vp/...",
            "comment": "🔥 오늘 저녁 고기 찬스! 역대급 할인가"
        }
    ]

    final_mail_content = "오늘의 최저가 핫딜 공유 리스트입니다.\n\n"

    for deal in hotdeals:
        # [핵심] 토스와 쿠팡 가격 비교 후 더 저렴한 쪽으로 자동 분기
        if deal["toss_price"] <= deal["coupang_price"]:
            # 토스 쇼핑이 더 저렴한 경우 (고정 IP 서버 경유)
            formatted_msg = get_toss_monetized_link(
                deal["toss_url"], 
                deal["name"], 
                deal["comment"]
            )
            if formatted_msg:
                final_mail_content += formatted_msg + "\n\n"
        else:
            # 쿠팡이 더 저렴한 경우 (기존 쿠팡 파트너스 API 활용)
            short_link = get_coupang_link(deal["coupang_url"])
            final_mail_content += f"{deal['comment']}\n{deal['name']}\n👉 최저가: {deal['coupang_price']:,}원 (쿠팡)\n{short_link}\n✱ 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.\n\n"

    # 최종 완성된 텍스트를 등록된 모든 수신자 메일로 발송
    send_email("[자동화] 오늘의 최저가 핫딜 모음", final_mail_content)

if __name__ == "__main__":
    메인()
