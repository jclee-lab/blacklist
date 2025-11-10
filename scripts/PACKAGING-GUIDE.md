# Docker Image Packaging Guide

## 📦 개요

이 가이드는 Blacklist 시스템의 Docker 이미지를 오프라인 배포용으로 패키징하는 방법을 설명합니다.

## 🎯 목적

- 네트워크가 제한된 환경으로 배포
- 에어갭(Air-gapped) 환경 배포
- 버전 관리 및 백업
- 대용량 이미지 효율적 전송

## 🔧 사전 준비

### 시스템 요구사항
- Docker 설치됨
- gzip 유틸리티
- 최소 5GB 여유 디스크 공간 (압축 파일 저장용)

### 이미지 빌드 확인
```bash
# 모든 이미지가 빌드되어 있는지 확인
docker images | grep blacklist

# 이미지가 없으면 빌드
docker-compose build
```

## 📋 패키징 스크립트

### 파일 위치
```
scripts/package-images.sh
```

### 기능
1. ✅ 의존성 검증 (docker, gzip)
2. ✅ 이미지 존재 확인
3. ✅ Docker 이미지 저장 (tar)
4. ✅ gzip 압축 (평균 65% 절감)
5. ✅ Manifest 생성 (JSON)
6. ✅ 자동 배포 스크립트 생성

## 🚀 사용법

### 1. 기본 실행
```bash
cd /home/jclee/app/blacklist
./scripts/package-images.sh
```

**출력 디렉터리**: `dist/images/` (기본값)

### 2. 커스텀 출력 디렉터리
```bash
./scripts/package-images.sh /path/to/custom/output
```

### 3. 백그라운드 실행 (대용량 이미지)
```bash
nohup ./scripts/package-images.sh > package.log 2>&1 &

# 진행 상황 확인
tail -f package.log
```

## 📊 예상 패키징 시간 및 크기

| 서비스 | 원본 크기 | 압축 후 | 절감률 | 예상 시간 |
|--------|----------|---------|--------|----------|
| postgres | 261MB | ~80MB | 69% | 1-2분 |
| app | 439MB | ~140MB | 68% | 2-3분 |
| collector | 1.45GB | ~450MB | 69% | 5-7분 |
| frontend | 201MB | ~67MB | 67% | 1-2분 |
| redis | 39MB | ~15MB | 62% | 30초 |
| **합계** | **~2.4GB** | **~750MB** | **69%** | **10-15분** |

## 📁 생성되는 파일

### 패키징 디렉터리 구조
```
dist/images/
├── blacklist-postgres_YYYYMMDD_HHMMSS.tar.gz
├── blacklist-app_YYYYMMDD_HHMMSS.tar.gz
├── blacklist-collector_YYYYMMDD_HHMMSS.tar.gz
├── blacklist-frontend_YYYYMMDD_HHMMSS.tar.gz
├── blacklist-redis_YYYYMMDD_HHMMSS.tar.gz
├── manifest_YYYYMMDD_HHMMSS.json
└── deploy_YYYYMMDD_HHMMSS.sh
```

### Manifest 파일 (예시)
```json
{
  "packaging_date": "2025-11-08T04:50:00+09:00",
  "packaging_host": "rocky-dev",
  "packaging_user": "jclee",
  "images": [
    {
      "service": "blacklist-postgres",
      "image": "blacklist-postgres:offline",
      "image_id": "sha256:bb6fda...",
      "image_size": 274000000,
      "created": "2025-11-08T01:22:39+09:00",
      "archive_file": "blacklist-postgres_20251108_045000.tar.gz"
    }
  ]
}
```

## 🚚 배포 방법

### 1. 패키징된 파일 전송
```bash
# SCP로 전송
scp -r dist/images/ user@target-server:/opt/blacklist-images/

# 또는 USB/외장하드로 복사
cp -r dist/images/ /mnt/usb/blacklist-images/
```

