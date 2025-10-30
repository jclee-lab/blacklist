# 📊 XWiki 배포 구조 시각화

## 🗂️ XAR 패키지 구조

```
blacklist-docs.xar (40KB, ZIP 포맷)
│
├── 📄 package.xml                           # 패키지 메타데이터
│
└── 📑 Page XMLs (11개)
    ├── Main.Blacklist.Index.xml             # 00-index.txt
    ├── Main.Blacklist.Deployment.xml        # 01-deployment.txt
    ├── Main.Blacklist.Architecture.xml      # 02-architecture.txt
    ├── Main.Blacklist.API.xml               # 03-api-auto.txt
    ├── Main.Blacklist.Diagrams.xml          # 04-diagrams.txt (PlantUML)
    ├── Main.Blacklist.Upgrade.xml           # 05-upgrade.txt
    ├── Main.Blacklist.Security.xml          # 06-security.txt
    ├── Main.Blacklist.Troubleshooting.xml   # 07-troubleshooting.txt
    ├── Main.Blacklist.Appendix.xml          # 08-appendix.txt
    ├── Main.Blacklist.Dashboard.xml         # 09-dashboard.txt
    └── Main.Blacklist.Monitoring.xml        # 10-monitoring.txt
```

---

## 🌳 XWiki 배포 후 계층 구조

### Import 전 (XWiki 빈 상태)
```
XWiki
└── 📂 Main Space
    └── (비어있음)
```

### Import 후 (자동 계층 생성)
```
XWiki
└── 📂 Main Space
    └── 📘 Blacklist (부모 페이지)
        ├── 📄 Index (목차)                    ← 00-index.txt
        ├── 📄 Deployment (설치 및 배포)        ← 01-deployment.txt
        ├── 📄 Architecture (시스템 아키텍처)   ← 02-architecture.txt
        ├── 📄 API (API 사용법)                ← 03-api-auto.txt
        ├── 📄 Diagrams (다이어그램 모음)       ← 04-diagrams.txt (PlantUML)
        ├── 📄 Upgrade (업그레이드 가이드)      ← 05-upgrade.txt
        ├── 📄 Security (보안 설정)            ← 06-security.txt
        ├── 📄 Troubleshooting (문제 해결)     ← 07-troubleshooting.txt
        ├── 📄 Appendix (부록)                 ← 08-appendix.txt
        ├── 📄 Dashboard (실시간 대시보드)      ← 09-dashboard.txt
        └── 📄 Monitoring (모니터링)           ← 10-monitoring.txt
```

**총 12개 페이지**: 부모 1개 + 하위 11개

---

## 🔗 URL 구조

### 부모 페이지
```
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist
```

### 하위 페이지들
```
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist/Index
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist/Deployment
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist/Architecture
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist/API
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist/Diagrams
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist/Upgrade
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist/Security
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist/Troubleshooting
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist/Appendix
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist/Dashboard
http://your-xwiki.com:8080/xwiki/bin/view/Main/Blacklist/Monitoring
```

---

## 🎨 XWiki 화면 구성 (Import 후)

### 1. 좌측 네비게이션 패널
```
📂 Main
  └── 📘 Blacklist
      ├── 📄 Index
      ├── 📄 Deployment
      ├── 📄 Architecture
      ├── 📄 API
      ├── 📄 Diagrams ← PlantUML 다이어그램 5개
      ├── 📄 Upgrade
      ├── 📄 Security
      ├── 📄 Troubleshooting
      ├── 📄 Appendix
      ├── 📄 Dashboard ← Velocity + 실시간 API
      └── 📄 Monitoring ← Grafana iframe 3개
```

### 2. 부모 페이지 (Main.Blacklist)
```
┌─────────────────────────────────────────┐
│ 📘 Blacklist Documentation              │
│                                         │
│ 목차 (자동 생성 트리)                    │
│ ├─ Index                                │
│ ├─ Deployment                           │
│ ├─ Architecture                         │
│ └─ ...                                  │
│                                         │
│ [하위 페이지 링크 자동 생성]             │
└─────────────────────────────────────────┘
```

### 3. Diagrams 페이지 (PlantUML)
```
┌─────────────────────────────────────────┐
│ 📄 Diagrams                             │
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ Container Network Topology      │   │
│ │ (PlantUML 자동 렌더링)           │   │
│ │                                 │   │
│ │   [Docker Network Diagram]      │   │
│ └─────────────────────────────────┘   │
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ IP Check Flowchart              │   │
│ │ (PlantUML 자동 렌더링)           │   │
│ │                                 │   │
│ │   [3-Stage Decision Logic]      │   │
│ └─────────────────────────────────┘   │
│                                         │
│ ... (총 5개 다이어그램)                 │
└─────────────────────────────────────────┘
```

