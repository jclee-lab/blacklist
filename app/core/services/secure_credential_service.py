"""
🔐 보안 인증정보 관리 서비스
REGTECH Blacklist Intelligence Platform - Secure Credential Management Service
Version: 1.0.0 (September 2025)

데이터베이스 기반 암호화된 인증정보 저장 및 관리
- AES-256 암호화 기반 안전한 저장
- 환경변수 기반 암호화 키 관리
- 다중 서비스 지원 (REGTECH, CloudFlare, 기타)
- 자동 암호화/복호화 처리
- 활성/비활성 상태 관리
"""

import json
import os
import base64
import hashlib
from datetime import datetime
from typing import Dict, Optional, List, Any
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

import logging

logger = logging.getLogger(__name__)


class SecureCredentialService:
    """보안 인증정보 관리 서비스 - 암호화된 DB 저장"""

    def __init__(self):
        """서비스 초기화"""
        self._cipher_suite = None
        self._salt = None
        self._setup_encryption()
        
    def _setup_encryption(self):
        """암호화 키 설정"""
        try:
            # 환경변수에서 마스터 키 획득
            master_key = os.getenv("CREDENTIAL_MASTER_KEY")
            if not master_key:
                # 기본 키 생성 (프로덕션에서는 환경변수로 설정 필요)
                master_key = "default-blacklist-credential-master-key-2025"
                logger.warning("⚠️ 기본 마스터 키 사용. 프로덕션에서는 CREDENTIAL_MASTER_KEY 환경변수 설정 필요")
            
            # Salt 생성 (고정값으로 일관성 유지)
            self._salt = b'blacklist-regtech-salt-2025'
            
            # PBKDF2를 사용한 키 파생
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self._salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
            self._cipher_suite = Fernet(key)
            
            logger.info("🔐 암호화 시스템 초기화 완료")
            
        except Exception as e:
            logger.error(f"❌ 암호화 시스템 초기화 실패: {e}")
            raise

    def _get_database_connection(self):
        """데이터베이스 연결 획득"""
        try:
            from .database_service import db_service
            return db_service.get_connection()
        except ImportError:
            # 서비스 직접 임포트 시도
            from core.services.database_service import DatabaseService
            db_service = DatabaseService()
            return db_service.get_connection()

    def _encrypt_data(self, data: str) -> str:
        """데이터 암호화"""
        try:
            encrypted = self._cipher_suite.encrypt(data.encode())
            return base64.b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"❌ 데이터 암호화 실패: {e}")
            raise

    def _decrypt_data(self, encrypted_data: str) -> str:
        """데이터 복호화"""
        try:
            decoded = base64.b64decode(encrypted_data.encode())
            decrypted = self._cipher_suite.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"❌ 데이터 복호화 실패: {e}")
            raise

    def save_credentials(
        self, 
        service_name: str, 
        username: str, 
        password: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        암호화된 인증정보 저장
        
        Args:
            service_name: 서비스명 (REGTECH, CLOUDFLARE 등)
            username: 사용자명
            password: 비밀번호
            config: 추가 설정 정보
            
        Returns:
            bool: 저장 성공 여부
        """
        try:
            # 데이터 준비
            credential_data = {
                "username": username,
                "password": password,
                "config": config or {},
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            # JSON 직렬화 및 암호화
            json_data = json.dumps(credential_data)
            encrypted_data = self._encrypt_data(json_data)
            
            # 데이터베이스 저장
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            # UPSERT 쿼리 실행
            cursor.execute("""
                INSERT INTO collection_credentials 
                (service_name, username, password, config, encrypted, is_active, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (service_name) 
                DO UPDATE SET
                    username = EXCLUDED.username,
                    password = EXCLUDED.password,
                    config = EXCLUDED.config,
                    encrypted = EXCLUDED.encrypted,
                    is_active = EXCLUDED.is_active,
                    updated_at = EXCLUDED.updated_at
            """, (
                service_name.upper(),
                username,  # 평문 저장 (호환성)
                encrypted_data,  # 암호화된 패스워드
                json.dumps(config or {}),
                True,  # encrypted 플래그
                True,  # is_active
                datetime.now()
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"✅ {service_name} 인증정보 암호화 저장 완료: {username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ {service_name} 인증정보 저장 실패: {e}")
            return False

    def get_credentials(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        암호화된 인증정보 조회
        
        Args:
            service_name: 서비스명
            
        Returns:
            Dict: 복호화된 인증정보 또는 None
        """
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT username, password, config, encrypted, created_at, updated_at
                FROM collection_credentials
                WHERE service_name = %s AND is_active = true
            """, (service_name.upper(),))
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not result:
                logger.warning(f"⚠️ {service_name} 인증정보를 찾을 수 없음")
                return None
                
            username, password, config, encrypted, created_at, updated_at = result
            
            if encrypted:
                # 암호화된 데이터 복호화
                try:
                    decrypted_json = self._decrypt_data(password)
                    credential_data = json.loads(decrypted_json)
                    
                    return {
                        "username": credential_data.get("username", username),
                        "password": credential_data.get("password", ""),
                        "config": credential_data.get("config", {}),
                        "service_name": service_name,
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "encrypted": True
                    }
                except Exception as decrypt_error:
                    logger.error(f"❌ {service_name} 인증정보 복호화 실패: {decrypt_error}")
                    return None
            else:
                # 평문 데이터 (기존 호환성)
                return {
                    "username": username,
                    "password": password,
                    "config": config if config else {},
                    "service_name": service_name,
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "encrypted": False
                }
                
        except Exception as e:
            logger.error(f"❌ {service_name} 인증정보 조회 실패: {e}")
            return None

    def list_credentials(self) -> List[Dict[str, Any]]:
        """모든 활성 인증정보 목록 조회 (비밀번호 제외)"""
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT service_name, username, encrypted, created_at, updated_at, is_active
                FROM collection_credentials
                WHERE is_active = true
                ORDER BY service_name
            """)
            
            results = cursor.fetchall()
            cursor.close()
            conn.close()
            
            credentials_list = []
            for row in results:
                service_name, username, encrypted, created_at, updated_at, is_active = row
                credentials_list.append({
                    "service_name": service_name,
                    "username": username,
                    "encrypted": bool(encrypted),
                    "has_password": bool(username),  # username이 있으면 password도 있다고 가정
                    "created_at": created_at,
                    "updated_at": updated_at,
                    "is_active": is_active
                })
            
            return credentials_list
            
        except Exception as e:
            logger.error(f"❌ 인증정보 목록 조회 실패: {e}")
            return []

    def delete_credentials(self, service_name: str) -> bool:
        """인증정보 삭제 (논리적 삭제 - is_active = false)"""
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE collection_credentials
                SET is_active = false, updated_at = %s
                WHERE service_name = %s
            """, (datetime.now(), service_name.upper()))
            
            deleted_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"✅ {service_name} 인증정보 삭제 완료")
                return True
            else:
                logger.warning(f"⚠️ {service_name} 인증정보가 존재하지 않음")
                return False
                
        except Exception as e:
            logger.error(f"❌ {service_name} 인증정보 삭제 실패: {e}")
            return False

    def activate_credentials(self, service_name: str) -> bool:
        """인증정보 활성화"""
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE collection_credentials
                SET is_active = true, updated_at = %s
                WHERE service_name = %s
            """, (datetime.now(), service_name.upper()))
            
            updated_count = cursor.rowcount
            conn.commit()
            cursor.close()
            conn.close()
            
            if updated_count > 0:
                logger.info(f"✅ {service_name} 인증정보 활성화 완료")
                return True
            else:
                logger.warning(f"⚠️ {service_name} 인증정보가 존재하지 않음")
                return False
                
        except Exception as e:
            logger.error(f"❌ {service_name} 인증정보 활성화 실패: {e}")
            return False

    def validate_credentials(self, service_name: str) -> Dict[str, Any]:
        """인증정보 유효성 검증"""
        try:
            credentials = self.get_credentials(service_name)
            
            if not credentials:
                return {
                    "valid": False,
                    "error": "인증정보가 존재하지 않음",
                    "service_name": service_name
                }
            
            username = credentials.get("username", "").strip()
            password = credentials.get("password", "").strip()
            
            if not username or not password:
                return {
                    "valid": False,
                    "error": "사용자명 또는 비밀번호가 비어있음",
                    "service_name": service_name,
                    "username": username
                }
            
            return {
                "valid": True,
                "service_name": service_name,
                "username": username,
                "encrypted": credentials.get("encrypted", False),
                "created_at": credentials.get("created_at"),
                "updated_at": credentials.get("updated_at")
            }
            
        except Exception as e:
            logger.error(f"❌ {service_name} 인증정보 검증 실패: {e}")
            return {
                "valid": False,
                "error": str(e),
                "service_name": service_name
            }

    def migrate_existing_credentials(self) -> Dict[str, Any]:
        """기존 평문 인증정보를 암호화된 형태로 마이그레이션"""
        try:
            conn = self._get_database_connection()
            cursor = conn.cursor()
            
            # 평문으로 저장된 인증정보 조회
            cursor.execute("""
                SELECT service_name, username, password, config
                FROM collection_credentials
                WHERE (encrypted = false OR encrypted IS NULL)
                AND is_active = true
                AND password IS NOT NULL
                AND password != ''
            """)
            
            results = cursor.fetchall()
            migrated_count = 0
            errors = []
            
            for row in results:
                service_name, username, password, config = row
                
                try:
                    # 새로운 암호화 방식으로 저장
                    if self.save_credentials(
                        service_name,
                        username,
                        password,
                        config if config else {}
                    ):
                        migrated_count += 1
                        logger.info(f"✅ {service_name} 인증정보 마이그레이션 완료")
                    else:
                        errors.append(f"{service_name}: 저장 실패")
                        
                except Exception as e:
                    errors.append(f"{service_name}: {str(e)}")
                    logger.error(f"❌ {service_name} 마이그레이션 실패: {e}")
            
            cursor.close()
            conn.close()
            
            return {
                "success": True,
                "migrated_count": migrated_count,
                "total_found": len(results),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"❌ 인증정보 마이그레이션 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "migrated_count": 0
            }


