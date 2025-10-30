#!/usr/bin/env python3
"""
REGTECH 간단 테스트 - 공개 데이터 확인
"""

import requests
import re
import json

# SSL 경고 무시
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_public_endpoints():
    """공개 엔드포인트 테스트"""

    base_url = "https://regtech.fsec.or.kr"

    # 공개 가능한 엔드포인트들
    endpoints = [
        "/",
        "/public/api/blacklist",
        "/public/threat",
        "/open/api/blacklist",
        "/api/public/blacklist",
        "/fcti/public",
        "/resources/blacklist.json"
    ]

    session = requests.Session()

    for endpoint in endpoints:
        try:
            print(f"\n테스트: {base_url}{endpoint}")
            resp = session.get(
                f"{base_url}{endpoint}",
                verify=False,
                timeout=10,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )

            print(f"상태: {resp.status_code}")

            if resp.status_code == 200:
                # JSON 응답 확인
                try:
                    data = resp.json()
                    print(f"JSON 응답 발견: {list(data.keys()) if isinstance(data, dict) else f'Array[{len(data)}]'}")
                except:
                    # HTML에서 IP 찾기
                    ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
                    found_ips = ip_pattern.findall(resp.text)
                    if found_ips:
                        print(f"HTML에서 {len(set(found_ips))}개 IP 발견")
                    else:
                        print(f"응답 크기: {len(resp.text)} bytes")

        except Exception as e:
            print(f"오류: {e}")

    # 로그인 없이 접근 가능한 데이터 확인
    print("\n\n=== 로그인 없이 데이터 접근 테스트 ===")

    data_endpoints = [
        "/fcti/blacklist/list",
        "/fcti/threat/blacklist",
        "/api/blacklist/ips"
    ]

    for endpoint in data_endpoints:
        try:
            print(f"\n테스트: {base_url}{endpoint}")

            # GET 시도
            resp = session.get(f"{base_url}{endpoint}", verify=False, timeout=5)
            print(f"GET 상태: {resp.status_code}")

            # POST 시도
            resp = session.post(
                f"{base_url}{endpoint}",
                data={'page': '1', 'rows': '10'},
                verify=False,
                timeout=5
            )
            print(f"POST 상태: {resp.status_code}")

            if resp.status_code == 200:
                if 'login' in resp.url:
                    print("로그인 페이지로 리다이렉트됨")
                else:
                    print(f"접근 가능! URL: {resp.url}")

        except Exception as e:
            print(f"오류: {e}")

if __name__ == "__main__":
    test_public_endpoints()