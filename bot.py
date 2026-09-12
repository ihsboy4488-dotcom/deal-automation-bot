import os
import requests
import hmac
import hashlib
import time

# 구글 클라우드 고정 IP 서버 주소 (토스 API 우회용)
GCP_TOSS_PROXY = "http://34.44.7.69:8000/make-toss-message"

# 1. 토스 수익 링크 및 멘트 변환 함수 (고정 IP 서버 경유)
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

# 2. (참고) 기존에 쓰시던 쿠팡 링크 변환 함수 위치...
# def get_coupang_link(url):
#     ... (기존 쿠팡 파트너스 API 연동 코드 유지) ...

def 메인():
    print("핫딜 가격 비교 및 링크 변환 시작...")
    
    # 예시: 가격 비교 후 토스가 더 저렴할 때의 처리 예시
    # toss_price = 15000
    # coupang_price = 18000
    
    # if toss_price <= coupang_price:
    #     # 토스 쇼핑 링크 변환 요청 (고정 IP 서버 호출)
    #     result_text = get_toss_monetized_link(
    #         "https://shopping.toss.im/products/...", 
    #         "부드러운 한돈 쫄갈비, 300g, 5팩", 
    #         "🔥 오늘 저녁은 쫄갈비 어떠세요? 역대급 할인가!"
    #     )
    #     print(result_text)
    #     # 이후 기존 메일 발송 로직에 result_text를 태워서 전송!

if __name__ == "__main__":
    메인()
