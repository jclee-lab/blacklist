# FortiManager 자동 연동 설정

## 🚀 빠른 시작

```bash
# 1. 설정 파일 편집
vi .env.fortimanager

# 2. 정보 입력 (3가지만)
FMG_HOST=192.168.1.100
FMG_PASS=actual_password
API_URL=https://blacklist.nxtd.co.kr/api/fortinet/active-ips

# 3. 자동 설정 실행
source .env.fortimanager && bash scripts/setup-fmg-threat-feed-hosting.sh
```

**끝!** FortiManager가 자동으로:
- 5분마다 Blacklist API에서 IP 다운로드
- 로컬에 캐싱/호스팅
- FortiGate들에게 배포

## 📚 상세 가이드

**설정**: [docs/fortimanager-setup-guide.md](docs/fortimanager-setup-guide.md)

## ⚙️ 필요 사항

- FortiManager 7.4.1+ (호스팅 기능) ⚠️ 7.4.1부터 지원!
- FortiManager → Internet 연결
- FortiGate → Internet 불필요 ✅
