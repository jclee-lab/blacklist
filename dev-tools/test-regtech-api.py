#!/usr/bin/env python3
"""
REGTECH API 문서 확인
"""

import requests
import re
from bs4 import BeautifulSoup
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def find_api_docs():
    username = 'nextrade'
    password = 'Sprtmxm1@3'

    session = requests.Session()
    session.verify = False

    # 로그인
    print("로그인 중...")
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

    print("✅ 로그인 성공")

    # API 문서나 개발자 가이드 찾기
    api_pages = [
        '/api',
        '/api/doc',
        '/api/docs',
        '/developer',
        '/guide/api',
        '/docs',
        '/swagger',
        '/api-docs',
        '/help/api'
    ]

    print("\nAPI 문서 페이지 확인:")
    for page in api_pages:
        try:
            resp = session.get(f'https://regtech.fsec.or.kr{page}', timeout=5)
            print(f"{page}: {resp.status_code}")
            if resp.status_code == 200:
                print(f"  ✅ 접근 가능!")
        except:
            print(f"{page}: 오류")

    # 메인 페이지에서 메뉴 분석
    print("\n\n메인 페이지 메뉴 분석:")
    main_resp = session.get('https://regtech.fsec.or.kr/main/main')

    if main_resp.status_code == 200:
        soup = BeautifulSoup(main_resp.text, 'html.parser')

        # 모든 링크 추출
        links = soup.find_all('a', href=True)
        api_related = []
        threat_related = []

        for link in links:
            href = link['href']
            text = link.get_text(strip=True)

            if any(word in href.lower() for word in ['api', 'data', 'download', 'export']):
                api_related.append((text, href))

            if any(word in text.lower() for word in ['위협', '침해', '악성', 'threat', 'malware', 'blacklist']):
                threat_related.append((text, href))

        if api_related:
            print("\nAPI 관련 링크:")
            for text, href in api_related[:10]:
                print(f"  - {text}: {href}")

        if threat_related:
            print("\n위협 관련 링크:")
            for text, href in threat_related[:10]:
                print(f"  - {text}: {href}")

    # JavaScript에서 API 호출 찾기
    print("\n\nJavaScript API 호출 분석:")
    scripts = soup.find_all('script')

    api_calls = []
    for script in scripts:
        if script.string:
            # $.ajax, fetch, axios 패턴 찾기
            ajax_patterns = [
                r'\$\.ajax\s*\(\s*\{[^}]*url\s*:\s*["\']([^"\']+)',
                r'fetch\s*\(["\']([^"\']+)',
                r'axios\.\w+\s*\(["\']([^"\']+)'
            ]

            for pattern in ajax_patterns:
                matches = re.findall(pattern, script.string)
                api_calls.extend(matches)

    # 중복 제거 및 필터링
    unique_apis = set(api_calls)
    filtered_apis = [api for api in unique_apis if
                     any(word in api.lower() for word in ['list', 'data', 'get', 'find', 'search'])]

    if filtered_apis:
        print("발견된 API 호출:")
        for api in filtered_apis[:20]:
            print(f"  - {api}")

    # 네트워크 요청 분석을 위한 특정 페이지 접근
    print("\n\n특정 기능 페이지 테스트:")

    # 마이기관페이지나 다른 기능 페이지
    feature_pages = [
        '/organ/myOrgan/myOrganMain',
        '/member/crisisMemberList',
        '/fcti/securityAdvisory/advisoryList'
    ]

    for page in feature_pages:
        try:
            resp = session.get(f'https://regtech.fsec.or.kr{page}', timeout=5)
            if resp.status_code == 200:
                print(f"\n{page} 페이지 분석:")

                # 페이지에서 데이터 테이블이나 그리드 찾기
                soup = BeautifulSoup(resp.text, 'html.parser')

                # data-url 속성 찾기
                data_urls = soup.find_all(attrs={'data-url': True})
                if data_urls:
                    print("  데이터 URL 속성:")
                    for elem in data_urls:
                        print(f"    - {elem.get('data-url')}")

                # grid 설정 찾기
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'grid' in script.string.lower():
                        grid_urls = re.findall(r'url\s*:\s*["\']([^"\']+)', script.string)
                        if grid_urls:
                            print("  그리드 데이터 URL:")
                            for url in grid_urls[:5]:
                                print(f"    - {url}")

        except Exception as e:
            print(f"{page}: 오류 - {e}")

if __name__ == "__main__":
    find_api_docs()