# 싱글톤 인스턴스 생성
secure_credential_service = SecureCredentialService()


# REGTECH 전용 헬퍼 함수들
def save_regtech_credentials(username: str, password: str) -> bool:
    """REGTECH 인증정보 저장"""
    config = {
        "base_url": "https://regtech.fsec.or.kr",
        "login_url": "/login/loginProcess",
        "advisory_url": "/advisory/advisory01_search",
        "timeout_seconds": 30,
        "max_pages": 100,
        "items_per_page": 50,
        "request_delay_seconds": 1
    }
    return secure_credential_service.save_credentials("REGTECH", username, password, config)


def get_regtech_credentials() -> Optional[Dict[str, Any]]:
    """REGTECH 인증정보 조회"""
    return secure_credential_service.get_credentials("REGTECH")


def validate_regtech_credentials() -> Dict[str, Any]:
    """REGTECH 인증정보 유효성 검증"""
    return secure_credential_service.validate_credentials("REGTECH")


def delete_regtech_credentials() -> bool:
    """REGTECH 인증정보 삭제"""
    return secure_credential_service.delete_credentials("REGTECH")


if __name__ == "__main__":
    # 테스트 코드
    print("🔐 보안 인증정보 서비스 테스트")
    
    # 테스트 저장
    test_result = save_regtech_credentials("test_user", "test_password")
    print(f"저장 테스트: {'✅ 성공' if test_result else '❌ 실패'}")
    
    # 테스트 조회
    credentials = get_regtech_credentials()
    if credentials:
        print(f"조회 테스트: ✅ 성공 - {credentials['username']}")
    else:
        print("조회 테스트: ❌ 실패")
    
    # 유효성 검증
    validation = validate_regtech_credentials()
    print(f"검증 테스트: {'✅ 유효' if validation['valid'] else '❌ 무효'}")
    
    # 마이그레이션 테스트
    migration_result = secure_credential_service.migrate_existing_credentials()
    print(f"마이그레이션: {migration_result['migrated_count']}개 완료")