### 4. Dashboard 페이지 (실시간)
```
┌─────────────────────────────────────────┐
│ 📄 Dashboard                            │
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ System Status (실시간 API 호출)  │   │
│ │ ✅ PostgreSQL: healthy          │   │
│ │ ✅ Redis: healthy               │   │
│ │ ✅ App: running                 │   │
│ └─────────────────────────────────┘   │
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ Recent Activity (실시간)         │   │
│ │ - 192.168.1.1 blocked           │   │
│ │ - 10.0.0.1 whitelisted          │   │
│ └─────────────────────────────────┘   │
│                                         │
│ (30초마다 자동 새로고침)                │
└─────────────────────────────────────────┘
```

### 5. Monitoring 페이지 (Grafana)
```
┌─────────────────────────────────────────┐
│ 📄 Monitoring                           │
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ Grafana Dashboard 1             │   │
│ │ (iframe embed)                  │   │
│ │ [Real-time Metrics]             │   │
│ └─────────────────────────────────┘   │
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ Grafana Dashboard 2             │   │
│ │ (iframe embed)                  │   │
│ │ [Log Analysis]                  │   │
│ └─────────────────────────────────┘   │
│                                         │
│ ┌─────────────────────────────────┐   │
│ │ Grafana Dashboard 3             │   │
│ │ (iframe embed)                  │   │
│ │ [Performance Metrics]           │   │
│ └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## 🔄 배포 프로세스 시각화

### 방법 1: XAR Import (가장 쉬움, 30초)

```
┌─────────────────┐
│ blacklist-docs  │
│     .xar        │  ← 로컬 파일 (40KB)
└────────┬────────┘
         │ Upload (10초)
         ↓
┌─────────────────┐
│ XWiki Admin     │
│ Import Page     │  ← http://xwiki.com:8080/xwiki/bin/admin/.../Import
└────────┬────────┘
         │ Click "Import" (5초)
         ↓
┌─────────────────┐
│ XWiki Processing│
│ - Extract ZIP   │
│ - Parse 11 XMLs │
│ - Create Pages  │  ← 자동 계층 구조 생성
│ - Set Parents   │
└────────┬────────┘
         │ Complete (15초)
         ↓
┌─────────────────┐
│ Main.Blacklist  │
│   ├─ Index      │
│   ├─ Deployment │
│   └─ ...        │  ← 12개 페이지 완성
└─────────────────┘
```

### 방법 2: REST API (자동화 가능, 1분)

```
┌─────────────────┐
│ xwiki-deploy-   │
│ advanced.py     │  ← 로컬 Python 스크립트
└────────┬────────┘
         │ HTTP PUT (각 페이지마다)
         ↓
┌─────────────────┐
│ XWiki REST API  │
│ /rest/wikis/    │
│ xwiki/spaces/   │  ← http://xwiki.com:8080/rest/...
│ Main/pages/     │
└────────┬────────┘
         │ Create Pages (병렬 처리)
         ↓
┌─────────────────┐
│ 11번 반복:      │
│ PUT Index       │
│ PUT Deployment  │
│ PUT Architecture│  ← 각 페이지 생성 + parent 설정
│ ...             │
└────────┬────────┘
         │ Complete (1분)
         ↓
┌─────────────────┐
│ Main.Blacklist  │
│   ├─ Index      │
│   ├─ Deployment │
│   └─ ...        │  ← 12개 페이지 완성
└─────────────────┘
```

### 방법 3: 수동 복붙 (비추천, 5분)

```
┌─────────────────┐
│ XWIKI_COMPLETE_ │
│ SINGLE_PAGE.txt │  ← 로컬 통합 파일 (160KB)
└────────┬────────┘
         │ Copy (Ctrl+C)
         ↓
┌─────────────────┐
│ XWiki Edit Mode │
│ Main.Blacklist  │  ← 수동으로 페이지 생성
└────────┬────────┘
         │ Paste (Ctrl+V)
         ↓
┌─────────────────┐
│ 1개 페이지 생성  │
│ (단일 페이지만)  │  ← 계층 구조 없음
└────────┬────────┘
         │ 하위 페이지 생성 필요
         ↓
┌─────────────────┐
│ 11번 반복:      │
│ 1. 페이지 생성   │
│ 2. 파일 복사     │
│ 3. 붙여넣기      │  ← 수동 작업 (각 5분)
│ 4. Parent 설정   │
└────────┬────────┘
         │ Complete (55분)
         ↓
