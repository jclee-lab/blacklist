# XWiki Import 스크립트 변경 이력

## v2.0 (2025-10-14)

### 🎉 주요 개선사항

#### 1. 경로 추적 기능
- 스크립트 실행 위치 명확히 표시
- 디렉토리 이동 과정 시각화
- `cd` 명령어처럼 현재 위치 추적

**Before (v1.0):**
```
[INFO] 페이지 생성 중...
```

**After (v2.0):**
```
[INFO] 📂 스크립트 위치: /home/jclee/app/blacklist/docs/xwiki-sections
[INFO] 📂 현재 디렉토리: /home/jclee
[INFO] 📂 디렉토리 이동: /home/jclee → /home/jclee/app/blacklist/docs/xwiki-sections
[✓] 📂 작업 디렉토리: /home/jclee/app/blacklist/docs/xwiki-sections
```

#### 2. 섹션 정보 표시
- 각 페이지의 용도를 한눈에 파악
- 파일명과 XWiki 페이지명 매핑 명확화
- 실시간 생성 진행상황에 설명 추가

**Before (v1.0):**
```
├── Index ✓
├── Deployment ✓
```

**After (v2.0):**
```
├── 📑 목차 (Index) ← 00-index.txt ✓ // 전체 문서 목차
├── 🚀 1. 설치 및 배포 (Deployment) ← 01-deployment.txt ✓ // 오프라인 패키지 설치, Docker 배포
```

#### 3. 파일 크기 및 메타정보
- 통합 파일 크기와 라인 수 표시
- 각 섹션 파일 크기 표시
- 최종 구조 요약에 파일 크기 포함

**Before (v1.0):**
```
Main.Blacklist (부모)
├── Main.Blacklist.Architecture
```

**After (v2.0):**
```
Main.Blacklist (부모 - 통합 문서 72KB)
├── Main.Blacklist.Architecture (10K) // 5개 컨테이너 구성, 차단 로직, ERD
```

#### 4. 시각적 개선
- 이모지로 섹션 구분 (📑, 🚀, 🏗️, 📡, 📊, 🔄, 🔐, 🔧, 📝)
- 색상 코드 최적화 (Cyan, Yellow, Blue)
- 트리 구조 더 명확하게 표시

#### 5. 에러 처리 개선
- 파일 존재 여부 확인 강화
- 경로 오류 시 상세 메시지
- 403 에러 시 해결 방법 자동 안내

---

## v1.0 (2025-10-13)

### 초기 릴리스

#### 기능
- XWiki REST API 연동
- 일반 사용자 권한 지원
- 자동 권한 체크
- 9개 하위 페이지 자동 생성
- PlantUML 다이어그램 13개 포함

#### 파일 구성
- `xwiki-import.sh` - 통합 스크립트
- `check-xwiki-permissions.sh` - 권한 체크 전용
- `create-xwiki-pages.sh` - 생성 전용
- `README_XWIKI_IMPORT.md` - 사용 가이드

---

## 마이그레이션 가이드 (v1.0 → v2.0)

### 변경 사항 없음
v1.0 스크립트는 그대로 사용 가능합니다. v2.0은 **출력 형식만 개선**되었으며, 사용법은 동일합니다.

### 권장 사항
- 최신 `xwiki-import.sh` 사용 (더 명확한 출력)
- 기존 환경 변수 그대로 사용 가능
- 추가 설치 불필요

---

## 향후 계획

### v2.1 (예정)
- [ ] 페이지 수정 모드 추가 (업데이트 지원)
- [ ] 배치 모드 (여러 프로젝트 한번에)
- [ ] 로그 파일 자동 저장

### v3.0 (검토 중)
- [ ] GUI 인터페이스
- [ ] 설정 파일 지원 (YAML)
- [ ] 롤백 기능

---

**작성: 정보보안팀**
**최종 업데이트: 2025-10-14**
