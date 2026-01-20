#!/usr/bin/env python3
"""
인증정보 관리 서비스
웹 UI에서 입력한 REGTECH 인증정보를 안전하게 저장하고 로드
"""

import os
import json
import logging
from pathlib import Path
from cryptography.fernet import Fernet
import base64
from datetime import datetime

logger = logging.getLogger(__name__)


class CredentialService:
    """인증정보 관리 서비스 - 데이터베이스 기반"""

    def __init__(self, db_service=None):
        """인증정보 서비스 초기화 - 환경변수 기반 암호화 키 사용"""
        self.db_service = db_service

        # 파일 경로 초기화
        self.credentials_file = Path("/app/data/credentials.enc")
        self.key_file = Path("/app/data/credential.key")

        # 데이터 디렉토리 생성
        self.credentials_file.parent.mkdir(parents=True, exist_ok=True)

        # 환경변수에서 암호화 키 가져오기 (없으면 생성하여 저장)
        import os

        encryption_key = os.getenv("CREDENTIAL_ENCRYPTION_KEY")

        if not encryption_key:
            # 새 키 생성
            key = Fernet.generate_key()
            encryption_key = key.decode()
            logger.warning(
                "⚠️ 새로운 암호화 키가 생성되었습니다. 환경변수 CREDENTIAL_ENCRYPTION_KEY에 저장하세요."
            )
            logger.warning(f"CREDENTIAL_ENCRYPTION_KEY={encryption_key}")

        try:
            self.cipher_suite = Fernet(encryption_key.encode())
            logger.info("✅ 암호화 키 로드 완료")
        except Exception as e:
            logger.error(f"❌ 암호화 키 로드 실패: {e}")
            # 폴백: 새 키 생성
            key = Fernet.generate_key()
            self.cipher_suite = Fernet(key)
            logger.warning("⚠️ 폴백으로 새 암호화 키 생성됨")

        self._setup_database()

    def _setup_database(self):
        """데이터베이스 테이블 초기화"""
        try:
            if not self.db_service:
                return

            conn = self.db_service.get_connection()
            cursor = conn.cursor()

            # credentials 테이블 생성
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS credentials (
                    id SERIAL PRIMARY KEY,
                    service_name VARCHAR(50) NOT NULL,
                    encrypted_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(service_name)
                )
            """
            )

            conn.commit()
            cursor.close()
            conn.close()

        except Exception as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")

    def _ensure_key(self):
        """암호화 키 생성 또는 로드"""
        try:
            # 프로덕션 환경: 환경변수에서 키 로드 시도
            env_key = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
            if env_key:
                self.key = base64.b64decode(env_key.encode())
                self.cipher_suite = Fernet(self.key)
                logger.info("🔑 환경변수에서 암호화 키 로드됨")
                return

            # 파일에서 키 로드 시도 (개발환경)
            if self.key_file.exists():
                with open(self.key_file, "rb") as f:
                    self.key = f.read()
                self.cipher_suite = Fernet(self.key)
                logger.info("🔑 파일에서 암호화 키 로드됨")
                return

            # 키 생성 시도 (파일 시스템 권한이 있는 경우)
            try:
                key = Fernet.generate_key()
                with open(self.key_file, "wb") as f:
                    f.write(key)
                self.key = key
                self.cipher_suite = Fernet(self.key)
                logger.info("🔑 새 암호화 키 생성 및 파일 저장됨")
                return
            except (PermissionError, OSError):
                logger.warning("⚠️ 파일 시스템 권한 없음, 임시 키 생성")

            # 모든 방법 실패시 임시 키 생성 (메모리 전용)
            self.key = Fernet.generate_key()
            self.cipher_suite = Fernet(self.key)
            logger.warning("⚠️ 임시 암호화 키 생성됨 (재시작시 기존 데이터 복호화 불가)")

        except Exception as e:
            logger.error(f"❌ 암호화 키 처리 실패: {e}")
            raise

    def _ensure_table(self):
        """인증정보 테이블 생성"""
        try:
            if not self.db_service:
                logger.warning("db_service not available, skipping table creation")
                return

            conn = self.db_service.get_connection()
            cursor = conn.cursor()

            # 인증정보 테이블 생성
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS credentials (
                    id SERIAL PRIMARY KEY,
                    service_name VARCHAR(50) NOT NULL,
                    encrypted_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(service_name)
                )
            """
            )

            conn.commit()
            cursor.close()
            conn.close()

            logger.info("✅ 인증정보 테이블 확인/생성 완료")

        except Exception as e:
            logger.warning(f"⚠️ 데이터베이스 테이블 생성 실패, 파일 기반으로 대체: {e}")

    def save_credentials(self, regtech_id, regtech_pw):
        """인증정보 저장 (데이터베이스에 암호화)"""
        try:
            credentials = {
                "regtech_id": regtech_id,
                "regtech_pw": regtech_pw,
                "saved_at": str(datetime.now()),
                "version": "1.0",
            }

            # JSON으로 직렬화 및 암호화
            json_data = json.dumps(credentials).encode()
            encrypted_data = self.cipher_suite.encrypt(json_data)
            encrypted_str = base64.b64encode(encrypted_data).decode()

            # 데이터베이스에 저장 시도
            try:
                if not self.db_service:
                    raise Exception("db_service not available")
                conn = self.db_service.get_connection()
                cursor = conn.cursor()

                # UPSERT 쿼리 (PostgreSQL 9.5+)
                cursor.execute(
                    """
                    INSERT INTO credentials (service_name, encrypted_data, updated_at)
                    VALUES (%s, %s, NOW())
                    ON CONFLICT (service_name)
                    DO UPDATE SET
                        encrypted_data = EXCLUDED.encrypted_data,
                        updated_at = NOW()
                """,
                    ("regtech", encrypted_str),
                )

                conn.commit()
                cursor.close()
                conn.close()

                logger.info(f"✅ 인증정보 데이터베이스 저장 완료: {regtech_id}")

                # 백업으로 파일에도 저장 (실패해도 DB 저장 성공이면 성공 처리)
                try:
                    with open(self.credentials_file, "wb") as f:
                        f.write(encrypted_data)
                    logger.info("✅ 파일 백업 저장 완료")
                except (PermissionError, OSError) as file_error:
                    logger.warning(f"⚠️ 파일 백업 실패 (DB 저장은 성공): {file_error}")

                return True

            except Exception as db_error:
                logger.warning(f"⚠️ 데이터베이스 저장 실패, 파일로만 저장: {db_error}")

                # 파일로 저장 (백업)
                try:
                    with open(self.credentials_file, "wb") as f:
                        f.write(encrypted_data)
                    logger.info(f"✅ 인증정보 파일 저장 완료: {regtech_id}")
                    return True
                except (PermissionError, OSError) as file_error:
                    logger.error(
                        f"❌ 파일 저장도 실패 - 프로덕션 환경에서는 임시 메모리 저장: {file_error}"
                    )
                    # 프로덕션 환경에서는 메모리에 임시 저장
                    self._temp_credentials = credentials
                    logger.warning("⚠️ 메모리에 임시 저장됨 (재시작시 소실)")
                    return True

        except Exception as e:
            logger.error(f"❌ 인증정보 저장 실패: {e}")
            return False

    def load_credentials(self):
        """저장된 인증정보 로드 (데이터베이스 우선) - 평문 저장 방식"""
        # 1단계: 데이터베이스에서 로드 시도
        try:
            if not self.db_service:
                raise Exception("db_service not available")
            conn = self.db_service.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT encrypted_data, updated_at
                FROM credentials
                WHERE service_name = %s
            """,
                ("regtech",),
            )

            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result:
                json_str, updated_at = result

                # 평문 JSON으로 저장된 데이터 직접 파싱
                credentials = json.loads(json_str)

                logger.info(
                    f"✅ 인증정보 데이터베이스 로드 완료: {credentials.get('regtech_id', 'N/A')}"
                )
                return credentials

        except Exception as db_error:
            logger.warning(f"⚠️ 데이터베이스 로드 실패, 파일에서 시도: {db_error}")

        # 2단계: 파일에서 로드 시도 (백업) - 암호화된 파일일 수 있음
        try:
            if not self.credentials_file.exists():
                logger.warning("⚠️ 저장된 인증정보가 없습니다 (DB와 파일 모두)")
                return None

            # 파일 읽기
            with open(self.credentials_file, "rb") as f:
                file_data = f.read()

            try:
                # 먼저 암호화된 데이터로 시도
                decrypted_data = self.cipher_suite.decrypt(file_data)
                credentials = json.loads(decrypted_data.decode())
            except BaseException:
                # 암호화 실패시 평문으로 시도
                credentials = json.loads(file_data.decode())

            logger.info(
                f"✅ 인증정보 파일 로드 완료: {credentials.get('regtech_id', 'N/A')}"
            )
            return credentials

        except Exception as e:
            logger.error(f"❌ 인증정보 로드 실패: {e}")
            return None

    def get_credentials(self):
        """인증정보 반환 - collection_credentials 테이블에서 직접 로드"""
        try:
            if not self.db_service:
                logger.warning("db_service not available")
                return {}
            conn = self.db_service.get_connection()
            cursor = conn.cursor()

            # collection_credentials 테이블에서 직접 인증정보 조회
            cursor.execute(
                """
                SELECT username, password
                FROM collection_credentials
                WHERE service_name = 'REGTECH' AND is_active = true
                """
            )

            result = cursor.fetchone()
            cursor.close()
            self.db_service.return_connection(conn)

            if result:
                regtech_id, regtech_pw = result
                logger.info(
                    f"✅ collection_credentials에서 인증정보 로드: {regtech_id}"
                )
                return {"regtech_id": regtech_id, "regtech_pw": regtech_pw}
            else:
                logger.warning("⚠️ collection_credentials에서 인증정보를 찾을 수 없음")
                return {}

        except Exception as e:
            logger.error(f"❌ 인증정보 로드 실패: {e}")
            return {}

    def has_credentials(self):
        """저장된 인증정보 존재 여부 - collection_credentials 테이블 확인"""
        try:
            if not self.db_service:
                logger.warning("db_service not available")
                return False
            conn = self.db_service.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) FROM collection_credentials
                WHERE service_name = 'REGTECH' AND is_active = true
                AND username IS NOT NULL AND password IS NOT NULL
                """
            )

            count = cursor.fetchone()[0]
            cursor.close()
            self.db_service.return_connection(conn)

            return count > 0

        except Exception as e:
            logger.error(f"❌ 인증정보 존재 확인 실패: {e}")
            return False

    def clear_credentials(self):
        """저장된 인증정보 삭제 (데이터베이스와 파일 모두)"""
        deleted_any = False

        # 1단계: 데이터베이스에서 삭제
        try:
            if not self.db_service:
                raise Exception("db_service not available")
            conn = self.db_service.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                DELETE FROM credentials WHERE service_name = %s
            """,
                ("regtech",),
            )

            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()

            if deleted_count > 0:
                logger.info("✅ 데이터베이스 인증정보 삭제 완료")
                deleted_any = True

        except Exception as db_error:
            logger.warning(f"⚠️ 데이터베이스 삭제 실패: {db_error}")

        # 2단계: 파일 삭제
        try:
            if self.credentials_file.exists():
                self.credentials_file.unlink()
                logger.info("✅ 파일 인증정보 삭제 완료")
                deleted_any = True
        except Exception as e:
            logger.error(f"❌ 파일 삭제 실패: {e}")

        return deleted_any

    def save_regtech_credentials(self, username, password):
        """REGTECH 인증정보 직접 저장"""
        try:
            result = self.save_credentials(username, password)
            logger.info(f"✅ REGTECH 인증정보 저장 완료: {username}")
            return result

        except Exception as e:
            logger.error(f"❌ REGTECH 인증정보 저장 실패: {e}")
            return False


# 전역 인스턴스 대체
# credential_service = CredentialService()
from flask import current_app
from werkzeug.local import LocalProxy

credential_service = LocalProxy(lambda: current_app.extensions["credential_service"])


if __name__ == "__main__":
    # 테스트 코드
    from datetime import datetime

    logger.info("🔧 인증정보 서비스 테스트")

    # 저장 테스트 (실제 운영 인증정보 필요)
    test_id = os.getenv("REGTECH_ID")
    test_pw = os.getenv("REGTECH_PW")

    if not test_id or not test_pw:
        logger.warning(
            "❌ 테스트를 위한 환경변수가 설정되지 않음: REGTECH_ID, REGTECH_PW"
        )
        logger.info("   환경변수를 설정하거나 웹 UI를 통해 인증정보를 저장하세요.")
        exit(1)

    save_result = credential_service.save_credentials(test_id, test_pw)
    logger.info(f"저장 결과: {save_result}")

    # 로드 테스트
    loaded_creds = credential_service.get_credentials()
    logger.info(f"로드된 인증정보: {loaded_creds}")

    # 존재 확인
    has_creds = credential_service.has_credentials()
    logger.info(f"인증정보 존재: {has_creds}")