┌─────────────────┐
│ Main.Blacklist  │
│   ├─ Index      │
│   ├─ Deployment │
│   └─ ...        │  ← 12개 페이지 완성 (힘들게)
└─────────────────┘
```

---

## 📦 파일 → XWiki 매핑

| 로컬 파일 | XAR 내부 XML | XWiki 페이지 | 비고 |
|----------|-------------|-------------|------|
| `00-index.txt` | `Main.Blacklist.Index.xml` | `Main.Blacklist.Index` | 목차 |
| `01-deployment.txt` | `Main.Blacklist.Deployment.xml` | `Main.Blacklist.Deployment` | 설치 |
| `02-architecture.txt` | `Main.Blacklist.Architecture.xml` | `Main.Blacklist.Architecture` | 아키텍처 |
| `03-api-auto.txt` | `Main.Blacklist.API.xml` | `Main.Blacklist.API` | API 37개 |
| `04-diagrams.txt` | `Main.Blacklist.Diagrams.xml` | `Main.Blacklist.Diagrams` | **PlantUML 5개** |
| `05-upgrade.txt` | `Main.Blacklist.Upgrade.xml` | `Main.Blacklist.Upgrade` | 업그레이드 |
| `06-security.txt` | `Main.Blacklist.Security.xml` | `Main.Blacklist.Security` | 보안 |
| `07-troubleshooting.txt` | `Main.Blacklist.Troubleshooting.xml` | `Main.Blacklist.Troubleshooting` | 문제 해결 |
| `08-appendix.txt` | `Main.Blacklist.Appendix.xml` | `Main.Blacklist.Appendix` | 부록 |
| `09-dashboard.txt` | `Main.Blacklist.Dashboard.xml` | `Main.Blacklist.Dashboard` | **실시간 API** |
| `10-monitoring.txt` | `Main.Blacklist.Monitoring.xml` | `Main.Blacklist.Monitoring` | **Grafana 3개** |

---

## 🎯 배포 위치 요약

### 물리적 위치 (서버)
```
XWiki 서버
└── /opt/xwiki/                    # XWiki 설치 디렉토리
    └── data/
        └── store/
            └── file/
                └── xwiki/
                    └── Main/
                        └── Blacklist/  ← 여기에 12개 페이지 저장
```

### 논리적 위치 (XWiki 구조)
```
Space: Main
└── Page: Blacklist (부모)
    ├── Page: Index (자식)
    ├── Page: Deployment (자식)
    ├── Page: Architecture (자식)
    ├── Page: API (자식)
    ├── Page: Diagrams (자식) ← PlantUML 5개
    ├── Page: Upgrade (자식)
    ├── Page: Security (자식)
    ├── Page: Troubleshooting (자식)
    ├── Page: Appendix (자식)
    ├── Page: Dashboard (자식) ← Velocity + API
    └── Page: Monitoring (자식) ← Grafana iframe 3개
```

### 접근 URL
```
부모:    http://xwiki.com:8080/xwiki/bin/view/Main/Blacklist
하위 11개: http://xwiki.com:8080/xwiki/bin/view/Main/Blacklist/{PageName}
```

---

## 🔍 배포 확인 방법

### 1. XWiki 웹 UI 확인
```
1. http://xwiki.com:8080/xwiki 접속
2. 좌측 네비게이션에서 "Main" Space 클릭
3. "Blacklist" 페이지 확인
4. 하위 11개 페이지 트리 구조 확인
```

### 2. REST API로 확인
```bash
# 부모 페이지 존재 확인
curl http://xwiki.com:8080/xwiki/rest/wikis/xwiki/spaces/Main/pages/Blacklist

# 하위 페이지 목록
curl http://xwiki.com:8080/xwiki/rest/wikis/xwiki/spaces/Main/spaces/Blacklist/pages

# 특정 하위 페이지 확인
curl http://xwiki.com:8080/xwiki/rest/wikis/xwiki/spaces/Main/spaces/Blacklist/pages/Diagrams
```

### 3. 데이터베이스 확인 (고급)
```sql
-- XWiki 데이터베이스 접속
SELECT XWD_FULLNAME, XWD_PARENT
FROM xwikidoc
WHERE XWD_FULLNAME LIKE 'Main.Blacklist%'
ORDER BY XWD_FULLNAME;

-- 예상 결과:
-- Main.Blacklist                     (parent: Main.WebHome)
-- Main.Blacklist.Index               (parent: Main.Blacklist)
-- Main.Blacklist.Deployment          (parent: Main.Blacklist)
-- ...
```

---

## 📊 배포 통계

### 파일 크기
| 항목 | 크기 | 설명 |
|------|------|------|
| **XAR 패키지** | 40KB | 압축된 ZIP 파일 |
| **압축 해제** | 99KB | 12개 XML 파일 |
| **원본 섹션 파일** | 160KB | 11개 .txt 파일 합계 |

### 페이지 수
- **총 12개**: 부모 1개 + 하위 11개
- **PlantUML 다이어그램**: 5개 (Diagrams 페이지)
- **Mermaid 다이어그램**: 10개 (별도 파일, 미포함)
- **API 엔드포인트**: 37개 (API 페이지)
- **Grafana 임베딩**: 3개 (Monitoring 페이지)

### 기능별 페이지
| 카테고리 | 페이지 | 특징 |
|---------|--------|------|
| **정적 문서** | Index, Deployment, Architecture, API, Upgrade, Security, Troubleshooting, Appendix | 일반 XWiki 문법 |
| **시각화** | Diagrams | PlantUML 매크로 5개 |
| **동적 콘텐츠** | Dashboard | Velocity 템플릿 + API 호출 |
| **외부 임베딩** | Monitoring | Grafana iframe 3개 |

---

**생성일**: 2025-10-15
**버전**: 1.0
**작성자**: Blacklist Team
**파일 위치**: `/home/jclee/app/blacklist/docs/xwiki-sections/XWIKI_DEPLOYMENT_VISUAL.md`
