#!/usr/bin/env python3
"""
REGTECH advisoryList 엔드포인트 테스트
"""

import requests
import json
import re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_advisory():
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

    if '/main' not in login_resp.url:
        print("❌ 로그인 실패")
        return

    print("✅ 로그인 성공")

    # advisoryList 페이지 접근
    print("\n/fcti/securityAdvisory/advisoryList 접근...")

    # GET 요청
    resp = session.get('https://regtech.fsec.or.kr/fcti/securityAdvisory/advisoryList')
    print(f"GET 상태: {resp.status_code}")

    if resp.status_code == 200:
        print("✅ 페이지 접근 성공")

        # HTML 분석
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 테이블 찾기
        tables = soup.find_all('table')
        print(f"테이블 수: {len(tables)}")

        # form 찾기
        forms = soup.find_all('form')
        print(f"폼 수: {len(forms)}")

        # JavaScript에서 데이터 URL 찾기
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Ajax URL 패턴 찾기
                ajax_urls = re.findall(r'url\s*:\s*["\']([^"\']+)', script.string)
                if ajax_urls:
                    print("\nAjax URL 발견:")
                    for url in ajax_urls:
                        print(f"  - {url}")

                # 데이터 그리드 설정 찾기
                if 'grid' in script.string.lower() or 'data' in script.string.lower():
                    grid_configs = re.findall(r'url\s*:\s*["\'][^"\']*list[^"\']*["\']', script.string)
                    if grid_configs:
                        print("\n그리드 데이터 URL:")
                        for config in grid_configs:
                            print(f"  - {config}")

        # IP 패턴 찾기
        ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        ips = ip_pattern.findall(resp.text)
        if ips:
            print(f"\n페이지에서 IP 발견: {len(set(ips))}개")
            print(f"샘플: {list(set(ips))[:5]}")

    # POST 요청으로 데이터 가져오기
    print("\n\nPOST 요청으로 데이터 시도...")

    # 다양한 파라미터 조합 시도
    param_sets = [
        {'page': '1', 'rows': '100'},
        {'pageNo': '1', 'pageSize': '100'},
        {'start': '0', 'limit': '100'},
        {'draw': '1', 'start': '0', 'length': '100'}
    ]

    for params in param_sets:
        print(f"\n파라미터: {params}")

        resp = session.post(
            'https://regtech.fsec.or.kr/fcti/securityAdvisory/advisoryList',
            data=params,
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )

        print(f"응답 상태: {resp.status_code}")

        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"JSON 응답: {list(data.keys()) if isinstance(data, dict) else 'Array'}")

                # 데이터 찾기
                if isinstance(data, dict):
                    for key in ['data', 'rows', 'list', 'result']:
                        if key in data:
                            print(f"데이터 키 '{key}' 발견: {len(data[key]) if isinstance(data[key], list) else 'Not a list'}")
                            if isinstance(data[key], list) and data[key]:
                                print(f"첫 번째 항목: {data[key][0]}")

            except json.JSONDecodeError:
                # HTML 응답인 경우 IP 찾기
                ips = ip_pattern.findall(resp.text)
                if ips:
                    print(f"HTML에서 IP 발견: {len(set(ips))}개")

    # advisoryList.json 시도
    print("\n\nadvisoryList.json 엔드포인트 시도...")
    resp = session.post(
        'https://regtech.fsec.or.kr/fcti/securityAdvisory/advisoryList.json',
        data={'page': '1', 'rows': '100'}
    )
    print(f"상태: {resp.status_code}")

    if resp.status_code == 200:
        try:
            data = resp.json()
            print(f"JSON 데이터: {data}")
        except:
            print("JSON 파싱 실패")

if __name__ == "__main__":
    test_advisory()