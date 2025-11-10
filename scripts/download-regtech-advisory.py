#!/usr/bin/env python3
"""
REGTECH 보안 권고사항 다운로드 스크립트
========================================

URL: https://regtech.fsec.or.kr/fcti/securityAdvisory/advisoryView
용도: 리눅스 서버 대상 점검도구 및 보안 권고사항 다운로드
"""

import requests
import json
import csv
from datetime import datetime
from pathlib import Path
import sys
import os

# 색상 코드
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def log_info(msg):
    print(f"{BLUE}[INFO]{NC} {msg}")

def log_success(msg):
    print(f"{GREEN}[SUCCESS]{NC} {msg}")

def log_warning(msg):
    print(f"{YELLOW}[WARNING]{NC} {msg}")

def log_error(msg):
    print(f"{RED}[ERROR]{NC} {msg}")

class RegtechAdvisoryDownloader:
    """REGTECH 보안 권고사항 다운로더"""

    def __init__(self, output_dir="./regtech_advisory"):
        self.base_url = "https://regtech.fsec.or.kr"
        self.advisory_url = f"{self.base_url}/fcti/securityAdvisory/advisoryView"
        self.api_url = f"{self.base_url}/api/fcti/securityAdvisory"  # 추정 API
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Referer': self.advisory_url,
        })

    def authenticate(self, username=None, password=None):
        """
        REGTECH 인증 (필요 시)

        환경변수 우선: REGTECH_ID, REGTECH_PW
        """
        username = username or os.getenv('REGTECH_ID')
        password = password or os.getenv('REGTECH_PW')

        if not username or not password:
            log_warning("REGTECH credentials not provided (may not need auth)")
            return True

        log_info("Authenticating with REGTECH...")

        # Step 1: findOneMember
        find_url = f"{self.base_url}/api/member/findOneMember"
        find_data = {
            "userId": username,
            "userPw": password
        }

        try:
            resp = self.session.post(find_url, json=find_data, timeout=10)
            if resp.status_code != 200:
                log_error(f"Authentication failed (step 1): {resp.status_code}")
                return False

            # Step 2: addLogin
            login_url = f"{self.base_url}/api/member/addLogin"
            login_resp = self.session.post(login_url, json=find_data, timeout=10)

            if login_resp.status_code == 200:
                log_success("Authentication successful")
                return True
            else:
                log_error(f"Authentication failed (step 2): {login_resp.status_code}")
                return False

        except Exception as e:
            log_error(f"Authentication error: {e}")
            return False

    def fetch_advisory_list(self, page=1, size=100):
        """
        보안 권고사항 목록 조회

        Args:
            page: 페이지 번호
            size: 페이지 크기

        Returns:
            list: 권고사항 목록
        """
        log_info(f"Fetching advisory list (page={page}, size={size})...")

        # 일반적인 REST API 패턴 시도
        params = {
            'page': page,
            'size': size,
            'sort': 'createdAt,desc'
        }

        try:
            # 시도 1: /api/fcti/securityAdvisory/list
            url = f"{self.base_url}/api/fcti/securityAdvisory/list"
            resp = self.session.get(url, params=params, timeout=10)

            if resp.status_code == 200:
                data = resp.json()
                if 'content' in data:  # Spring Data REST 패턴
                    return data['content']
                elif isinstance(data, list):
                    return data
                else:
                    return [data]

            # 시도 2: /fcti/securityAdvisory/advisoryList (JSP)
            url = f"{self.base_url}/fcti/securityAdvisory/advisoryList"
            resp = self.session.get(url, params=params, timeout=10)

            if resp.status_code == 200:
                # HTML 파싱 필요 시 추가
                log_warning("HTML response received - may need parsing")
                return []

            log_error(f"Failed to fetch advisory list: {resp.status_code}")
            return []

        except Exception as e:
            log_error(f"Error fetching advisory list: {e}")
            return []

    def download_advisory_file(self, advisory_id, file_url):
        """
        권고사항 첨부파일 다운로드

        Args:
            advisory_id: 권고사항 ID
            file_url: 파일 URL

        Returns:
            str: 저장된 파일 경로
        """
        try:
            if not file_url.startswith('http'):
                file_url = f"{self.base_url}{file_url}"

            resp = self.session.get(file_url, timeout=30)

            if resp.status_code == 200:
                # 파일명 추출
                filename = file_url.split('/')[-1]
                if not filename or '?' in filename:
                    filename = f"advisory_{advisory_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                # 저장
                filepath = self.output_dir / filename
                filepath.write_bytes(resp.content)

                log_success(f"Downloaded: {filename} ({len(resp.content)} bytes)")
                return str(filepath)
            else:
                log_error(f"Failed to download file: {resp.status_code}")
                return None

        except Exception as e:
            log_error(f"Error downloading file: {e}")
            return None

    def export_to_csv(self, advisory_list, filename="regtech_advisory.csv"):
        """
        권고사항 목록을 CSV로 저장

        Args:
            advisory_list: 권고사항 목록
            filename: 저장할 파일명
        """
        if not advisory_list:
            log_warning("No advisory data to export")
            return

        filepath = self.output_dir / filename

        # CSV 필드 추출 (첫 번째 항목 기준)
        fields = list(advisory_list[0].keys())

        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(advisory_list)

        log_success(f"Exported to CSV: {filepath} ({len(advisory_list)} records)")

    def export_to_json(self, advisory_list, filename="regtech_advisory.json"):
        """
        권고사항 목록을 JSON으로 저장

        Args:
            advisory_list: 권고사항 목록
            filename: 저장할 파일명
        """
        if not advisory_list:
            log_warning("No advisory data to export")
            return

        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(advisory_list, f, ensure_ascii=False, indent=2)

        log_success(f"Exported to JSON: {filepath} ({len(advisory_list)} records)")

    def run(self, format='csv', max_pages=10):
        """
        보안 권고사항 다운로드 실행

        Args:
            format: 출력 포맷 (csv, json, both)
            max_pages: 최대 페이지 수
        """
        log_info("Starting REGTECH Advisory Downloader")
        log_info("=" * 50)

        # 1. 인증 (필요 시)
        self.authenticate()

        # 2. 목록 조회
        all_advisories = []

        for page in range(1, max_pages + 1):
            advisories = self.fetch_advisory_list(page=page)

            if not advisories:
                log_info(f"No more data at page {page}")
                break

            all_advisories.extend(advisories)
            log_info(f"Page {page}: {len(advisories)} records")

        if not all_advisories:
            log_error("No advisory data retrieved")
            return

        log_success(f"Total advisories retrieved: {len(all_advisories)}")

        # 3. 파일 다운로드 (첨부파일이 있는 경우)
        for advisory in all_advisories:
            if 'fileUrl' in advisory and advisory['fileUrl']:
                self.download_advisory_file(advisory.get('id'), advisory['fileUrl'])

        # 4. 내보내기
        if format in ['csv', 'both']:
            self.export_to_csv(all_advisories)

        if format in ['json', 'both']:
            self.export_to_json(all_advisories)

        log_success("Download completed!")
        log_info(f"Output directory: {self.output_dir.resolve()}")


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(
        description='REGTECH 보안 권고사항 다운로드',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # CSV 다운로드
  python download-regtech-advisory.py --format csv

  # JSON 다운로드
  python download-regtech-advisory.py --format json

  # 둘 다 다운로드
  python download-regtech-advisory.py --format both

  # 인증 정보 제공
  export REGTECH_ID=your_id
  export REGTECH_PW=your_password
  python download-regtech-advisory.py
        """
    )

    parser.add_argument(
        '--format',
        choices=['csv', 'json', 'both'],
        default='csv',
        help='출력 포맷 (기본: csv)'
    )

    parser.add_argument(
        '--output',
        default='./regtech_advisory',
        help='출력 디렉토리 (기본: ./regtech_advisory)'
    )

    parser.add_argument(
        '--max-pages',
        type=int,
        default=10,
        help='최대 페이지 수 (기본: 10)'
    )

    parser.add_argument(
        '--username',
        help='REGTECH 사용자 ID (또는 REGTECH_ID 환경변수)'
    )

    parser.add_argument(
        '--password',
        help='REGTECH 비밀번호 (또는 REGTECH_PW 환경변수)'
    )

    args = parser.parse_args()

    # 다운로더 실행
    downloader = RegtechAdvisoryDownloader(output_dir=args.output)

    # 인증 정보 설정
    if args.username and args.password:
        os.environ['REGTECH_ID'] = args.username
        os.environ['REGTECH_PW'] = args.password

    # 실행
    try:
        downloader.run(format=args.format, max_pages=args.max_pages)
    except KeyboardInterrupt:
        log_warning("\nDownload interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
