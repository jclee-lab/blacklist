"""
Health Server for Multi-Collector Scheduler
Provides HTTP health endpoint at :8545/health
"""
import json
from datetime import datetime
from flask import Flask, jsonify
from waitress import serve
import threading
import logging
from collections import deque

logger = logging.getLogger(__name__)

# Global log buffer for recent logs (circular buffer)
LOG_BUFFER = deque(maxlen=100)

class LogBufferHandler(logging.Handler):
    """Custom log handler that stores logs in memory buffer"""

    def emit(self, record):
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'line': record.lineno
            }
            LOG_BUFFER.append(log_entry)
        except Exception:
            self.handleError(record)

class HealthServer:
    """Simple health check server for multi-collector"""

    def __init__(self, collectors_ref, scheduler_ref=None, port=8545):
        self.app = Flask(__name__)
        self.collectors = collectors_ref  # Reference to collectors dict
        self.scheduler = scheduler_ref  # Reference to scheduler instance
        self.port = port
        self.thread = None
        
        # Setup routes
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'collectors': self._get_collector_status()
            })
        
        @self.app.route('/status', methods=['GET'])
        def status():
            return jsonify({
                'collectors': self._get_collector_status(),
                'timestamp': datetime.now().isoformat()
            })

        @self.app.route('/logs', methods=['GET'])
        def logs():
            """Get recent logs from memory buffer"""
            return jsonify({
                'logs': list(LOG_BUFFER),
                'count': len(LOG_BUFFER),
                'timestamp': datetime.now().isoformat()
            })

        @self.app.route('/api/test-auth/<source>', methods=['POST'])
        def test_authentication(source):
            """Test authentication for a specific source"""
            try:
                source_upper = source.upper()

                if source_upper not in ["REGTECH", "SECUDIUM"]:
                    return jsonify({
                        "success": False,
                        "error": f"Invalid source: {source_upper}"
                    }), 400

                # Get credentials from database
                from core.database import DatabaseService

                db = DatabaseService()
                with db.get_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        SELECT username, password, enabled
                        FROM collection_credentials
                        WHERE service_name = %s
                    """, (source_upper,))

                    row = cursor.fetchone()
                    cursor.close()

                if not row:
                    return jsonify({
                        "success": False,
                        "error": f"No credentials found for {source_upper}"
                    }), 404

                username, password, enabled = row

                if not enabled:
                    return jsonify({
                        "success": False,
                        "error": f"{source_upper} collection is disabled"
                    }), 403

                # Test authentication
                logger.info(f"Testing authentication for {source_upper} with user: {username}")

                if source_upper == "REGTECH":
                    from core.regtech_collector import RegtechCollector
                    collector = RegtechCollector()
                    auth_result = collector.authenticate(username, password)
                elif source_upper == "SECUDIUM":
                    from api.secudium_api import SecudiumAPIClient
                    collector = SecudiumAPIClient(username, password)
                    auth_result = collector.authenticate()

                # Update test results in database
                test_timestamp = datetime.now()
                test_message = "인증 성공" if auth_result else "인증 실패"

                with db.get_connection() as update_conn:
                    update_cursor = update_conn.cursor()
                    update_cursor.execute("""
                        UPDATE collection_credentials
                        SET last_connection_test = %s,
                            last_test_result = %s,
                            last_test_message = %s
                        WHERE service_name = %s
                    """, (test_timestamp, auth_result, test_message, source_upper))
                    update_conn.commit()
                    update_cursor.close()

                if auth_result:
                    logger.info(f"✅ {source_upper} authentication successful")
                    return jsonify({
                        "success": True,
                        "message": "인증 성공",
                        "timestamp": test_timestamp.isoformat()
                    })
                else:
                    logger.warning(f"❌ {source_upper} authentication failed")
                    return jsonify({
                        "success": False,
                        "error": "인증 실패",
                        "timestamp": test_timestamp.isoformat()
                    })  # 200 OK - 테스트 결과는 항상 성공 응답

            except Exception as e:
                logger.error(f"Error testing authentication for {source}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })  # 200 OK - 예외도 테스트 결과로 처리

        @self.app.route('/api/force-collection/<source>', methods=['POST'])
        def force_collection(source):
            """Force immediate collection for a specific source"""
            try:
                source_upper = source.upper()

                if not self.scheduler:
                    return jsonify({
                        "success": False,
                        "error": "Scheduler not available"
                    }), 500

                if source_upper not in ["REGTECH", "SECUDIUM"]:
                    return jsonify({
                        "success": False,
                        "error": f"Invalid source: {source_upper}"
                    }), 400

                logger.info(f"Forcing immediate collection for {source_upper}")
                result = self.scheduler.force_collection(source_upper)

                if result.get('success'):
                    return jsonify({
                        "success": True,
                        "message": f"{source_upper} 수집 완료",
                        "data": result,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    return jsonify({
                        "success": False,
                        "error": result.get('error', '수집 실패'),
                        "timestamp": datetime.now().isoformat()
                    }), 500

            except Exception as e:
                logger.error(f"Error forcing collection for {source}: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500

    def _get_collector_status(self):
        """Get current collector status"""
        status = {}
        for name, collector in self.collectors.items():
            status[name] = {
                'enabled': collector.get('enabled', False),
                'run_count': collector.get('run_count', 0),
                'error_count': collector.get('error_count', 0),
                'interval_seconds': collector.get('interval', 0),
                'last_run': collector.get('last_run').isoformat() if collector.get('last_run') else None,
                'next_run': collector.get('next_run').isoformat() if collector.get('next_run') else None,
            }
        return status
    
    def start(self):
        """Start health server in background thread"""
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        logger.info(f"Health server started on port {self.port}")
    
    def _run_server(self):
        """Run Flask server with waitress"""
        serve(self.app, host='0.0.0.0', port=self.port, _quiet=True)
