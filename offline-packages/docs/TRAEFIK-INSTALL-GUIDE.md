# 🌐 Traefik 오프라인 설치 가이드

## 📦 필요한 파일

```
traefik-offline.tar.gz    (48M)
```

## 🚀 설치 방법 (3분)

### 1단계: 파일 전송

```bash
# Air-gap 서버로 파일 전송
scp traefik-offline.tar.gz user@server:/opt/

# 서버 접속
ssh user@server
cd /opt/
```

### 2단계: 압축 해제

```bash
tar -xzf traefik-offline.tar.gz
cd traefik-offline/
```

### 3단계: 자동 설치

```bash
bash install-traefik.sh
```

**설치 완료!** (30초~1분 소요)

---

## ✅ 설치 확인

### 컨테이너 상태 확인
```bash
docker ps | grep traefik
```

### 대시보드 접속
```bash
# 브라우저에서 열기
http://서버IP:8080
```

### 네트워크 확인
```bash
docker network ls | grep traefik-public
```

---

## 📂 설치 후 파일 구조

```
traefik-offline/
├── install-traefik.sh           # 자동 설치 스크립트
├── traefik-20251030.tar         # Traefik Docker 이미지
├── traefik.yml                  # 주 설정 파일
├── traefik-nas-multihost.yml    # Docker Compose 파일
├── certs/                       # SSL 인증서 (빈 디렉토리)
├── dynamic/                     # 동적 설정
├── scripts/                     # 배포 스크립트
└── docs/                        # 문서
```

---

## 🔧 SSL 인증서 설정 (선택사항)

### Let's Encrypt 자동 발급 (인터넷 연결 필요)

**traefik.yml**에 이미 설정되어 있음:
```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      email: your-email@example.com
      storage: /etc/traefik/acme.json
      httpChallenge:
        entryPoint: web
```

### 수동 인증서 사용 (Air-gap 환경)

```bash
# 1. certs/ 디렉토리에 인증서 복사
cp your-domain.crt certs/
cp your-domain.key certs/

# 2. dynamic/tls.yml 생성
cat > dynamic/tls.yml << 'EOF'
tls:
  certificates:
    - certFile: /etc/traefik/certs/your-domain.crt
      keyFile: /etc/traefik/certs/your-domain.key
EOF

# 3. Traefik 재시작
docker restart traefik
```

---

## 🎯 Blacklist 연동

Traefik 설치 후 Blacklist 배포:

```bash
# Blacklist 패키지 압축 해제
tar -xzf blacklist.tar.gz
cd blacklist/

# 설치 (Traefik 자동 연동)
bash install.sh
```

Traefik가 자동으로 인식하는 labels:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.blacklist-https.rule=Host(`blacklist.nxtd.co.kr`)"
  - "traefik.http.routers.blacklist-https.entrypoints=websecure"
  - "traefik.http.routers.blacklist-https.tls=true"
```

---

## 🔍 문제 해결

### Traefik 시작 안됨

```bash
# 로그 확인
docker logs traefik

# 포트 충돌 확인
ss -tuln | grep -E ':(80|443|8080)'

# 설정 파일 검증
docker exec traefik traefik version
```

### 대시보드 접속 안됨

```bash
# 8080 포트 확인
curl http://localhost:8080/api/http/routers

# 방화벽 확인
firewall-cmd --list-ports
ufw status
```

### SSL 인증서 오류

```bash
# 인증서 권한 확인
ls -l certs/

# 동적 설정 확인
docker exec traefik cat /etc/traefik/dynamic/tls.yml
```

---

## 📊 Traefik 대시보드 사용법

### 접속
```
http://서버IP:8080
```

### 주요 화면
- **HTTP Routers**: 등록된 서비스 목록
- **Services**: 백엔드 서버 상태
- **Middlewares**: 미들웨어 설정
- **Entrypoints**: 포트 설정 (80, 443)

---

## ⚙️ 고급 설정

### Docker Compose 사용

```bash
# traefik-nas-multihost.yml 사용
docker compose -f traefik-nas-multihost.yml up -d

# 로그 확인
docker compose -f traefik-nas-multihost.yml logs -f
```

### 동적 설정 추가

```bash
# dynamic/ 디렉토리에 YAML 파일 생성
cat > dynamic/custom-middleware.yml << 'EOF'
http:
  middlewares:
    ratelimit:
      rateLimit:
        average: 100
        burst: 50
EOF

# Traefik가 자동으로 감지 (재시작 불필요)
```

---

## 📞 지원

- **Traefik 공식 문서**: https://doc.traefik.io/traefik/
- **로컬 README**: `./README.md`
- **로컬 CLAUDE.md**: `./CLAUDE.md`

---

## 🎉 설치 완료 확인

설치가 성공하면 다음과 같이 표시됩니다:

```
╔════════════════════════════════════════════════════════════════╗
║  ✅ Traefik Reverse Proxy Installed Successfully              ║
╚════════════════════════════════════════════════════════════════╝

📊 Access Points:
   • Dashboard:    http://localhost:8080
   • HTTP Entry:   http://localhost:80
   • HTTPS Entry:  https://localhost:443
```

---

**버전**: v3.0
**최종 수정**: 2025-10-30
**패키지 크기**: 48M
