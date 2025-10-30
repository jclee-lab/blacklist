#!/usr/bin/env python3
"""
REGTECH 페이지 분석 - 실제 엔드포인트 찾기
"""

import requests
import re
from bs4 import BeautifulSoup
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def analyze_regtech():
    username = 'nextrade'
    password = 'Sprtmxm1@3'

    session = requests.Session()
    session.verify = False

    # 1. 로그인
    print("1. 로그인 중...")
    session.get('https://regtech.fsec.or.kr/login/loginForm')

    login_resp = session.post(
        'https://regtech.fsec.or.kr/login/addLogin',
        data={
            'username': username,
            'password': password,
            'id': username,
            'pwd': password
        },
        allow_redirects=True
    )

    if '/main' in login_resp.url:
        print("✅ 로그인 성공")
        print(f"JWT 토큰: {session.cookies.get('regtech-va', '')[:50]}...")
    else:
        print("❌ 로그인 실패")
        return

    # 2. 메인 페이지 분석
    print("\n2. 메인 페이지 분석...")
    main_html = login_resp.text

    # JavaScript에서 API 엔드포인트 찾기
    api_patterns = [
        r'url\s*:\s*["\']([^"\']+)',
        r'endpoint\s*:\s*["\']([^"\']+)',
        r'href\s*=\s*["\']([^"\']+)',
        r'action\s*=\s*["\']([^"\']+)'
    ]

    found_urls = set()
    for pattern in api_patterns:
        matches = re.findall(pattern, main_html)
        for match in matches:
            if match.startswith('/'):
                found_urls.add(match)

    print(f"발견된 URL: {len(found_urls)}개")

    # 관심있는 키워드로 필터
    keywords = ['blacklist', 'threat', 'ip', 'block', 'security', 'api', 'data', 'list']
    relevant_urls = []

    for url in found_urls:
        for keyword in keywords:
            if keyword in url.lower():
                relevant_urls.append(url)
                break

    print("\n관련 URL들:")
    for url in sorted(set(relevant_urls)):
        print(f"  - {url}")

    # 3. 메뉴 구조 분석
    print("\n3. 메뉴 구조 분석...")
    soup = BeautifulSoup(main_html, 'html.parser')

    # 링크 찾기
    links = soup.find_all('a', href=True)
    menu_items = []
    for link in links:
        href = link['href']
        text = link.get_text(strip=True)
        if href.startswith('/') and text:
            menu_items.append((text, href))

    print("메뉴 항목들:")
    for text, href in menu_items[:20]:  # 처음 20개만
        print(f"  - {text}: {href}")

    # 4. 실제 데이터 페이지 시도
    print("\n4. 데이터 페이지 접근 시도...")

    # 메뉴에서 찾은 URL들 시도
    test_urls = [
        '/fcti/securityAdvisory',
        '/fcti/threatInfo',
        '/fcti/main',
        '/security/threat',
        '/threat/list'
    ]

    for test_url in test_urls:
        try:
            print(f"\n시도: {test_url}")
            resp = session.get(f'https://regtech.fsec.or.kr{test_url}', timeout=5)
            print(f"  상태: {resp.status_code}")

            if resp.status_code == 200:
                # 페이지에서 테이블이나 데이터 찾기
                soup = BeautifulSoup(resp.text, 'html.parser')

                # 테이블 찾기
                tables = soup.find_all('table')
                if tables:
                    print(f"  테이블 발견: {len(tables)}개")

                # IP 패턴 찾기
                ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
                ips = ip_pattern.findall(resp.text)
                if ips:
                    print(f"  IP 발견: {len(set(ips))}개")
                    print(f"  샘플: {list(set(ips))[:3]}")

        except Exception as e:
            print(f"  오류: {e}")

    # 5. Ajax 엔드포인트 찾기
    print("\n5. Ajax/API 엔드포인트 탐색...")

    # JavaScript 파일에서 API 엔드포인트 찾기
    js_files = re.findall(r'<script[^>]*src="([^"]+\.js)"', main_html)
    print(f"JavaScript 파일: {len(js_files)}개")

    for js_file in js_files[:3]:  # 처음 3개만
        try:
            if not js_file.startswith('http'):
                js_file = f'https://regtech.fsec.or.kr{js_file}'

            js_resp = session.get(js_file, timeout=5)
            if js_resp.status_code == 200:
                # API 경로 찾기
                api_matches = re.findall(r'["\']/(api|fcti|threat|blacklist|security)[^"\']*["\']', js_resp.text)
                if api_matches:
                    print(f"\nJS 파일에서 발견된 API 경로:")
                    for match in set(api_matches[:10]):
                        print(f"  - {match}")

        except Exception as e:
            pass

if __name__ == "__main__":
    analyze_regtech()