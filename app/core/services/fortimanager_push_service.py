"""
FortiManager Push Service (Real-time)

Purpose:
    - PostgreSQL NOTIFY/LISTEN으로 blacklist 변경 감지
    - 변경 시 즉시 FortiManager에 Push
    - Cron 없이 실시간 동기화

Usage:
    python -m core.services.fortimanager_push_service
"""

import os
import time
import requests
import psycopg2
import select
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FortiManagerPushService:
    """FortiManager 실시간 Push 서비스"""

    def __init__(self, db_service=None):
        """
        Initialize FortiManager push service

        Args:
            db_service: DatabaseService instance for connection pool access

        Note:
            This service maintains a separate persistent connection (self.db_conn)
            for PostgreSQL LISTEN/NOTIFY functionality. The db_service is available
            for any other database queries needed in the future.
        """
        self.db_service = db_service
        self.fmg_host = os.getenv("FMG_HOST")
        self.fmg_user = os.getenv("FMG_USER", "admin")
        self.fmg_pass = os.getenv("FMG_PASS")
        self.fmg_adom = os.getenv("FMG_ADOM", "root")
        self.api_url = os.getenv(
            "API_URL", "http://localhost:443/api/fortinet/threat-feed?format=text"
        )

        self.session_id: Optional[str] = None
        # Persistent connection for PostgreSQL LISTEN/NOTIFY (required for real-time notifications)
        self.db_conn = None
        self.last_update = time.time()

    def connect_database(self):
        """
        PostgreSQL 연결 및 LISTEN 설정

        Note: Creates a persistent connection for LISTEN/NOTIFY.
        This is a special case that requires a connection outside the pool.
        """
        if self.db_service:
            # Use DatabaseService to create a raw connection (consistent config)
            self.db_conn = self.db_service.create_raw_connection()
        else:
            # Fallback to manual connection (legacy support)
            db_host = os.getenv("POSTGRES_HOST", "blacklist-postgres")
            db_name = os.getenv("POSTGRES_DB", "blacklist")
            db_user = os.getenv("POSTGRES_USER", "postgres")
            db_pass = os.getenv("POSTGRES_PASSWORD")

            self.db_conn = psycopg2.connect(
                host=db_host, database=db_name, user=db_user, password=db_pass
            )

        self.db_conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        # LISTEN 설정
        cursor = self.db_conn.cursor()
        cursor.execute("LISTEN blacklist_changes;")
        logger.info("✅ PostgreSQL LISTEN started: blacklist_changes")

    def login_fortimanager(self) -> bool:
        """FortiManager 로그인"""
        if not self.fmg_host or not self.fmg_pass:
            logger.error("FMG_HOST or FMG_PASS not configured")
            return False

        url = f"https://{self.fmg_host}/jsonrpc"
        payload = {
            "method": "exec",
            "params": [
                {
                    "url": "/sys/login/user",
                    "data": {"user": self.fmg_user, "passwd": self.fmg_pass},
                }
            ],
            "id": 1,
        }

        try:
            response = requests.post(url, json=payload, verify=False, timeout=10)
            result = response.json()

            if result.get("result", [{}])[0].get("status", {}).get("code") == 0:
                self.session_id = result.get("session")
                logger.info(
                    f"✅ FortiManager login successful (Session: {self.session_id[:10]}...)"
                )
                return True
            else:
                logger.error(f"❌ Login failed: {result}")
                return False
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False

    def fetch_blacklist(self) -> Optional[str]:
        """Flask API에서 블랙리스트 가져오기"""
        try:
            response = requests.get(self.api_url, timeout=10)
            if response.status_code == 200:
                ip_list = response.text.strip()
                ip_count = len(ip_list.split("\n"))
                logger.info(f"✅ Fetched {ip_count} IPs from API")
                return ip_list
            else:
                logger.error(f"❌ API error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ API fetch error: {e}")
            return None

    def upload_to_fortimanager(self, ip_list: str) -> bool:
        """FortiManager Hosted Resource 업데이트"""
        if not self.session_id:
            if not self.login_fortimanager():
                return False

        url = f"https://{self.fmg_host}/jsonrpc"

        # Base64 인코딩
        import base64

        file_content = base64.b64encode(ip_list.encode()).decode()

        # Update External Resource
        payload = {
            "method": "update",
            "params": [
                {
                    "url": f"/pm/config/adom/{self.fmg_adom}/obj/system/external-resource/NXTD-Blacklist-Hosted",
                    "data": {
                        "resource": f"data:text/plain;base64,{file_content}",
                        "comments": f"Auto-updated by Push Service - {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    },
                }
            ],
            "session": self.session_id,
            "id": 2,
        }

        try:
            response = requests.post(url, json=payload, verify=False, timeout=10)
            result = response.json()

            status_code = result.get("result", [{}])[0].get("status", {}).get("code")

            if status_code == 0:
                logger.info("✅ FortiManager update successful")
                return True
            else:
                logger.error(f"❌ Update failed: {result}")
                # Session expired? Try re-login
                if status_code == -11:
                    self.session_id = None
                    return self.upload_to_fortimanager(ip_list)
                return False
        except Exception as e:
            logger.error(f"❌ Upload error: {e}")
            return False

    def handle_change_notification(self, payload: str):
        """DB 변경 알림 처리

        Note: INSERT/UPDATE/DELETE 모두 전체 재동기화 방식
              - 삭제된 IP도 자동으로 FortiManager에서 제거됨
        """
        logger.info(f"🔔 Database change detected: {payload}")

        # Rate limiting (1분에 1번만)
        now = time.time()
        if now - self.last_update < 60:
            logger.info("⏳ Rate limited (wait 60s)")
            return

        self.last_update = now

        # Fetch CURRENT state and Upload
        # 현재 DB 상태를 전체 동기화 (삭제된 IP는 자동으로 제외됨)
        ip_list = self.fetch_blacklist()
        if ip_list:
            self.upload_to_fortimanager(ip_list)

    def run(self):
        """메인 루프"""
        logger.info("Starting FortiManager Push Service...")

        # Database 연결
        self.connect_database()

        # FortiManager 로그인
        self.login_fortimanager()

        logger.info("👂 Listening for database changes...")

        try:
            while True:
                # Wait for notifications (timeout 30s)
                if select.select([self.db_conn], [], [], 30) == ([], [], []):
                    # No notification, check connection
                    continue

                self.db_conn.poll()
                while self.db_conn.notifies:
                    notify = self.db_conn.notifies.pop(0)
                    self.handle_change_notification(notify.payload)

        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            if self.db_conn:
                self.db_conn.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # Initialize DatabaseService for standalone execution
    try:
        from .database_service import DatabaseService

        db_service = DatabaseService()
        logger.info("✅ DatabaseService initialized for FortiManager Push Service")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize DatabaseService: {e}")
        db_service = None

    service = FortiManagerPushService(db_service=db_service)
    service.run()

from flask import current_app
from werkzeug.local import LocalProxy

fortimanager_service = LocalProxy(
    lambda: current_app.extensions["fortimanager_service"]
)
