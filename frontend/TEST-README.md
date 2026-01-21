# Frontend UI/UX Automated Testing

이 프로젝트는 **Playwright**, **Vitest**, **Testing Library**를 사용한 포괄적인 UI/UX 자동화 테스트를 포함합니다.

## 📦 설치된 도구

### 1. **Playwright** - E2E 테스트
- 브라우저 자동화 테스트 (Chromium, Firefox, WebKit)
- 모바일 뷰포트 테스트
- 접근성 테스트
- 성능 테스트
- 비주얼 리그레션 테스트

### 2. **Vitest** - 단위 테스트
- Jest 대체 (빠른 실행 속도)
- React 컴포넌트 테스트
- 코드 커버리지

### 3. **Testing Library** - 컴포넌트 테스트
- 사용자 중심 테스트
- React 컴포넌트 렌더링
- 이벤트 시뮬레이션

## 🚀 테스트 실행 방법

### 단위 테스트 (Vitest)

```bash
# 단일 실행
npm run test

# Watch 모드 (개발 중)
npm run test:watch

# UI 모드 (브라우저에서 확인)
npm run test:ui

# 커버리지 리포트
npm run test:coverage
```

### E2E 테스트 (Playwright)

```bash
# 모든 E2E 테스트 실행
npm run test:e2e

# UI 모드 (브라우저에서 확인)
npm run test:e2e:ui

# Headed 모드 (브라우저 표시)
npm run test:e2e:headed

# 디버그 모드
npm run test:e2e:debug

# 리포트 보기
npm run test:e2e:report

# 모든 테스트 실행 (Unit + E2E)
npm run test:all
```

### 특정 테스트만 실행

```bash
# 특정 파일
npx playwright test e2e/homepage.spec.ts

# 특정 테스트
npx playwright test -g "should display the page title"

# 접근성 테스트만
npx playwright test e2e/accessibility.spec.ts

# 성능 테스트만
npx playwright test e2e/performance.spec.ts

# 비주얼 리그레션 테스트만
npx playwright test --grep @visual
```

## 📁 테스트 파일 구조

```
frontend/
├── __tests__/              # 단위 테스트 (Vitest)
│   └── components/
│       └── NavBar.test.tsx
├── e2e/                    # E2E 테스트 (Playwright)
│   ├── homepage.spec.ts
│   ├── ip-management.spec.ts
│   ├── accessibility.spec.ts
│   ├── performance.spec.ts
│   └── visual-regression.spec.ts
├── playwright.config.ts    # Playwright 설정
├── vitest.config.ts        # Vitest 설정
└── vitest.setup.ts         # Vitest 설정 파일
```

## 🎯 작성된 테스트

### ✅ 단위 테스트 (Vitest)
- **NavBar Component** (`__tests__/components/NavBar.test.tsx`)
  - ✓ 로고 렌더링
  - ✓ 메뉴 아이템 렌더링
  - ✓ 시스템 상태 표시
  - ✓ 모바일 메뉴 토글
  - ✓ 네비게이션 링크 확인

### 🌐 E2E 테스트 (Playwright)

#### Homepage (`e2e/homepage.spec.ts`)
- ✓ 페이지 타이틀
- ✓ NavBar 로고
- ✓ 네비게이션 메뉴
- ✓ 시스템 상태
- ✓ 페이지 간 네비게이션
- ✓ 모바일 메뉴 토글
- ✓ 모바일 네비게이션

#### 페이지별 테스트 (`e2e/ip-management.spec.ts`)
- ✓ IP Management 페이지
- ✓ Database 페이지
- ✓ Collection 페이지
- ✓ Monitoring 페이지
- ✓ FortiGate 페이지

#### 접근성 테스트 (`e2e/accessibility.spec.ts`)
- ✓ 시맨틱 HTML
- ✓ 이미지 alt 텍스트
- ✓ ARIA 레이블
- ✓ 키보드 네비게이션

