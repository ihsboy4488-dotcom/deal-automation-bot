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
# 🔑 보안 설정 (깃허브 Secrets에서 가져옴)
# ==========================================
ACCESS_KEY = os.environ.get("COUPANG_ACCESS_KEY")
SECRET_KEY = os.environ.get("COUPANG_SECRET_KEY")
MY_EMAIL = os.environ.get("MY_EMAIL")
APP_PASSWORD = os.environ.get("APP_PASSWORD")

# 주부 및 알뜰족들이 환호하는 핵심 카테고리/키워드 리스트
DEAL_KEYWORDS = [
    "생수", "한우", "스팸", "참치", "햇반", "라면", "세제", "물티슈", 
    "밀키트", "김치", "기저귀", "피자", "만두", "휴지", "식용유", 
    "올리브영", "최저가", "반값", "무료배송", "1+1", "균일가", "특가"
]

SENT_DEALS_FILE = "sent_deals.txt"

def load_sent_deals():
    if os.path.exists(SENT_DEALS_FILE):
        with open(SENT_DEALS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_sent_deal(deal_title):
    with open(SENT_DEALS_FILE, "a", encoding="utf-8") as f:
        f.write(deal_title + "\n")

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
        print(f"📧 [지메일 발송 성공] {subject}")
    except Exception as e:
        print(f"❌ 지메일 전송 실패: {e}")

# 1. 쿠팡 파트너스 최저가/특가 스캐너
def run_coupang_scanner(sent_deals):
    print("🚀 [쿠팡 봇] 실시간 특가 스캔 중...")
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

    # 인기 핫딜 키워드 순회
    search_queries = ["생수 특가", "햇반 최저가", "한우 구이용", "식용유 1+1", "주방세제 대용량"]
    
    for query in search_queries:
        encoded_keyword = urllib.parse.quote(query)
        path_and_query = f"/v2/providers/affiliate_open_api/apis/openapi/products/search?keyword={encoded_keyword}&limit=2"
        url = domain + path_and_query
        authorization = generate_coupang_signature("GET", path_and_query, SECRET_KEY, ACCESS_KEY)
        
        headers = {"Authorization": authorization, "Content-Type": "application/json;charset=UTF-8"}
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                items = response.json().get("data", {}).get("productData", [])
                for item in items:
                    title = item.get('productName')
                    price = item.get('productPrice', 0)
                    link = item.get('productUrl')
                    
                    if title not in sent_deals:
                        sent_deals.add(title)
                        save_sent_deal(title)
                        
                        ment = f"""✱ 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.

🛒 "네이버 및 시중가 비교 완료!" 압도적 가성비 쿠팡 핫딜 떴습니다! 🏃💨

🔥 **상품명:** {title}
💰 **특가 가격:** {price:,}원

인터넷 최저가와 비교해 봐도 메리트 있는 역대급 상품입니다. 품절 되기 전에 확인해 보세요! 👇
🔗 구매 링크: {link}"""
                        send_to_my_gmail(f"[쿠팡 핫딜] {title[:15]}...", ment)
        except Exception as e:
            print(f"❌ 쿠팡 봇 에러: {e}")

# 2. 토스쇼핑 실시간 특가 스캐너
def run_toss_scanner(sent_deals):
    print("🚀 [토스 봇] 실시간 찐특가 스캔 중...")
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
                    if any(kw in text for kw in DEAL_KEYWORDS):
                        if text not in sent_deals:
                            sent_deals.add(text)
                            save_sent_deal(text)
                            count += 1
                            
                            ment = f"""✱ 이 포스팅은 토스쇼핑 쉐어링크 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.

🛒 "다이소·쿠팡보다 더 싼가요?" 토스 실시간 릴레이 특가 포착! 🏃💨

🔥 **상품명:** {text}

주부 눈에 딱 들어온 알뜰 가성비 아이템입니다. 품절 되기 전에 확인해 보세요! 👇
🔗 [토스 앱에서 쉐어링크 복사해서 활용하세요]"""
                            send_to_my_gmail(f"[토스 찐특가] {text[:15]}...", ment)
                            if count >= 2: # 한 번에 너무 많이 오지 않게 제한
                                break
    except Exception as e:
        print(f"❌ 토스 봇 에러: {e}")

# 3. 국내 대형 커뮤니티(뽐뿌 등) 실시간 핫딜 크롤러
def run_hotdeal_community_scanner(sent_deals):
    print("🚀 [커뮤니티 핫딜 봇] 실시간 베스트 핫딜 스캔 중...")
    # 뽐뿌 핫딜 게시판 주소 예시
    url = "https://www.ppomppu.co.kr/zboard/zboard.php?id=ppomppu"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            # 게시글 제목 추출
            titles = soup.select(".list_title")
            count = 0
            for t in titles:
                title_text = t.text.strip()
                # 조회수나 추천수 조건이 좋거나 특가 키워드가 포함된 경우
                if any(kw in title_text for kw in ["무료배송", "특가", "할인", "역대급", "대박", "1+1"]):
                    if title_text not in sent_deals:
                        sent_deals.add(title_text)
                        save_sent_deal(title_text)
                        count += 1
                        
                        ment = f"""🛒 "커뮤니티 실시간 검증 완료!" 네이버 최저가 파괴 핫딜 포착! 🏃💨

🔥 **핫딜 제목:** {title_text}

유저들이 추천한 가성비 대박 상품입니다. 품절 임박일 수 있으니 빠르게 확인해 보세요! 👇
🔗 출처 커뮤니티 핫딜 게시판 확인 요망"""
                        send_to_my_gmail(f"[커뮤니티 핫딜] {title_text[:15]}...", ment)
                        if count >= 2:
                            break
    except Exception as e:
        print(f"❌ 커뮤니티 크롤러 에러: {e}")

if __name__ == "__main__":
    print("🎯 [통합 멀티 오픈마켓 핫딜 큐레이션 봇] 가동 시작!\n")
    sent_deals = load_sent_deals()
    
    # 3대 소스 동시 가동
    run_coupang_scanner(sent_deals)
    run_toss_scanner(sent_deals)
    run_hotdeal_community_scanner(sent_deals)
    
    print("\n✨ 이번 스캔 사이클이 성공적으로 종료되었습니다!")
