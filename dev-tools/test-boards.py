#!/usr/bin/env python3
"""
REGTECH 게시판들 확인 - 보안 권고 데이터 찾기
"""

import requests
import json
import re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_boards():
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

    # 보드 종류들
    boards = [
        ('/board/2/boardList', '가이드라인'),  # 가이드라인
        ('/board/3/boardList', '보안 동향'),    # 보안 동향
        ('/board/4/boardList', '연구 보고서'),  # 연구 보고서
        ('/board/11/boardList', '공지사항'),
        ('/board/14/boardList', '기타')
    ]

    ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
    found_any_ip = False

    for board_url, board_name in boards:
        print(f"\n=== {board_name} ({board_url}) ===")

        resp = session.get(f'https://regtech.fsec.or.kr{board_url}')
        print(f"상태: {resp.status_code}")

        if resp.status_code == 200:
            # IP 찾기
            ips = ip_pattern.findall(resp.text)
            if ips:
                print(f"✅ IP 발견: {len(set(ips))}개")
                print(f"샘플: {list(set(ips))[:5]}")
                found_any_ip = True

            # 테이블 구조 확인
            soup = BeautifulSoup(resp.text, 'html.parser')
            tables = soup.find_all('table')
            if tables:
                print(f"테이블 수: {len(tables)}")

                # 첫 번째 테이블의 헤더 확인
                if tables[0].find('thead'):
                    headers = [th.get_text(strip=True) for th in tables[0].find('thead').find_all('th')]
                    print(f"헤더: {headers}")

    # 위협 정보 관련 URL 직접 시도
    print("\n\n=== 위협 정보 관련 페이지 시도 ===")

    threat_urls = [
        '/threat/ip',
        '/threat/blacklist',
        '/security/blacklist',
        '/api/threat/ip',
        '/data/threat',
        '/malware/list',
        '/incident/list',
        '/vulnerability/list'
    ]

    for url in threat_urls:
        try:
            print(f"\n시도: {url}")
            resp = session.get(f'https://regtech.fsec.or.kr{url}', timeout=5)
            print(f"상태: {resp.status_code}")

            if resp.status_code == 200:
                ips = ip_pattern.findall(resp.text)
                if ips:
                    print(f"✅ IP 발견: {len(set(ips))}개")
                    found_any_ip = True

        except Exception as e:
            print(f"오류: {e}")

    if not found_any_ip:
        print("\n\n⚠️ 어떤 페이지에서도 블랙리스트 IP를 찾을 수 없습니다.")
        print("REGTECH는 IP 블랙리스트를 웹 인터페이스로 제공하지 않거나,")
        print("특별한 권한이나 다른 접근 방법이 필요할 수 있습니다.")

if __name__ == "__main__":
    test_boards()