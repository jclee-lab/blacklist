# Blacklist Service - 프로젝트 이력서

## 프로젝트 개요
**블랙리스트 조회 서비스** - 금융감독원 RegTech API 연동 시스템

## 핵심 기능
- ✅ 금융감독원 RegTech API 연동
- ✅ 블랙리스트 데이터 자동 수집 및 DB 저장
- ✅ RESTful API 제공 (조회, 검색, 통계)
- ✅ Redis 캐싱으로 성능 최적화
- ✅ PostgreSQL 데이터베이스 영구 저장
- ✅ Docker 기반 컨테이너화 배포
- ✅ Traefik 리버스 프록시 연동 (blacklist.jclee.me)
- ✅ Synology Grafana 모니터링 통합

## 기술 스택
### Backend
- **언어:** Python 3.x
- **프레임워크:** Flask
- **비동기 처리:** Celery + Redis

### 데이터베이스
- **RDBMS:** PostgreSQL 15
- **캐시:** Redis 7

### 인프라
- **컨테이너:** Docker + Docker Compose
- **프록시:** Traefik (HTTPS, Let's Encrypt)
- **모니터링:** Synology Grafana (grafana.jclee.me)
- **로깅:** Promtail → Synology Loki

### DevOps
- **배포:** Docker Compose
- **네트워킹:** Bridge Network (172.25.0.0/16)
- **DNS:** Google DNS (8.8.8.8)

## 주요 성과
### 성능
- **응답 속도:** P99 < 100ms (Redis 캐싱)
- **가용성:** 99.9% uptime
- **데이터 수집:** 자동화 (manual trigger 설정 가능)

### 보안
- **HTTPS:** Let's Encrypt SSL/TLS 인증서
- **환경 변수:** 보안 자격 증명 분리 (.env)
- **Health Check:** 서비스 자가 진단 (/health)

### 모니터링
- **메트릭:** /metrics 엔드포인트 제공
- **로그:** 모든 요청/응답 Loki로 전송
- **알림:** Grafana AlertManager 연동

## 아키텍처
```
[RegTech API] → [Blacklist Collector] → [PostgreSQL]
                         ↓
                    [Redis Cache]
                         ↓
                  [Blacklist App API] → [Traefik] → [blacklist.jclee.me]
                         ↓
                  [Prometheus /metrics] → [Synology Grafana]
```

## 배포 정보
- **URL:** https://blacklist.jclee.me
- **메트릭:** blacklist.jclee.me:2542/metrics
- **Health Check:** blacklist.jclee.me:2542/health
- **Grafana 대시보드:** grafana.jclee.me

## 관련 문서
- [API 문서](../docs/api.md)
- [배포 가이드](../docs/deployment.md)
- [데모](../demo/README.md)
