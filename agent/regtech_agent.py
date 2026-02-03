#!/usr/bin/env python3
"""
REGTECH Local Agent for Cloudflare D1
Collects data from REGTECH and pushes to CF Worker API

Usage:
    python regtech_agent.py              # One-time collection
    python regtech_agent.py --daemon     # Run as daemon with scheduler
"""

import os
import sys
import time
import json
import logging
import argparse
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collector.core.regtech_collector import RegtechCollector

# Configuration
CF_API_URL = os.getenv("CF_API_URL", "https://blacklist-api.jclee.workers.dev")
CF_INGEST_API_KEY = os.getenv("CF_INGEST_API_KEY", "")
REGTECH_USERNAME = os.getenv("REGTECH_USERNAME", "")
REGTECH_PASSWORD = os.getenv("REGTECH_PASSWORD", "")
COLLECTION_INTERVAL = int(os.getenv("COLLECTION_INTERVAL", "21600"))  # 6 hours

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent.log"),
    ],
)
logger = logging.getLogger(__name__)


class RegtechAgent:
    """Local agent that collects REGTECH data and pushes to CF D1"""

    def __init__(self):
        self.collector = RegtechCollector()
        self.cf_api_url = CF_API_URL
        self.ingest_api_key = CF_INGEST_API_KEY

    def collect_and_push(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Main collection workflow"""
        result = {
            "success": False,
            "collected": 0,
            "pushed": 0,
            "errors": [],
            "timestamp": datetime.now().isoformat(),
        }

        # Step 1: Authenticate
        logger.info("Step 1: Authenticating with REGTECH...")
        if not REGTECH_USERNAME or not REGTECH_PASSWORD:
            result["errors"].append("REGTECH credentials not configured")
            logger.error("REGTECH_USERNAME or REGTECH_PASSWORD not set")
            return result

        if not self.collector.authenticate(REGTECH_USERNAME, REGTECH_PASSWORD):
            result["errors"].append("REGTECH authentication failed")
            logger.error("Failed to authenticate with REGTECH")
            return result

        logger.info("REGTECH authentication successful")

        # Step 2: Collect data
        logger.info("Step 2: Collecting data from REGTECH...")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Date range: {start_date} to {end_date}")

        collected_data = self.collector.collect_blacklist_data(
            page_size=2000,
            start_date=start_date,
            end_date=end_date,
            max_pages=100,
        )

        result["collected"] = len(collected_data)
        logger.info(f"Collected {len(collected_data)} IP records")

        if not collected_data:
            result["errors"].append("No data collected")
            logger.warning("No data collected from REGTECH")
            return result

        # Step 3: Transform data for CF API
        logger.info("Step 3: Transforming data for CF API...")
        items = self._transform_for_cf(collected_data)

        # Step 4: Push to CF D1 via ingest API
        logger.info("Step 4: Pushing data to Cloudflare D1...")
        push_result = self._push_to_cf(items)

        if push_result.get("success"):
            result["success"] = True
            result["pushed"] = push_result.get("stats", {}).get("total", 0)
            result["cf_response"] = push_result
            logger.info(f"Successfully pushed {result['pushed']} records to CF D1")
        else:
            result["errors"].append(f"Push failed: {push_result.get('error')}")
            logger.error(f"Failed to push to CF: {push_result}")

        return result

    def _transform_for_cf(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform collected data to CF ingest format"""
        items = []
        for record in data:
            item = {
                "ip_address": record.get("ip_address", ""),
                "threat_type": record.get("reason", "unknown"),
                "severity": self._map_confidence_to_severity(
                    record.get("confidence_level", 80)
                ),
                "source": "REGTECH",
                "country_code": record.get("country"),
                "first_seen": record.get("detection_date"),
                "last_seen": record.get("last_seen"),
                "description": record.get("reason"),
                "metadata": {
                    "detection_count": record.get("detection_count", 1),
                    "confidence_level": record.get("confidence_level", 80),
                    "removal_date": record.get("removal_date"),
                    "is_active": record.get("is_active", True),
                },
            }

            # Clean None values
            item = {k: v for k, v in item.items() if v is not None}

            # Handle datetime objects
            if isinstance(item.get("last_seen"), datetime):
                item["last_seen"] = item["last_seen"].isoformat()

            items.append(item)

        return items

    def _map_confidence_to_severity(self, confidence: int) -> str:
        """Map confidence level to severity"""
        if confidence >= 90:
            return "critical"
        elif confidence >= 75:
            return "high"
        elif confidence >= 50:
            return "medium"
        else:
            return "low"

    def _push_to_cf(
        self, items: List[Dict[str, Any]], batch_size: int = 500
    ) -> Dict[str, Any]:
        """Push items to CF D1 via ingest API"""
        if not self.ingest_api_key:
            return {"success": False, "error": "CF_INGEST_API_KEY not configured"}

        url = f"{self.cf_api_url}/api/collection/ingest"
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.ingest_api_key,
        }

        total_stats = {"inserted": 0, "updated": 0, "errors": 0, "total": 0}

        # Batch processing
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            payload = {
                "service_name": "REGTECH",
                "items": batch,
                "collection_date": datetime.now().strftime("%Y-%m-%d"),
            }

            try:
                logger.info(
                    f"Pushing batch {i // batch_size + 1} ({len(batch)} items)..."
                )
                response = requests.post(
                    url, headers=headers, json=payload, timeout=120
                )

                if response.status_code == 200:
                    result = response.json()
                    stats = result.get("stats", {})
                    total_stats["inserted"] += stats.get("inserted", 0)
                    total_stats["updated"] += stats.get("updated", 0)
                    total_stats["errors"] += stats.get("errors", 0)
                    total_stats["total"] += stats.get("total", 0)
                    logger.info(f"Batch result: {stats}")
                elif response.status_code == 401:
                    return {"success": False, "error": "Unauthorized - check API key"}
                else:
                    logger.error(
                        f"Batch failed: {response.status_code} - {response.text}"
                    )
                    total_stats["errors"] += len(batch)

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                total_stats["errors"] += len(batch)

            # Rate limiting between batches
            time.sleep(1)

        return {"success": total_stats["errors"] == 0, "stats": total_stats}


