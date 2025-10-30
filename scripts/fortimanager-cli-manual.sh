#!/bin/bash
#
# FortiManager CLI Manual Configuration Generator
# FortiManager 7.4.7 External Resource 설정
#
# Usage:
#   1. 이 스크립트 실행하여 명령어 생성
#   2. FortiManager SSH 접속
#   3. 생성된 명령어 복사/붙여넣기

cat << 'EOF'
========================================
FortiManager 7.4.7 CLI Configuration
========================================

Step 1: External Resource 등록
--------------------------------
config system external-resource
    edit "NXTD-Blacklist"
        set type address
        set category 193
        set resource "https://blacklist.nxtd.co.kr/api/fortinet/active-ips"
        set status enable
        set comments "NXTD Blacklist - Auto-updated"
    next
end

Step 2: ADOM에서 Address Object 생성
--------------------------------
config pm config adom root obj firewall address
    edit "NXTD-Blacklist"
        set type external-resource
        set external-resource "NXTD-Blacklist"
        set comment "NXTD Blacklist External Resource"
    next
end

Step 3: Policy Package에 할당
--------------------------------
# GUI에서:
# Policy & Objects > Addresses > NXTD-Blacklist
# Firewall Policy > New Policy > Destination: NXTD-Blacklist > Action: Deny

Step 4: 확인
--------------------------------
diagnose system external-resource list
diagnose system external-resource status NXTD-Blacklist
diagnose system external-resource refresh NXTD-Blacklist

========================================
⚠️ 중요 사항
========================================

1. FortiManager 7.4.7에서는 URL 직접 pull이 안될 수 있음
   → Bash script 자동화 사용 권장:
     bash scripts/fortimanager-hosted-upload.sh

2. FortiGate는 FortiManager에서 pull (fmg://)
   → 인터넷 접근 불필요

3. 주기적 업데이트는 cron 설정:
   */5 * * * * /path/to/fortimanager-hosted-upload.sh

========================================
자동화 스크립트 사용 (권장)
========================================

export FMG_HOST="192.168.1.100"
export FMG_USER="admin"
export FMG_PASS="your_password"

# 즉시 실행
bash scripts/fortimanager-hosted-upload.sh

# Cron 등록 (5분마다)
(crontab -l 2>/dev/null; echo "*/5 * * * * cd /home/jclee/app/blacklist && bash scripts/fortimanager-hosted-upload.sh >> /var/log/fmg-update.log 2>&1") | crontab -

========================================

EOF