### 2. 대상 서버에서 이미지 로드
```bash
# 패키징 디렉터리로 이동
cd /opt/blacklist-images/

# 자동 배포 스크립트 실행
./deploy_YYYYMMDD_HHMMSS.sh
```

### 3. 수동 로드 (필요시)
```bash
# 개별 이미지 로드
gunzip -c blacklist-postgres_20251108_045000.tar.gz | docker load

# 모든 이미지 로드
for archive in *.tar.gz; do
    echo "Loading $archive..."
    gunzip -c "$archive" | docker load
done
```

### 4. 이미지 확인
```bash
docker images | grep blacklist
```

### 5. 서비스 시작
```bash
docker-compose up -d
```

## 🔍 문제 해결

### 패키징 중 디스크 공간 부족
```bash
# 임시 파일 정리
docker system prune -a

# 다른 디스크로 변경
./scripts/package-images.sh /mnt/external/images
```

### 압축 속도가 느림
```bash
# gzip 대신 빠른 압축 (약간 큰 파일)
# 스크립트 내 gzip을 pigz로 변경
sudo yum install pigz

# 또는 압축 없이 저장 (스크립트 수정 필요)
docker save blacklist-app:offline -o app.tar
```

### 특정 이미지만 패키징
```bash
# 스크립트를 수정하여 SERVICES 배열에서 제외
# 또는 수동으로 패키징:
docker save -o postgres.tar blacklist-postgres:offline
gzip postgres.tar
```

## 📝 베스트 프랙티스

### 1. 정기 백업
```bash
# Cron 작업으로 주간 백업
0 2 * * 0 cd /home/jclee/app/blacklist && ./scripts/package-images.sh /backup/images/$(date +\%Y\%m\%d)
```

### 2. 버전 관리
```bash
# Git 태그와 함께 패키징
git tag -a v3.3.9 -m "Release 3.3.9"
./scripts/package-images.sh /releases/v3.3.9
```

### 3. 배포 전 검증
```bash
# 패키징된 이미지 무결성 확인
gunzip -t blacklist-app_*.tar.gz

# SHA256 체크섬 생성
sha256sum *.tar.gz > checksums.txt
```

### 4. 네트워크 대역폭 고려
```bash
# 작은 이미지부터 전송 (redis → postgres → frontend → app → collector)
# 또는 병렬 전송
parallel scp {} user@server:/opt/images/ ::: *.tar.gz
```

## 🔐 보안 고려사항

### 1. 이미지 스캔 (패키징 전)
```bash
# Trivy로 취약점 스캔
trivy image blacklist-app:offline
```

### 2. 전송 암호화
```bash
# SCP with encryption
scp -c aes256-ctr dist/images/* user@server:/opt/images/
```

### 3. 접근 권한
```bash
# 패키징된 파일 권한 설정
chmod 600 dist/images/*.tar.gz
```

## 📚 추가 리소스

### 스크립트 수정
패키징 로직을 커스터마이징하려면:
```bash
vi scripts/package-images.sh
```

### 로그 위치
- 백그라운드 실행: `nohup.out` 또는 지정한 로그 파일
- 스크립트 내부 로그: `/tmp/package-*.log`

### Docker 저장 공간 위치
```bash
# Docker 데이터 디렉터리 확인
docker info | grep "Docker Root Dir"
```

## ✅ 체크리스트

배포 전 확인사항:
- [ ] 모든 이미지 빌드 완료
- [ ] 충분한 디스크 공간 (최소 5GB)
- [ ] 패키징 스크립트 실행 권한 확인
- [ ] 대상 서버 Docker 설치 확인
- [ ] 네트워크/전송 방법 준비
- [ ] Manifest 파일 확인
- [ ] 배포 스크립트 테스트

## 🆘 지원

문제 발생 시:
1. 로그 파일 확인: `/tmp/package*.log`
2. Docker 상태 확인: `docker info`
3. 디스크 공간 확인: `df -h`
4. 이미지 존재 확인: `docker images`

---

**마지막 업데이트**: 2025-11-08
**스크립트 버전**: 1.0
**작성자**: jclee