def run_daemon(agent: RegtechAgent):
    """Run agent as daemon with scheduler"""
    logger.info(f"Starting daemon mode (interval: {COLLECTION_INTERVAL}s)")

    while True:
        try:
            logger.info("=" * 50)
            logger.info("Starting scheduled collection...")
            result = agent.collect_and_push()
            logger.info(f"Collection result: {json.dumps(result, indent=2)}")
        except Exception as e:
            logger.exception(f"Collection failed: {e}")

        logger.info(f"Next collection in {COLLECTION_INTERVAL} seconds...")
        time.sleep(COLLECTION_INTERVAL)


def main():
    parser = argparse.ArgumentParser(description="REGTECH Local Agent for CF D1")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full collection (90 days)",
    )
    args = parser.parse_args()

    # Validate configuration
    if not CF_INGEST_API_KEY:
        logger.error("CF_INGEST_API_KEY environment variable is required")
        sys.exit(1)

    if not REGTECH_USERNAME or not REGTECH_PASSWORD:
        logger.error("REGTECH_USERNAME and REGTECH_PASSWORD are required")
        sys.exit(1)

    agent = RegtechAgent()

    if args.daemon:
        run_daemon(agent)
    else:
        # One-time collection
        start_date = args.start_date
        end_date = args.end_date

        if args.full:
            start_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
            end_date = datetime.now().strftime("%Y-%m-%d")

        result = agent.collect_and_push(start_date, end_date)
        print(json.dumps(result, indent=2))

        if not result["success"]:
            sys.exit(1)


if __name__ == "__main__":
    main()
