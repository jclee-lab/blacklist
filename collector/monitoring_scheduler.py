#!/usr/bin/env python3
"""
Multi-Source Blacklist Data Collection Scheduler
- Supports multiple data sources (REGTECH, SECUDIUM)
- Database-driven configuration
- Independent scheduling per source
- Health monitoring and error recovery
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import psycopg2
from psycopg2 import pool

# Use absolute imports (PYTHONPATH includes /app)
from collector.config import CollectorConfig
from core.policy_monitor import REGTECHPolicyMonitor
from collector.health_server import HealthServer


logger = logging.getLogger(__name__)


class CollectorScheduler:
    """Multi-source blacklist data collection scheduler"""

    def __init__(self):
        self.config = CollectorConfig()

        # Database connection pool for fetching collection credentials
        try:
            self.db_pool = pool.SimpleConnectionPool(
                1, 5,
                host=self.config.POSTGRES_HOST,
                port=self.config.POSTGRES_PORT,
                database=self.config.POSTGRES_DB,
                user=self.config.POSTGRES_USER,
                password=self.config.POSTGRES_PASSWORD
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            self.db_pool = None

        # Collector instances
        self.collectors = {}
        self._initialize_collectors()

        # Scheduling state
        self.is_running = False
        self.scheduler_threads = {}

        # Statistics per source
        self.stats = {}

    def _initialize_collectors(self):
        """Initialize collectors based on database configuration"""
        try:
            # REGTECH collector (always available)
            self.collectors['REGTECH'] = {
                'instance': REGTECHPolicyMonitor(self.config.to_dict()),
                'type': 'monitor',
                'last_run': None,
                'next_run': None,
                'run_count': 0,
                'error_count': 0,
                'enabled': True,
                'interval': 86400  # 24 hours (daily)
            }
            logger.info("REGTECH collector initialized")

            # SECUDIUM collector (import dynamically to avoid errors if not available)
            try:
                from api.secudium_api import SecudiumAPIClient

                # Get credentials from database
                credentials = self._get_collector_credentials('SECUDIUM')
                if credentials and credentials['enabled']:
                    self.collectors['SECUDIUM'] = {
                        'instance': SecudiumAPIClient(
                            credentials['username'],
                            credentials['password']
                        ),
                        'type': 'api',
                        'last_run': credentials.get('last_collection'),
                        'next_run': None,
                        'run_count': 0,
                        'error_count': 0,
                        'enabled': credentials['enabled'],
                        'interval': self._interval_to_seconds(credentials.get('collection_interval', 'daily'))
                    }
                    logger.info("SECUDIUM collector initialized")
                else:
                    logger.info("SECUDIUM collector disabled or credentials not found")
            except ImportError as e:
                logger.warning(f"SECUDIUM collector not available: {e}")

        except Exception as e:
            logger.error(f"Error initializing collectors: {e}", exc_info=True)

    def _get_collector_credentials(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Fetch collector credentials from database"""
        if not self.db_pool:
            return None

        conn = None
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT service_name, username, password, enabled,
                       collection_interval, last_collection
                FROM collection_credentials
                WHERE service_name = %s
            """, (service_name,))

            row = cursor.fetchone()
            if row:
                return {
                    'service_name': row[0],
                    'username': row[1],
                    'password': row[2],
                    'enabled': row[3],
                    'collection_interval': row[4],
                    'last_collection': row[5]
                }
            return None

        except Exception as e:
            logger.error(f"Error fetching credentials for {service_name}: {e}")
            return None
        finally:
            if conn:
                self.db_pool.putconn(conn)

    def _interval_to_seconds(self, interval: str) -> int:
        """Convert interval string to seconds"""
        interval_map = {
            'hourly': 3600,
            'daily': 86400,  # 24 hours
            'weekly': 604800
        }
        return interval_map.get(interval, 86400)  # Default to daily

    def start(self):
        """Start all enabled collectors"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        self.is_running = True

        # Start thread for each enabled collector
        for source_name, collector_info in self.collectors.items():
            if collector_info['enabled']:
                thread = threading.Thread(
                    target=self._collector_loop,
                    args=(source_name,),
                    daemon=True,
                    name=f"Collector-{source_name}"
                )
                self.scheduler_threads[source_name] = thread
                thread.start()
                logger.info(f"Started scheduler for {source_name}")

        logger.info(f"Collection scheduler started with {len(self.scheduler_threads)} collectors")

    def stop(self):
        """Stop all collectors"""
        self.is_running = False

        # Wait for all threads to finish
        for source_name, thread in self.scheduler_threads.items():
            if thread.is_alive():
                thread.join(timeout=10)
                logger.info(f"Stopped {source_name} collector")

        self.scheduler_threads.clear()
        logger.info("Collection scheduler stopped")

    def _collector_loop(self, source_name: str):
        """Main loop for a specific collector"""
        collector_info = self.collectors[source_name]

        logger.info(f"Starting collection loop for {source_name} (interval: {collector_info['interval']}s)")

        while self.is_running:
            try:
                # Execute collection
                result = self._execute_collection(source_name)

                # Update statistics
                collector_info['last_run'] = datetime.now()

                if result.get('success'):
                    collector_info['run_count'] += 1
                    logger.info(f"{source_name} collection completed successfully (#{collector_info['run_count']})")

                    # Update database last_collection timestamp
                    self._update_last_collection(source_name)
                else:
                    collector_info['error_count'] += 1
                    logger.error(f"{source_name} collection failed: {result.get('error', 'Unknown error')}")

                # Calculate next run time
                next_run_time = datetime.now() + timedelta(seconds=collector_info['interval'])
                collector_info['next_run'] = next_run_time

                # Wait until next collection
                self._sleep_until_next_run(source_name, collector_info['interval'])

            except Exception as e:
                collector_info['error_count'] += 1
                logger.error(f"Error in {source_name} collection loop: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retry

    def _execute_collection(self, source_name: str) -> Dict[str, Any]:
        """Execute collection for a specific source"""
        collector_info = self.collectors.get(source_name)
        if not collector_info:
            return {'success': False, 'error': f'Collector {source_name} not found'}

        try:
            logger.info(f"Executing {source_name} collection...")
            start_time = time.time()

            instance = collector_info['instance']
            collector_type = collector_info['type']

            # Execute based on collector type
            if collector_type == 'monitor':
                # REGTECH monitor
                result = instance.run_monitoring_check()
            elif collector_type == 'api':
                # SECUDIUM API collector
                result = self._run_secudium_collection(instance)
            else:
                raise ValueError(f"Unknown collector type: {collector_type}")

            duration = time.time() - start_time

            return {
                'success': True,
                'source': source_name,
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'details': result
            }

        except Exception as e:
            logger.error(f"Error executing {source_name} collection: {e}", exc_info=True)
            return {
                'success': False,
                'source': source_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _run_secudium_collection(self, client) -> Dict[str, Any]:
        """
        Run SECUDIUM collection workflow using browser automation.

        Browser automation is used instead of API because:
        1. API listing endpoint returns 401 even with valid token
        2. API download endpoint returns "관리자에게 문의해 주세요" error
        3. Browser automation works reliably
        """
        try:
            logger.info("[SECUDIUM] Starting browser-based collection...")

            # Use browser automation for complete workflow
            # Returns: List of tuples [(records, metadata), ...]
            results = client.collect_latest_via_browser(limit=5)

            if not results:
                logger.info("[SECUDIUM] No files collected")
                return {'success': True, 'items_collected': 0, 'message': 'No files found'}

            total_collected = 0

            # Process each collected file
            for idx, (records, metadata) in enumerate(results, 1):
                logger.info(f"[SECUDIUM] Processing file {idx}/{len(results)}: {metadata['filename']}")

                # Insert blacklist data
                items_inserted = self._insert_blacklist_data(records, 'SECUDIUM')
                total_collected += items_inserted

                logger.info(f"[SECUDIUM] File {metadata['filename']} processed: {items_inserted} IPs inserted")

            return {
                'success': True,
                'items_collected': total_collected,
                'files_processed': len(results)
            }

        except Exception as e:
            logger.error(f"SECUDIUM collection error: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _is_report_processed(self, report_id: str) -> bool:
        """Check if report has already been processed"""
        if not self.db_pool:
            return False

        conn = None
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT 1 FROM processed_reports
                WHERE source = 'SECUDIUM' AND report_id = %s
            """, (str(report_id),))

            return cursor.fetchone() is not None

        except Exception as e:
            logger.error(f"Error checking processed report: {e}")
            return False
        finally:
            if conn:
                self.db_pool.putconn(conn)

    def _mark_report_processed(self, report: Dict[str, Any]):
        """Mark report as processed in database"""
        if not self.db_pool:
            return

        conn = None
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO processed_reports (
                    source, report_id, report_date, filename,
                    records_count, processed_at, metadata
                ) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
                ON CONFLICT (source, report_id) DO NOTHING
            """, (
                'SECUDIUM',
                str(report['id']),
                report.get('date'),
                report.get('title', 'Unknown'),
                report.get('record_count', 0),
                psycopg2.extras.Json(report)
            ))

            conn.commit()
            logger.info(f"Marked SECUDIUM report {report['id']} as processed")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error marking report as processed: {e}")
        finally:
            if conn:
                self.db_pool.putconn(conn)

    def _insert_blacklist_data(self, data: List[Dict[str, Any]], source: str) -> int:
        """Insert blacklist data into database"""
        if not self.db_pool or not data:
            return 0

        conn = None
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            insert_count = 0
            for item in data:
                try:
                    cursor.execute("""
                        INSERT INTO blacklist_ips (
                            ip_address, country, reason, detection_date,
                            removal_date, data_source, raw_data, is_active
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, true)
                        ON CONFLICT (ip_address, detection_date)
                        DO UPDATE SET
                            country = EXCLUDED.country,
                            reason = EXCLUDED.reason,
                            removal_date = EXCLUDED.removal_date,
                            data_source = EXCLUDED.data_source,
                            raw_data = EXCLUDED.raw_data,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        item['ip_address'],
                        item.get('country', 'Unknown'),
                        item.get('reason', ''),
                        item.get('detection_date'),
                        item.get('removal_date'),
                        source,
                        psycopg2.extras.Json(item.get('raw_data', {}))
                    ))
                    insert_count += 1
                except Exception as e:
                    logger.warning(f"Failed to insert IP {item.get('ip_address')}: {e}")
                    continue

            conn.commit()
            logger.info(f"Inserted {insert_count} IPs from {source}")
            return insert_count

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error inserting blacklist data: {e}")
            return 0
        finally:
            if conn:
                self.db_pool.putconn(conn)

    def _update_last_collection(self, source_name: str):
        """Update last_collection timestamp in database"""
        if not self.db_pool:
            return

        conn = None
        try:
            conn = self.db_pool.getconn()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE collection_credentials
                SET last_collection = CURRENT_TIMESTAMP
                WHERE service_name = %s
            """, (source_name,))

            conn.commit()

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error updating last_collection for {source_name}: {e}")
        finally:
            if conn:
                self.db_pool.putconn(conn)

    def _sleep_until_next_run(self, source_name: str, interval: int):
        """Sleep until next collection time"""
        collector_info = self.collectors.get(source_name)
        if not collector_info:
            return

        # Adaptive interval adjustment on errors
        sleep_time = interval
        if collector_info['error_count'] > 3:
            sleep_time = min(interval * 2, 7200)  # Max 2 hours
            logger.info(f"{source_name}: Increased interval to {sleep_time}s due to errors")

        logger.debug(f"{source_name}: Sleeping {sleep_time}s until next run")

        # Interruptible sleep
        end_time = time.time() + sleep_time
        while self.is_running and time.time() < end_time:
            time.sleep(1)

    def get_status(self) -> Dict[str, Any]:
        """Get overall scheduler status"""
        return {
            'is_running': self.is_running,
            'collectors': {
                name: {
                    'enabled': info['enabled'],
                    'run_count': info['run_count'],
                    'error_count': info['error_count'],
                    'last_run': info['last_run'].isoformat() if info['last_run'] else None,
                    'next_run': info['next_run'].isoformat() if info['next_run'] else None,
                    'interval_seconds': info['interval']
                }
                for name, info in self.collectors.items()
            }
        }

    def force_collection(self, source_name: str) -> Dict[str, Any]:
        """Force immediate collection for a specific source"""
        if source_name not in self.collectors:
            return {'success': False, 'error': f'Unknown source: {source_name}'}

        logger.info(f"Forcing immediate collection for {source_name}")
        return self._execute_collection(source_name)


# Global scheduler instance
_scheduler = None


def get_scheduler() -> CollectorScheduler:
    """Get or create global scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = CollectorScheduler()
    return _scheduler


def start_scheduler():
    """Start the global scheduler"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """Stop the global scheduler"""
    scheduler = get_scheduler()
    scheduler.stop()


def get_scheduler_status():
    """Get scheduler status"""
    scheduler = get_scheduler()
    return scheduler.get_status()


def force_collection(source_name: str):
    """Force immediate collection"""
    scheduler = get_scheduler()
    return scheduler.force_collection(source_name)


if __name__ == "__main__":
    # Standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Attach log buffer handler for memory logging
    from collector.health_server import LogBufferHandler
    log_buffer_handler = LogBufferHandler()
    log_buffer_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(log_buffer_handler)

    try:
        print("Starting Multi-Source Collection Scheduler")

        # Start scheduler
        start_scheduler()

        # Start health server
        scheduler = get_scheduler()
        health_server = HealthServer(scheduler.collectors, scheduler_ref=scheduler, port=8545)
        health_server.start()
        logger.info("Health server started on port 8545")

        # Keep running
        while True:
            time.sleep(60)
            status = get_scheduler_status()
            print(f"\nScheduler Status: {status['is_running']}")
            for source, info in status['collectors'].items():
                print(f"  {source}: {info['run_count']} runs, {info['error_count']} errors")

    except KeyboardInterrupt:
        print("\nStopping scheduler...")
        stop_scheduler()
