# AWM (Awesome Window Manager)

## 🪟 개요

**AWM (Awesome Window Manager)** = 리눅스용 타일링 윈도우 매니저

---

## 📊 특징

### 1. 타일링 윈도우 매니저 (Tiling WM)
- 창을 자동으로 타일처럼 배치 (겹치지 않음)
- 수동 크기 조절 거의 필요 없음
- 키보드 중심 조작

### 2. 경량 & 빠름
- C 언어 + Lua 스크립트
- 메모리 사용량: ~30MB
- CPU 사용량: 거의 0%

### 3. 고도의 커스터마이징
- Lua 스크립트로 모든 것 설정
- 테마, 레이아웃, 키바인딩 자유롭게 변경
- 위젯 추가 가능

---

## 🆚 다른 WM과 비교

| WM | 타입 | 설정 | 메모리 | 난이도 |
|----|------|------|--------|--------|
| **Awesome** | Tiling | Lua | 30MB | ⭐⭐⭐☆☆ |
| i3 | Tiling | 텍스트 | 20MB | ⭐⭐☆☆☆ |
| bspwm | Tiling | 셸 | 15MB | ⭐⭐⭐⭐☆ |
| GNOME | Floating | GUI | 800MB | ⭐☆☆☆☆ |
| KDE | Floating | GUI | 600MB | ⭐☆☆☆☆ |

---

## 🎯 사용 예시

### 레이아웃 예시
```
┌──────────┬──────────┐
│          │          │
│  Editor  │ Terminal │
│          │          │
├──────────┴──────────┤
│                     │
│      Browser        │
│                     │
└─────────────────────┘
```

### 키바인딩 (기본)
- `Mod4 + Enter`: 터미널 열기
- `Mod4 + j/k`: 창 포커스 이동
- `Mod4 + Shift + j/k`: 창 위치 이동
- `Mod4 + Space`: 레이아웃 변경
- `Mod4 + 1~9`: 워크스페이스 전환

---

## 🔧 설정 파일

### 위치
```bash
~/.config/awesome/rc.lua
```

### 예시 설정
```lua
-- 테마 설정
beautiful.init("~/.config/awesome/themes/default/theme.lua")

-- 키바인딩
awful.key({ modkey }, "Return", function()
    awful.spawn(terminal)
end)

-- 레이아웃
awful.layout.layouts = {
    awful.layout.suit.tile,
    awful.layout.suit.floating,
    awful.layout.suit.max
}
```

---

## 💡 왜 사용하나?

### 장점
✅ 키보드만으로 모든 작업
✅ 매우 빠름 (저사양에서도)
✅ 생산성 향상 (창 관리 자동)
✅ 고도의 커스터마이징

### 단점
❌ 학습 곡선 (초보자 어려움)
❌ GUI 설정 없음 (Lua 코딩 필요)
❌ 일부 앱과 호환성 문제

---

## 🎨 인기 설정

### 1. Copycats
- https://github.com/lcpz/awesome-copycats
- 바로 사용 가능한 테마 모음

### 2. AwesomeWM Dotfiles
- https://github.com/JavaCafe01/awesome-wm
- 현대적인 UI 디자인

### 3. Material Awesome
- https://github.com/material-shell/material-awesome
- Material Design 테마

---

## 🚀 설치 (Rocky Linux / RHEL)

```bash
# EPEL 저장소 활성화
sudo dnf install epel-release

# Awesome 설치
sudo dnf install awesome

# 로그아웃 후 로그인 화면에서 "Awesome" 세션 선택
```

---

## 📚 관련 도구

- **picom**: 컴포지터 (투명도, 그림자)
- **rofi**: 애플리케이션 런처
- **feh**: 배경화면 설정
- **alacritty**: 터미널 (Awesome과 찰떡)

---

## 🔗 공식 리소스

- 공식 사이트: https://awesomewm.org/
- GitHub: https://github.com/awesomeWM/awesome
- Wiki: https://awesomewm.org/doc/api/
- Reddit: https://reddit.com/r/awesomewm/

---

## 🤔 Awesome이 적합한 사람

✅ 개발자 / 시스템 관리자
✅ 키보드 중심 워크플로우 선호
✅ 저사양 컴퓨터 사용
✅ 커스터마이징 좋아함
✅ 생산성 중시

❌ GUI 설정 선호
❌ 마우스 중심 작업
❌ 학습 시간 없음
❌ 기본 데스크탑 환경 만족

---

**요약**: AWM = 리눅스용 경량 타일링 윈도우 매니저, 키보드 중심, 고성능, 고도의 커스터마이징 가능

**생성일**: 2025-10-15
