# Blacklist Management Platform - Frontend

Next.js 15 + TypeScript + TailwindCSS로 구축된 현대적인 프론트엔드 애플리케이션

## 기술 스택

- **Next.js 15** - React 프레임워크 (App Router)
- **TypeScript** - 타입 안정성
- **TailwindCSS** - 유틸리티 CSS 프레임워크
- **React Query** - 서버 상태 관리
- **Axios** - HTTP 클라이언트
- **Zustand** - 클라이언트 상태 관리
- **Recharts** - 차트 라이브러리
- **Lucide React** - 아이콘 라이브러리

## 프로젝트 구조

````
frontend/
├── app/                    # Next.js App Router 페이지
│   ├── layout.tsx         # 루트 레이아웃
│   ├── page.tsx           # Dashboard (메인 페이지)
│   └── globals.css        # 전역 스타일
├── components/            # 재사용 가능한 컴포넌트
├── lib/                   # 유틸리티 및 API 클라이언트
│   └── api.ts            # Axios API 클라이언트
├── types/                 # TypeScript 타입 정의
│   └── index.ts          # 공통 타입
├── hooks/                 # Custom React Hooks
├── package.json          # 의존성 관리
├── tsconfig.json         # TypeScript 설정
├── tailwind.config.ts    # TailwindCSS 설정
└── next.config.ts        # Next.js 설정

## 시작하기

### 1. 의존성 설치

```bash
npm install
````

### 2. 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 파일에서 Flask API URL을 설정:

```
NEXT_PUBLIC_API_URL=http://localhost:2542
```

### 3. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 http://localhost:3001 접속

### 4. 프로덕션 빌드

```bash
npm run build
npm start
```

## Flask API와 통합

Next.js는 `next.config.ts`의 `rewrites` 설정을 통해 Flask API (포트 2542)와 통합됩니다:

```typescript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:2542/api/:path*',
    },
  ];
}
```

## 주요 기능

### Dashboard (`app/page.tsx`)

- 실시간 통계 표시 (전체 IP, 차단 IP, 신규 등록, 마지막 업데이트)
- 시스템 상태 모니터링
- 빠른 작업 메뉴

### API 클라이언트 (`lib/api.ts`)

- 통계 조회: `getStats()`
- IP 검색: `searchIP(ip)`
- 수집 내역: `getCollectionHistory()`
- 수집 트리거: `triggerCollection(startDate, endDate)`
- 시스템 상태: `getHealth()`
- 인증 상태: `getAuthStatus()`

## 개발 가이드

### 새 페이지 추가

1. `app/` 디렉토리에 새 폴더 생성
2. `page.tsx` 파일 작성
3. 예: `app/monitoring/page.tsx`

### 새 컴포넌트 추가

1. `components/` 디렉토리에 컴포넌트 파일 생성
2. TypeScript + React 코드 작성
3. 예: `components/StatCard.tsx`

### 새 API 엔드포인트 추가

1. `lib/api.ts`에 함수 추가
2. `types/index.ts`에 타입 정의
3. 컴포넌트에서 사용

## 스타일링

TailwindCSS 유틸리티 클래스 사용:

```tsx
<div className="bg-white rounded-lg p-6 shadow">
  <h3 className="text-2xl font-bold text-gray-900">타이틀</h3>
</div>
```

## 배포

### Docker 통합 (향후)

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

## 문제 해결

### CORS 에러

- `next.config.ts`의 rewrites 설정 확인
- Flask API가 실행 중인지 확인

### TypeScript 에러

```bash
npx tsc --noEmit
```

### 의존성 문제

```bash
rm -rf node_modules package-lock.json
npm install
```

## 라이선스

ISC
