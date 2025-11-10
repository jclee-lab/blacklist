#!/usr/bin/env python3
"""
FortiManager External Resource Connector Auto-Setup
JSON-RPC API를 사용한 완전 자동화 스크립트

Usage:
    python fortimanager_connector_setup.py --fmg-host 192.168.1.100 --username admin --password secret
"""

import requests
import json
import argparse
import sys
from urllib3.exceptions import InsecureRequestWarning

# SSL 경고 무시
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)


class FortiManagerAPI:
    """FortiManager JSON-RPC API Client"""

    def __init__(self, host, username, password, adom="root"):
        self.host = host
        self.username = username
        self.password = password
        self.adom = adom
        self.session_id = None
        self.base_url = f"https://{host}/jsonrpc"

    def login(self):
        """FortiManager 로그인 및 세션 ID 획득"""
        payload = {
            "method": "exec",
            "params": [{
                "url": "/sys/login/user",
                "data": {
                    "user": self.username,
                    "passwd": self.password
                }
            }],
            "id": 1
        }

        response = requests.post(self.base_url, json=payload, verify=False)
        result = response.json()

        if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
            self.session_id = result.get("session")
            print(f"✅ FortiManager 로그인 성공 (Session: {self.session_id})")
            return True
        else:
            print(f"❌ 로그인 실패: {result}")
            return False

    def logout(self):
        """세션 종료"""
        if not self.session_id:
            return

        payload = {
            "method": "exec",
            "params": [{
                "url": "/sys/logout"
            }],
            "session": self.session_id,
            "id": 1
        }

        requests.post(self.base_url, json=payload, verify=False)
        print("✅ FortiManager 로그아웃")

    def create_external_resource(self, name, uri, refresh_rate=5):
        """External Resource Connector 생성

        Args:
            name (str): 커넥터 이름
            uri (str): 블랙리스트 API URL
            refresh_rate (int): 갱신 주기 (분)
        """
        if not self.session_id:
            print("❌ 로그인되지 않음")
            return False

        payload = {
            "method": "add",
            "params": [{
                "url": f"/pm/config/adom/{self.adom}/obj/system/external-resource",
                "data": {
                    "name": name,
                    "type": "address",  # IP 주소 타입
                    "resource": uri,
                    "refresh-rate": refresh_rate,
                    "status": "enable",
                    "comments": "NXTD 블랙리스트 자동 동기화 (Auto-configured)"
                }
            }],
            "session": self.session_id,
            "id": 1
        }

        response = requests.post(self.base_url, json=payload, verify=False)
        result = response.json()

        status = result.get("result", [{}])[0].get("status", {})
        if status.get("code") == 0:
            print(f"✅ External Resource '{name}' 생성 성공")
            print(f"   - URI: {uri}")
            print(f"   - Refresh Rate: {refresh_rate} minutes")
            return True
        else:
            print(f"❌ 생성 실패: {status.get('message', 'Unknown error')}")
            return False

    def get_external_resource(self, name):
        """External Resource 정보 조회"""
        if not self.session_id:
            return None

        payload = {
            "method": "get",
            "params": [{
                "url": f"/pm/config/adom/{self.adom}/obj/system/external-resource/{name}"
            }],
            "session": self.session_id,
            "id": 1
        }

        response = requests.post(self.base_url, json=payload, verify=False)
        result = response.json()

        if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
            data = result["result"][0].get("data", {})
            return data
        return None

    def update_external_resource(self, name, uri=None, refresh_rate=None):
        """External Resource 업데이트"""
        if not self.session_id:
            return False

        update_data = {}
        if uri:
            update_data["resource"] = uri
        if refresh_rate:
            update_data["refresh-rate"] = refresh_rate

        payload = {
            "method": "update",
            "params": [{
                "url": f"/pm/config/adom/{self.adom}/obj/system/external-resource/{name}",
                "data": update_data
            }],
            "session": self.session_id,
            "id": 1
        }

        response = requests.post(self.base_url, json=payload, verify=False)
        result = response.json()

        status = result.get("result", [{}])[0].get("status", {})
        if status.get("code") == 0:
            print(f"✅ External Resource '{name}' 업데이트 성공")
            return True
        else:
            print(f"❌ 업데이트 실패: {status.get('message')}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="FortiManager External Resource Connector 자동 설정"
    )
    parser.add_argument("--fmg-host", required=True, help="FortiManager IP 주소")
    parser.add_argument("--username", default="admin", help="관리자 계정 (기본: admin)")
    parser.add_argument("--password", required=True, help="관리자 비밀번호")
    parser.add_argument("--adom", default="root", help="ADOM 이름 (기본: root)")
    parser.add_argument(
        "--connector-name",
        default="NXTD-Blacklist-Feed",
        help="커넥터 이름 (기본: NXTD-Blacklist-Feed)"
    )
    parser.add_argument(
        "--api-url",
        default="https://blacklist.nxtd.co.kr/api/fortinet/threat-feed?format=text",
        help="블랙리스트 API URL"
    )
    parser.add_argument(
        "--refresh-rate",
        type=int,
        default=5,
        help="갱신 주기 (분, 기본: 5)"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="기존 커넥터 업데이트 (없으면 새로 생성)"
    )

    args = parser.parse_args()

    # FortiManager API 클라이언트 생성
    fmg = FortiManagerAPI(
        host=args.fmg_host,
        username=args.username,
        password=args.password,
        adom=args.adom
    )

    # 로그인
    if not fmg.login():
        sys.exit(1)

    try:
        # 기존 커넥터 확인
        existing = fmg.get_external_resource(args.connector_name)

        if existing:
            print(f"⚠️ 커넥터 '{args.connector_name}' 이미 존재")
            print(f"   현재 URI: {existing.get('resource')}")
            print(f"   현재 Refresh Rate: {existing.get('refresh-rate')} minutes")

            if args.update:
                # 업데이트
                fmg.update_external_resource(
                    name=args.connector_name,
                    uri=args.api_url,
                    refresh_rate=args.refresh_rate
                )
            else:
                print("\n💡 --update 옵션으로 기존 커넥터를 업데이트할 수 있습니다")
        else:
            # 새로 생성
            fmg.create_external_resource(
                name=args.connector_name,
                uri=args.api_url,
                refresh_rate=args.refresh_rate
            )

            print("\n✅ 설정 완료!")
            print("\n📋 다음 단계:")
            print("1. FortiManager GUI에서 확인:")
            print("   Policy & Objects > FortiGuard > External Resource")
            print(f"2. '{args.connector_name}' 커넥터 확인")
            print("3. Policy Package에 Threat Feed 할당")
            print("4. FortiGate로 Policy 배포")

    finally:
        # 로그아웃
        fmg.logout()


if __name__ == "__main__":
    main()
