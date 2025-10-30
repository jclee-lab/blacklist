"""
탐지일 데이터 분석 및 시각화 API
Detection Date Analytics and Visualization
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, render_template

logger = logging.getLogger(__name__)

# Detection Analytics Blueprint
detection_bp = Blueprint("detection_analytics", __name__, url_prefix="/analytics")


@detection_bp.route("/detection-timeline", methods=["GET"])
def get_detection_timeline():
    """탐지일별 IP 수집 현황 분석"""
    try:
        from ..services.database_service import db_service

        # 쿼리 파라미터
        days_back = int(request.args.get("days", 30))  # 기본 30일
        format_type = request.args.get("format", "json")  # json 또는 chart

        conn = db_service.get_connection()
        cursor = conn.cursor()

        # 날짜별 수집 통계 (detection_date가 없으면 created_at 사용)
        query = """
            SELECT
                COALESCE(detection_date, created_at::date) as detection_day,
                COUNT(*) as ip_count,
                COUNT(DISTINCT source) as source_count,
                STRING_AGG(DISTINCT source, ', ') as sources,
                MIN(created_at) as first_collected,
                MAX(created_at) as last_collected
            FROM blacklist_ips
            WHERE COALESCE(detection_date, created_at::date) >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY COALESCE(detection_date, created_at::date)
            ORDER BY detection_day DESC
        """

        cursor.execute(query, (days_back,))
        results = cursor.fetchall()

        # 컬럼명 매핑
        columns = [
            "detection_day",
            "ip_count",
            "source_count",
            "sources",
            "first_collected",
            "last_collected",
        ]
        timeline_data = []

        for row in results:
            data = dict(zip(columns, row))

            # 날짜 형식 변환
            if data["detection_day"]:
                data["detection_day"] = str(data["detection_day"])
            if data["first_collected"]:
                data["first_collected"] = data["first_collected"].isoformat()
            if data["last_collected"]:
                data["last_collected"] = data["last_collected"].isoformat()

            # 수상한 패턴 탐지
            suspicious_patterns = []

            # 1. 비정상적으로 많은 IP (평균의 3배 이상)
            if len(timeline_data) > 0:
                avg_count = sum([d["ip_count"] for d in timeline_data]) / len(
                    timeline_data
                )
                if data["ip_count"] > avg_count * 3:
                    suspicious_patterns.append("abnormal_volume")

            # 2. 정확히 떨어지는 숫자 (1000, 5000, 10000 등)
            if data["ip_count"] % 1000 == 0 and data["ip_count"] >= 1000:
                suspicious_patterns.append("round_number")

            # 3. 동일한 소스에서 대량 수집
            if data["source_count"] == 1 and data["ip_count"] > 1000:
                suspicious_patterns.append("single_source_bulk")

            data["suspicious_patterns"] = suspicious_patterns
            data["is_suspicious"] = len(suspicious_patterns) > 0

            timeline_data.append(data)

        # 통계 요약
        total_ips = sum([d["ip_count"] for d in timeline_data])
        total_days = len(timeline_data)
        avg_per_day = total_ips / total_days if total_days > 0 else 0

        # 소스별 통계
        cursor.execute(
            """
            SELECT
                source,
                COUNT(*) as total_ips,
                COUNT(DISTINCT COALESCE(detection_date, created_at::date)) as active_days,
                MIN(COALESCE(detection_date, created_at::date)) as first_detection,
                MAX(COALESCE(detection_date, created_at::date)) as last_detection
            FROM blacklist_ips
            WHERE COALESCE(detection_date, created_at::date) >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY source
            ORDER BY total_ips DESC
        """,
            (days_back,),
        )

        source_results = cursor.fetchall()
        source_stats = []
        for row in source_results:
            source_data = {
                "source": row[0],
                "total_ips": row[1],
                "active_days": row[2],
                "first_detection": str(row[3]) if row[3] else None,
                "last_detection": str(row[4]) if row[4] else None,
                "avg_per_day": round(row[1] / row[2], 1) if row[2] > 0 else 0,
            }
            source_stats.append(source_data)

        cursor.close()
        conn.close()

        # 수상한 패턴 요약
        suspicious_days = [d for d in timeline_data if d["is_suspicious"]]
        pattern_summary = {}
        for day in suspicious_days:
            for pattern in day["suspicious_patterns"]:
                pattern_summary[pattern] = pattern_summary.get(pattern, 0) + 1

        # 로그 출력 (탐지일 데이터 분석)
        logger.info("📊 탐지일 데이터 분석 결과:")
        logger.info(f"   • 분석 기간: {days_back}일")
        logger.info(f"   • 총 IP 수: {total_ips:,}개")
        logger.info(f"   • 활성 일수: {total_days}일")
        logger.info(f"   • 일평균: {avg_per_day:.1f}개")
        logger.info(f"   • 수상한 패턴: {len(suspicious_days)}일")

        if suspicious_days:
            logger.warning("🚨 수상한 데이터 패턴 발견:")
            for day in suspicious_days[:5]:  # 최대 5일만 로그
                logger.warning(
                    f"   • {day['detection_day']}: {day['ip_count']:,}개 IP ({', '.join(day['suspicious_patterns'])})"
                )

        response_data = {
            "success": True,
            "metadata": {
                "analysis_period_days": days_back,
                "total_ips": total_ips,
                "total_days": total_days,
                "avg_per_day": round(avg_per_day, 1),
                "generated_at": datetime.now().isoformat(),
            },
            "timeline": timeline_data,
            "source_statistics": source_stats,
            "suspicious_analysis": {
                "suspicious_days_count": len(suspicious_days),
                "pattern_summary": pattern_summary,
                "suspicious_days": suspicious_days[:10],  # 최대 10일만 반환
            },
        }

        if format_type == "chart":
            # 차트용 간단한 데이터 형식
            chart_data = {
                "labels": [d["detection_day"] for d in timeline_data],
                "datasets": [
                    {
                        "label": "IP 수집량",
                        "data": [d["ip_count"] for d in timeline_data],
                        "backgroundColor": [
                            (
                                "rgba(255, 99, 132, 0.8)"
                                if d["is_suspicious"]
                                else "rgba(54, 162, 235, 0.8)"
                            )
                            for d in timeline_data
                        ],
                        "borderColor": [
                            (
                                "rgba(255, 99, 132, 1)"
                                if d["is_suspicious"]
                                else "rgba(54, 162, 235, 1)"
                            )
                            for d in timeline_data
                        ],
                        "borderWidth": 1,
                    }
                ],
            }
            return jsonify(
                {
                    "success": True,
                    "chart_data": chart_data,
                    "summary": response_data["metadata"],
                    "suspicious_count": len(suspicious_days),
                }
            )

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Detection timeline analysis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@detection_bp.route("/suspicious-patterns", methods=["GET"])
def get_suspicious_patterns():
    """수상한 데이터 패턴 상세 분석"""
    try:
        import os
        import psycopg2
        from psycopg2.extras import RealDictCursor

        # 직접 DB 연결로 인증 문제 해결
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "blacklist-postgres"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "blacklist"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            cursor_factory=RealDictCursor,
        )
        cursor = conn.cursor()

        patterns = []

        # 1. 정확히 떨어지는 숫자 패턴
        cursor.execute(
            """
            SELECT
                COALESCE(detection_date, created_at::date) as day,
                COUNT(*) as count,
                source
            FROM blacklist_ips
            GROUP BY COALESCE(detection_date, created_at::date), source
            HAVING COUNT(*) % 1000 = 0 AND COUNT(*) >= 1000
            ORDER BY count DESC
        """
        )

        round_numbers = cursor.fetchall()
        if round_numbers:
            patterns.append(
                {
                    "type": "round_numbers",
                    "description": "정확히 떨어지는 숫자 (1000, 5000, 10000 등)",
                    "severity": "high",
                    "count": len(round_numbers),
                    "examples": [
                        {"date": str(row[0]), "ip_count": row[1], "source": row[2]}
                        for row in round_numbers[:5]
                    ],
                }
            )

            # 로그 출력
            logger.warning("🚨 정확히 떨어지는 숫자 패턴 발견:")
            for row in round_numbers[:3]:
                logger.warning(f"   • {row[0]}: {row[1]:,}개 ({row[2]})")

        # 2. 비정상적 대량 수집
        cursor.execute(
            """
            WITH daily_stats AS (
                SELECT
                    COALESCE(detection_date, created_at::date) as day,
                    COUNT(*) as count
                FROM blacklist_ips
                GROUP BY COALESCE(detection_date, created_at::date)
            ),
            avg_stats AS (
                SELECT AVG(count) as avg_count, STDDEV(count) as stddev_count
                FROM daily_stats
            )
            SELECT d.day, d.count, a.avg_count
            FROM daily_stats d, avg_stats a
            WHERE d.count > (a.avg_count + 2 * COALESCE(a.stddev_count, a.avg_count))
            ORDER BY d.count DESC
        """
        )

        bulk_collections = cursor.fetchall()
        if bulk_collections:
            patterns.append(
                {
                    "type": "bulk_collection",
                    "description": "비정상적 대량 수집 (평균 + 2σ 이상)",
                    "severity": "medium",
                    "count": len(bulk_collections),
                    "examples": [
                        {
                            "date": str(row[0]),
                            "ip_count": row[1],
                            "avg_baseline": round(float(row[2]), 1),
                        }
                        for row in bulk_collections[:5]
                    ],
                }
            )

            # 로그 출력
            logger.warning("🚨 비정상적 대량 수집 패턴 발견:")
            for row in bulk_collections[:3]:
                logger.warning(f"   • {row[0]}: {row[1]:,}개 (평균: {row[2]:.1f}개)")

        # 3. 단일 소스 대량 수집
        cursor.execute(
            """
            SELECT
                source,
                COALESCE(detection_date, created_at::date) as day,
                COUNT(*) as count
            FROM blacklist_ips
            GROUP BY source, COALESCE(detection_date, created_at::date)
            HAVING COUNT(*) > 10000
            ORDER BY count DESC
        """
        )

        single_source_bulk = cursor.fetchall()
        if single_source_bulk:
            patterns.append(
                {
                    "type": "single_source_bulk",
                    "description": "단일 소스에서 1만개 이상 수집",
                    "severity": "high",
                    "count": len(single_source_bulk),
                    "examples": [
                        {"source": row[0], "date": str(row[1]), "ip_count": row[2]}
                        for row in single_source_bulk[:5]
                    ],
                }
            )

            # 로그 출력
            logger.warning("🚨 단일 소스 대량 수집 패턴 발견:")
            for row in single_source_bulk[:3]:
                logger.warning(f"   • {row[1]} {row[0]}: {row[2]:,}개")

        cursor.close()
        conn.close()

        # 종합 위험도 평가
        total_issues = sum([p["count"] for p in patterns])
        risk_level = "low"
        if total_issues > 10:
            risk_level = "high"
        elif total_issues > 5:
            risk_level = "medium"

        logger.info(
            f"📊 수상한 패턴 분석 완료: {len(patterns)}가지 패턴, 총 {total_issues}건, 위험도: {risk_level}"
        )

        return jsonify(
            {
                "success": True,
                "analysis": {
                    "total_pattern_types": len(patterns),
                    "total_issues": total_issues,
                    "risk_level": risk_level,
                    "generated_at": datetime.now().isoformat(),
                },
                "patterns": patterns,
            }
        )

    except Exception as e:
        logger.error(f"Suspicious patterns analysis error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@detection_bp.route("/detection-chart")
def detection_chart_page():
    """탐지일 데이터 시각화 페이지"""
    try:
        return render_template("detection_chart.html")
    except Exception as e:
        logger.error(f"Detection chart page error: {e}")
        return f"Error loading detection chart: {e}", 500


@detection_bp.route("/real-time-log", methods=["GET"])
def get_real_time_detection_log():
    """실시간 탐지 로그 스트림"""
    try:
        from ..services.database_service import db_service

        # 최근 24시간 내 수집된 데이터 로그
        conn = db_service.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                created_at,
                ip_address,
                source,
                COALESCE(detection_date, created_at::date) as detection_day,
                confidence_level
            FROM blacklist_ips
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 10000
        """
        )

        results = cursor.fetchall()

        log_entries = []
        for row in results:
            entry = {
                "timestamp": row[0].isoformat() if row[0] else None,
                "ip_address": row[1],
                "source": row[2],
                "detection_day": str(row[3]) if row[3] else None,
                "confidence_level": row[4],
                "log_type": "detection",
            }
            log_entries.append(entry)

        cursor.close()
        conn.close()

        # 실시간 로그 출력
        logger.info(f"📡 실시간 탐지 로그: 최근 24시간 {len(log_entries)}건")
        for entry in log_entries[:5]:  # 최근 5건만 로그
            logger.info(
                f"   • {entry['timestamp']}: {entry['ip_address']} ({entry['source']})"
            )

        return jsonify(
            {
                "success": True,
                "log_entries": log_entries,
                "metadata": {
                    "total_entries": len(log_entries),
                    "time_range": "24h",
                    "generated_at": datetime.now().isoformat(),
                },
            }
        )

    except Exception as e:
        logger.error(f"Real-time detection log error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