#### 성능 테스트 (`e2e/performance.spec.ts`)
- ✓ 페이지 로딩 시간 (< 5초)
- ✓ 콘솔 에러 확인
- ✓ 이미지 로딩

#### 비주얼 리그레션 (`e2e/visual-regression.spec.ts`)
- ✓ 홈페이지 데스크톱 뷰
- ✓ 홈페이지 모바일 뷰
- ✓ 모바일 메뉴 열린 상태
- ✓ IP Management 페이지
- ✓ 네비게이션 호버 상태
- ✓ NavBar 컴포넌트
- ✓ 시스템 상태 인디케이터
- ✓ 반응형 디자인 (5가지 뷰포트)

## 📊 CI/CD 통합

### GitHub Actions 워크플로우

3개의 자동화된 워크플로우가 추가되었습니다:

#### 1. Frontend Tests (`.github/workflows/frontend-tests.yml`)
- **Unit Tests**: Vitest로 컴포넌트 테스트
- **E2E Tests**: Playwright로 전체 시나리오 테스트
- **Accessibility Tests**: 접근성 검증
- **Performance Tests**: 성능 측정

#### 2. Visual Regression (`.github/workflows/visual-regression.yml`)
- 스크린샷 비교로 UI 변경 감지
- PR마다 자동 실행
- 베이스라인 이미지 관리

### 트리거 조건
- `frontend/` 디렉토리 변경 시 자동 실행
- PR 생성/업데이트 시
- `master`, `main`, `develop` 브랜치 푸시 시

## 🔧 설정 파일

### `playwright.config.ts`
```typescript
- 5개 브라우저/디바이스 프로젝트
- HTML/JSON 리포터
- 실패 시 스크린샷/비디오
- baseURL: http://localhost:2543
- 자동 dev 서버 시작
```

### `vitest.config.ts`
```typescript
- jsdom 환경
- React 플러그인
- 커버리지 설정 (v8)
- @ 경로 alias
```

## 📈 커버리지 목표

- **단위 테스트**: 80%+ 커버리지
- **E2E 테스트**: 주요 사용자 플로우 100%
- **접근성**: WCAG 2.1 AA 준수
- **성능**: 페이지 로딩 < 5초

## 🎨 비주얼 리그레션 베이스라인 업데이트

```bash
# 베이스라인 이미지 업데이트
npx playwright test --grep @visual --update-snapshots

# 특정 테스트만 업데이트
npx playwright test e2e/visual-regression.spec.ts --update-snapshots
```

## 🐛 디버깅

### Playwright 디버깅

```bash
# Inspector로 디버그
npm run test:e2e:debug

# Trace 뷰어
npx playwright show-trace trace.zip
```

### Vitest 디버깅

```bash
# UI 모드로 디버깅
npm run test:ui
```

## 📝 새 테스트 작성 가이드

### 단위 테스트 예제
```typescript
// __tests__/components/MyComponent.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import MyComponent from '../../components/MyComponent';

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });
});
```

### E2E 테스트 예제
```typescript
// e2e/my-feature.spec.ts
import { test, expect } from '@playwright/test';

test.describe('My Feature', () => {
  test('should work', async ({ page }) => {
    await page.goto('/my-page');
    await expect(page.getByText('Expected')).toBeVisible();
  });
});
```

## 🔗 참고 자료

- [Playwright 공식 문서](https://playwright.dev/)
- [Vitest 공식 문서](https://vitest.dev/)
- [Testing Library 공식 문서](https://testing-library.com/)
- [Next.js Testing](https://nextjs.org/docs/testing)

## 📌 다음 단계

1. ✅ 기본 테스트 설정 완료
2. ⏳ 추가 페이지 테스트 작성
3. ⏳ API 모킹 (MSW) 추가
4. ⏳ Storybook 통합
5. ⏳ 시각적 회귀 테스트 베이스라인 구축

---

**테스트 작성 원칙**
- 사용자 관점에서 테스트 작성
- 구현 세부사항이 아닌 동작 테스트
- 명확하고 의미 있는 테스트 이름
- 독립적이고 반복 가능한 테스트
