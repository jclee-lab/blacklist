#!/usr/bin/env python3
"""
REGTECH 디버깅 테스트 스크립트
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv
import logging
import re

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

def test_regtech_connection():
    """REGTECH 연결 테스트"""

    username = os.getenv('REGTECH_ID', 'nextrade')
    password = os.getenv('REGTECH_PW', '')

    if not password:
        logger.error("REGTECH_PW 환경변수가 설정되지 않았습니다")
        return

    logger.info(f"테스트 계정: {username}")

    session = requests.Session()
    session.verify = False

    # 1. 로그인 페이지 접근 테스트
    logger.info("\n=== 1. 로그인 페이지 접근 테스트 ===")
    try:
        resp = session.get('https://regtech.fsec.or.kr/login/loginForm', timeout=10)
        logger.info(f"로그인 페이지 상태: {resp.status_code}")
        logger.info(f"쿠키: {dict(session.cookies)}")

        # CSRF 토큰 추출
        csrf_match = re.search(r'name="(_csrf|csrf_token|token)".*?value="([^"]+)"', resp.text)
        csrf_token = csrf_match.group(2) if csrf_match else None
        logger.info(f"CSRF 토큰: {'발견' if csrf_token else '없음'}")

    except Exception as e:
        logger.error(f"로그인 페이지 접근 실패: {e}")
        return

    # 2. 로그인 시도
    logger.info("\n=== 2. 로그인 시도 ===")

    login_data = {
        'username': username,
        'password': password,
        'id': username,
        'pwd': password
    }

    if csrf_token:
        login_data['_csrf'] = csrf_token
        login_data['token'] = csrf_token

    # 여러 로그인 엔드포인트 시도
    login_endpoints = [
        '/login/addLogin',
        '/login/login.do',
        '/login/loginProcess'
    ]

    logged_in = False
    for endpoint in login_endpoints:
        try:
            logger.info(f"엔드포인트 시도: {endpoint}")
            resp = session.post(
                f'https://regtech.fsec.or.kr{endpoint}',
                data=login_data,
                headers={
                    'Referer': 'https://regtech.fsec.or.kr/login/loginForm',
                    'Origin': 'https://regtech.fsec.or.kr'
                },
                allow_redirects=True,
                timeout=10
            )

            logger.info(f"응답 상태: {resp.status_code}")
            logger.info(f"최종 URL: {resp.url}")
            logger.info(f"쿠키: {dict(session.cookies)}")

            # Check if redirected to main page (successful login)
            if '/main' in resp.url or '/index' in resp.url:
                logger.info(f"✅ 로그인 성공 (리다이렉트): {endpoint}")
                logged_in = True
                break

            if resp.status_code == 200:
                if 'JSESSIONID' in session.cookies or 'SESSION' in session.cookies:
                    logger.info(f"✅ 로그인 성공: {endpoint}")
                    logged_in = True
                    break

            # JSON 응답 확인
            try:
                json_resp = resp.json()
                if json_resp.get('success') or json_resp.get('result') == 'success':
                    logger.info(f"✅ 로그인 성공 (JSON): {endpoint}")
                    logged_in = True
                    break
            except:
                pass

        except Exception as e:
            logger.error(f"로그인 실패 {endpoint}: {e}")

    if not logged_in:
        logger.error("❌ 모든 로그인 시도 실패")
        return

    # 3. 데이터 수집 테스트
    logger.info("\n=== 3. 데이터 수집 테스트 ===")

    data_endpoints = [
        ('/fcti/blacklist/list', {'page': '1', 'rows': '10'}),
        ('/fcti/blacklist/ipList', {'page': '1', 'rows': '10'}),
        ('/fcti/threat/blacklist', None),
        ('/api/blacklist/ips', None)
    ]

    for endpoint, params in data_endpoints:
        try:
            logger.info(f"데이터 엔드포인트 시도: {endpoint}")

            if params:
                resp = session.post(
                    f'https://regtech.fsec.or.kr{endpoint}',
                    data=params,
                    timeout=10
                )
            else:
                resp = session.get(
                    f'https://regtech.fsec.or.kr{endpoint}',
                    timeout=10
                )

            logger.info(f"응답 상태: {resp.status_code}")

            if resp.status_code == 200:
                # JSON 파싱 시도
                try:
                    data = resp.json()
                    logger.info(f"✅ JSON 데이터 수신")
                    logger.info(f"데이터 구조: {list(data.keys()) if isinstance(data, dict) else 'Array'}")

                    # IP 찾기
                    ip_count = 0
                    if isinstance(data, dict):
                        for key in ['data', 'rows', 'list', 'blacklist_ips']:
                            if key in data and isinstance(data[key], list):
                                ip_count = len(data[key])
                                if ip_count > 0:
                                    logger.info(f"✅ {ip_count}개 IP 발견 (키: {key})")
                                    logger.info(f"샘플: {data[key][0] if data[key] else 'N/A'}")
                                    break

                    if ip_count > 0:
                        return

                except json.JSONDecodeError:
                    # HTML에서 IP 추출
                    ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
                    found_ips = ip_pattern.findall(resp.text)
                    unique_ips = set(found_ips)

                    if unique_ips:
                        logger.info(f"✅ HTML에서 {len(unique_ips)}개 IP 발견")
                        logger.info(f"샘플 IP: {list(unique_ips)[:5]}")
                        return

        except Exception as e:
            logger.error(f"데이터 수집 실패 {endpoint}: {e}")

    logger.warning("⚠️ 모든 엔드포인트에서 데이터를 찾을 수 없음")

if __name__ == "__main__":
    test_regtech_connection()