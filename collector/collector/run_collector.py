#!/usr/bin/env python3
"""
Blacklist Collector Main Entry Point
블랙리스트 수집기 메인 실행 스크립트
"""

import logging
import signal
import sys
import threading
import time
from datetime import datetime
from collector.config import CollectorConfig
from collector.scheduler import scheduler
from collector.health_server import start_health_server
from core.database import db_service

# Monitoring scheduler is optional - import only if needed
try:
    from monitoring_scheduler import monitoring_scheduler

    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    monitoring_scheduler = None


# 로깅 설정
def setup_logging():
    """로깅 설정"""
    log_format = CollectorConfig.LOG_FORMAT
    log_level = getattr(logging, CollectorConfig.LOG_LEVEL.upper(), logging.INFO)

    # 기본 로거 설정
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("/app/logs/collector.log", encoding="utf-8"),
        ],
    )

    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("flask").setLevel(logging.WARNING)


class CollectorApplication:
    """수집기 애플리케이션 클래스"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.running = False
        self.health_server_thread = None
        self.startup_time = datetime.now()
        self.monitoring_enabled = True  # 모니터링 활성화 플래그

    def start(self):
        """애플리케이션 시작"""
        try:
            self.logger.info("🚀 Starting Blacklist Collector")
            self.logger.info(f"📅 Startup time: {self.startup_time}")
            self.logger.info(f"🔧 Configuration: {CollectorConfig.to_dict()}")

            # 시그널 핸들러 등록
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            # 데이터베이스 연결 테스트
            if not self._test_database_connection():
                self.logger.error("❌ Database connection failed - exiting")
                sys.exit(1)

            # 헬스체크 서버 시작
            self._start_health_server()

            # 수집 스케줄러 시작
            self._start_scheduler()

            self.running = True
            self.logger.info("✅ Blacklist Collector started successfully")

            # 메인 루프
            self._main_loop()

        except Exception as e:
            self.logger.error(f"❌ Failed to start collector: {e}")
            sys.exit(1)

    def stop(self):
        """애플리케이션 중지"""
        if not self.running:
            return

        self.logger.info("🛑 Stopping Blacklist Collector")
        self.running = False

        # 스케줄러 중지
        try:
            scheduler.stop()
            self.logger.info("✅ Scheduler stopped")
        except Exception as e:
            self.logger.error(f"❌ Error stopping scheduler: {e}")

        # 헬스 서버는 데몬 스레드로 자동 종료됨

        self.logger.info("✅ Blacklist Collector stopped")

    def _test_database_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            self.logger.info("🔍 Testing database connection")

            if db_service.test_connection():
                self.logger.info("✅ Database connection successful")

                # 기본 통계 출력
                stats = db_service.get_collection_stats()
                self.logger.info(f"📊 Current DB stats: {stats}")

                return True
            else:
                self.logger.error("❌ Database connection failed")
                return False

        except Exception as e:
            self.logger.error(f"❌ Database connection test error: {e}")
            return False

    def _start_health_server(self):
        """헬스체크 서버 시작"""
        try:
            self.logger.info("🏥 Starting health check server")

            self.health_server_thread = threading.Thread(
                target=start_health_server, daemon=True
            )
            self.health_server_thread.start()

            # 서버 시작 대기
            time.sleep(2)
            self.logger.info(
                f"✅ Health server started on port {CollectorConfig.HEALTH_CHECK_PORT}"
            )

        except Exception as e:
            self.logger.error(f"❌ Failed to start health server: {e}")
            raise

    def _start_scheduler(self):
        """스케줄러 시작"""
        try:
            self.logger.info("⏰ Starting collection scheduler")
            scheduler.start()
            self.logger.info("✅ Scheduler started")

        except Exception as e:
            self.logger.error(f"❌ Failed to start scheduler: {e}")
            raise

    def _main_loop(self):
        """메인 루프"""
        self.logger.info("🔄 Entering main loop")

        try:
            while self.running:
                # 상태 체크
                self._periodic_health_check()

                # 1분 대기
                time.sleep(60)

        except KeyboardInterrupt:
            self.logger.info("⌨️ Keyboard interrupt received")
        except Exception as e:
            self.logger.error(f"❌ Main loop error: {e}")
        finally:
            self.stop()

    def _periodic_health_check(self):
        """주기적 헬스체크"""
        try:
            # 데이터베이스 상태 확인
            db_healthy = db_service.test_connection()

            # 스케줄러 상태 확인
            scheduler_status = scheduler.get_status()

            if not db_healthy:
                self.logger.warning("⚠️ Database connection issue detected")

            if not scheduler_status["running"]:
                self.logger.warning("⚠️ Scheduler not running")

            # 통계 정보 로깅 (매 10분마다)
            current_minute = datetime.now().minute
            if current_minute % 10 == 0:
                stats = db_service.get_collection_stats()
                self.logger.info(f"📊 Periodic stats: {stats}")

        except Exception as e:
            self.logger.error(f"❌ Health check error: {e}")

    def _signal_handler(self, signum, frame):
        """시그널 핸들러"""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"📡 Received signal: {signal_name}")
        self.stop()
        sys.exit(0)


def main():
    """메인 함수 - REGTECH 단일 소스 수집"""
    # 로깅 설정
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("🚀 BLACKLIST COLLECTOR STARTING")
    logger.info("📡 REGTECH Single Source Collection")
    logger.info("=" * 60)

    try:
        # 애플리케이션 실행
        app = CollectorApplication()
        app.start()

    except KeyboardInterrupt:
        logger.info("⌨️ Application interrupted by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        sys.exit(1)
    finally:
        logger.info("👋 Blacklist Collector shutdown complete")


if __name__ == "__main__":
    main()
