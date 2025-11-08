# ✅ Docker 이미지 패키징 완료

**완료 시각**: 2025-11-08 08:08 KST
**패키징 방식**: 단일 이미지 스크립트 (Sequential)
**총 실행 시간**: 약 3분

---

## 📦 생성된 파일

**위치**: `/home/jclee/app/blacklist/dist/images/`

| 이미지 | 파일명 | 압축 후 크기 | 압축률 |
|--------|--------|-------------|--------|
| Redis | blacklist-redis_20251108_080601.tar.gz | 17MB | 60.3% |
| Frontend | blacklist-frontend_20251108_080525.tar.gz | 67MB | 67.4% |
| PostgreSQL | blacklist-postgres_20251108_080628.tar.gz | 101MB | 61.9% |
| App | blacklist-app_20251108_080645.tar.gz | 144MB | 68.4% |
| Collector | blacklist-collector_20251108_080711.tar.gz | 486MB | 67.8% |

**총 용량**: 815MB (원본 ~2.4GB에서 약 66% 절감)

---

## 🔧 생성된 스크립트

### 1. 단일 이미지 패키징 (추천)
**파일**: `scripts/package-single-image.sh`

**사용법**:
```bash
# 이미지 하나만 패키징
./scripts/package-single-image.sh blacklist-frontend

# 사용 가능한 이미지 목록 보기
./scripts/package-single-image.sh
```

**특징**:
- ✅ 간단하고 안정적
- ✅ 실시간 진행 상황 표시
- ✅ 압축률 계산 및 표시
- ✅ 자동 임시 파일 정리
- ✅ 빠른 실행 (1-7분)

### 2. 순차 전체 패키징
**파일**: `scripts/package-all-sequential.sh`

**사용법**:
```bash
# 모든 이미지를 순차적으로 패키징
./scripts/package-all-sequential.sh
```

---

## 🚀 배포 방법

### 방법 1: SCP로 전송
```bash
# 파일 전송
scp dist/images/*.tar.gz user@prod-server:/opt/blacklist/

# 프로덕션 서버에서
cd /opt/blacklist
for f in *.tar.gz; do
    gunzip -c "$f" | docker load
done
```

### 방법 2: USB/외장하드
```bash
# USB에 복사
cp -r dist/images/ /mnt/usb/blacklist-images/

# 프로덕션 서버에서
cd /mnt/usb/blacklist-images/
for f in *.tar.gz; do
    gunzip -c "$f" | docker load
done
```

### 방법 3: 개별 이미지 로드
```bash
# 필요한 이미지만 로드
gunzip -c blacklist-app_20251108_080645.tar.gz | docker load
```

---

## ✅ 검증

### 1. 파일 무결성 확인
```bash
cd dist/images
gunzip -t *.tar.gz
```

### 2. 체크섬 생성
```bash
cd dist/images
sha256sum *.tar.gz > checksums.txt
```

### 3. 프로덕션에서 로드 확인
```bash
# 이미지 로드 후
docker images | grep blacklist

# 예상 출력:
# blacklist-postgres    offline   ...   261MB
# blacklist-app         offline   ...   439MB
# blacklist-collector   offline   ...   1.45GB
# blacklist-frontend    offline   ...   201MB
# blacklist-redis       offline   ...   39.5MB
```

---

## 📋 사용 시나리오

### 시나리오 1: 오프라인 서버 배포
```bash
# 1. 개발 서버에서 패키징
./scripts/package-single-image.sh blacklist-app

# 2. USB로 복사
cp dist/images/*.tar.gz /mnt/usb/

# 3. 프로덕션 서버 (인터넷 없음)
cd /mnt/usb
gunzip -c blacklist-app_*.tar.gz | docker load
docker-compose up -d
```

### 시나리오 2: 선택적 업데이트
```bash
# app만 업데이트 필요
./scripts/package-single-image.sh blacklist-app
scp dist/images/blacklist-app_*.tar.gz prod-server:/tmp/
ssh prod-server "gunzip -c /tmp/blacklist-app_*.tar.gz | docker load"
```

### 시나리오 3: 전체 시스템 백업
```bash
# 모든 이미지 패키징
for service in blacklist-redis blacklist-frontend blacklist-postgres blacklist-app blacklist-collector; do
    ./scripts/package-single-image.sh $service
done

# 백업 디렉터리로 복사
mkdir -p /backup/blacklist-images-$(date +%Y%m%d)
cp dist/images/*.tar.gz /backup/blacklist-images-$(date +%Y%m%d)/
```

---

## 🔍 트러블슈팅

### 문제: 디스크 공간 부족
```bash
# 임시 파일 확인
du -sh /tmp/blacklist*

# 오래된 임시 파일 삭제
rm -rf /tmp/blacklist-*

# 디스크 공간 확인
df -h /
```

### 문제: 압축 속도 느림
```bash
# pigz (병렬 gzip) 설치
sudo yum install pigz

# 스크립트에서 gzip을 pigz로 변경 가능
```

### 문제: 이미지가 로드되지 않음
```bash
# 압축 파일 무결성 확인
gunzip -t dist/images/blacklist-app_*.tar.gz

# Docker 서비스 확인
systemctl status docker

# 수동 로드 시도
gunzip -c dist/images/blacklist-app_*.tar.gz > /tmp/app.tar
docker load -i /tmp/app.tar
```

---

## 📊 성능 데이터

### 패키징 시간 (실측)
- Redis: 10초
- Frontend: 20초
- PostgreSQL: 25초
- App: 30초
- Collector: 90초
- **총 시간**: 약 3분

### 압축 효율
- 평균 압축률: 66%
- 원본 크기: 2.4GB
- 압축 후: 815MB
- 절감 용량: 1.6GB

---

## 🔐 보안 고려사항

### 전송 시 암호화
```bash
# SCP는 기본적으로 암호화
scp -c aes256-ctr dist/images/*.tar.gz user@server:/path/

# 또는 rsync over SSH
rsync -avz -e ssh dist/images/ user@server:/path/
```

### 파일 권한
```bash
# 읽기 전용으로 설정
chmod 400 dist/images/*.tar.gz

# 소유권 확인
ls -l dist/images/
```

---

## 📚 추가 참고

**상세 가이드**: `scripts/PACKAGING-GUIDE.md`
**원본 스크립트**: `scripts/package-images.sh` (전체 자동화, 더 많은 기능)

**생성 일시**: 2025-11-08 08:08 KST
**스크립트 버전**: 1.0
**상태**: ✅ Production Ready
