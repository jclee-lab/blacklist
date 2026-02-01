# FRONTEND KNOWLEDGE BASE

**Generated:** 2026-01-17
**Role:** Dashboard UI (관리 인터페이스)
**Parent:** [../AGENTS.md](../AGENTS.md)

---

## OVERVIEW

Next.js 15 기반 관리 대시보드. **Air-Gap 호환** — 모든 API 호출은 프록시를 통해 수행.
Tailwind CSS v4 + Radix UI 컴포넌트 시스템.

---

## STRUCTURE

```
frontend/
├── app/                    # App Router (Pages)
│   ├── (auth)/             # 인증 필요 라우트
│   ├── ip-management/      # IP 관리 기능
│   ├── globals.css         # Tailwind v4 설정
│   └── page.tsx            # 대시보드 루트
├── components/             # React 컴포넌트
│   ├── ui/                 # Radix UI 기반 원자 컴포넌트
│   └── features/           # 기능별 컴포넌트
├── lib/                    # 유틸리티
│   └── api.ts              # ⚠️ 필수: API 프록시 클라이언트
├── types/                  # TypeScript 타입 정의
└── next.config.ts          # /api/* → :2542 리라이트
```

---

## WHERE TO LOOK

| 작업               | 위치                     | 비고                 |
| ------------------ | ------------------------ | -------------------- |
| **새 페이지 추가** | `app/<feature>/page.tsx` | → HOW TO 섹션        |
| **API 호출**       | `lib/api.ts`             | 모든 API 메서드 정의 |
| **UI 컴포넌트**    | `components/ui/`         | Radix 기반           |
| **스타일**         | `app/globals.css`        | Tailwind v4          |
| **프록시 설정**    | `next.config.ts`         | rewrites 규칙        |

---

## HOW TO: 새 페이지 추가

### 1. 라우트 폴더 생성

```
frontend/app/my-feature/
├── page.tsx           # Server Component (진입점)
└── MyFeatureClient.tsx # Client Component (인터랙션)
```

### 2. Server Component (page.tsx)

```tsx
// app/my-feature/page.tsx
import { MyFeatureClient } from './MyFeatureClient';

export default async function MyFeaturePage() {
  // 서버 사이드 데이터 페칭 가능
  return <MyFeatureClient />;
}
```

### 3. Client Component (인터랙티브 로직)

```tsx
// app/my-feature/MyFeatureClient.tsx
'use client';

import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function MyFeatureClient() {
  const { data, isLoading } = useQuery({
    queryKey: ['my-feature'],
    queryFn: () => api.get('/api/my-feature').then((r) => r.data),
  });

  if (isLoading) return <div>Loading...</div>;

  return <div>{/* UI */}</div>;
}
```

### 4. API 메서드 추가

```typescript
// lib/api.ts
export const getMyFeature = () => api.get('/api/my-feature').then((r) => r.data);
export const createMyFeature = (data: MyFeatureInput) =>
  api.post('/api/my-feature', data).then((r) => r.data);
```

### 5. 타입 정의

```typescript
// types/index.ts
export interface MyFeature {
  id: string;
  name: string;
  // ...
}
```

---

## CONVENTIONS (규약)

| 규약              | 내용                                        |
| ----------------- | ------------------------------------------- |
| **API 호출**      | `lib/api.ts` 통해서만 (직접 fetch 금지)     |
| **컴포넌트 분리** | `page.tsx` = Server, `*Client.tsx` = Client |
| **상태 관리**     | Zustand (전역 UI), React Query (서버 상태)  |
| **스타일링**      | Tailwind Utility만 (커스텀 CSS 금지)        |
| **빌드**          | `output: 'standalone'` (Docker 최적화)      |

---

## ANTI-PATTERNS (금지 사항)

| ❌ 금지                          | ✅ 대안               | 이유                |
| -------------------------------- | --------------------- | ------------------- |
| `fetch('http://localhost:2542')` | `api.get('/api/...')` | CORS, Air-gap 깨짐  |
| `fetch('/api/...')` 직접 사용    | `lib/api.ts` 래퍼     | 일관성, 에러 핸들링 |
| 커스텀 `.css` 파일               | Tailwind utility      | 프로젝트 정책       |
| 포트 하드코딩 (`2542`, `2543`)   | 환경변수 / rewrites   | 환경 의존성         |
| `pages/` 디렉토리                | `app/` (App Router)   | 마이그레이션 완료   |
| `any` / `unknown` 타입           | 명시적 타입           | strict 모드         |
| `as any`, `@ts-ignore`           | 적절한 타입 정의      | 타입 안전성         |

---

## KNOWN ISSUES (수정 필요)

### Hardcoded URL (1 violation)

| 파일             | 라인 | 문제              |
| ---------------- | ---- | ----------------- |
| `next.config.ts` | 7    | Hardcoded API URL |

**수정 방향**: `API_URL` 환경변수 사용

---

## COMPONENT PATTERNS

### Server vs Client Component 분리

```
app/feature/
├── page.tsx           # Server Component (데이터 페칭)
├── FeatureClient.tsx  # Client Component (인터랙션)
└── loading.tsx        # Suspense fallback
```

| 유형    | 파일명 패턴              | 용도                |
| ------- | ------------------------ | ------------------- |
| Server  | `page.tsx`, `layout.tsx` | 데이터 페칭, SEO    |
| Client  | `*Client.tsx`            | 상태, 이벤트, hooks |
| Loading | `loading.tsx`            | Suspense boundary   |

### 대형 컴포넌트 리팩토링 가이드

`IPManagementClient.tsx` (893L) 같은 대형 컴포넌트:

1. 로직별 custom hooks 분리
2. UI 섹션별 서브 컴포넌트 분리
3. E2E 테스트 유지 필수

---

## KEY FILES (핵심 파일)

| 파일                                       | Lines | 역할             | 주의사항           |
| ------------------------------------------ | ----- | ---------------- | ------------------ |
| `app/ip-management/IPManagementClient.tsx` | 893L  | IP 관리 UI       | ⚠️ 복잡            |
| `lib/api.ts`                               | 150L  | API 프록시       | 모든 API 호출 경유 |
| `next.config.ts`                           | 50L   | 빌드/프록시 설정 | rewrites 규칙      |
| `app/globals.css`                          | 100L  | Tailwind 설정    | v4 문법            |

---

## DEPLOYMENT

```
┌─────────────────────────────────────────┐
│          Frontend Container             │
│  ┌─────────┐         ┌───────────────┐  │
│  │  Nginx  │ ──────► │   Next.js     │  │
│  │ (proxy) │         │  (standalone) │  │
│  └─────────┘         └───────────────┘  │
│       ↓                                 │
│  supervisord.conf 로 프로세스 관리        │
└─────────────────────────────────────────┘
```

- **Nginx**: 정적 파일 서빙 + API 프록시
- **Next.js**: SSR/SSG 렌더링
- **Supervisor**: 단일 컨테이너 내 멀티 프로세스

---

## NOTES

- **SSL**: 프로덕션은 Traefik, 개발은 `frontend/ssl/` 인증서
- **테스트**: `tests/e2e/` (Playwright)
- **복잡한 파일**: `IPManagementClient.tsx` 수정 시 E2E 테스트 권장
