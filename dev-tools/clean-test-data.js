#!/usr/bin/env node
/**
 * 테스트 데이터 제거 스크립트
 */

const testIPs = [
  'test.ip.for.verification',
  '192.0.2.100',     // TEST-NET-1 (RFC 5737)
  '198.51.100.50',   // TEST-NET-2 (RFC 5737)
  '203.0.113.1'      // TEST-NET-3 (RFC 5737)
];

async function cleanTestData() {
  console.log('테스트 데이터 제거 중...');

  // Get current IPs
  const getCmd = `npx wrangler kv:key get --namespace-id=4ff8d185b96748a68e5f5147df108999 "blacklist:ips"`;

  const { execSync } = require('child_process');

  try {
    const currentData = execSync(getCmd, { encoding: 'utf8' });
    const ips = JSON.parse(currentData);

    console.log(`현재 IP 수: ${ips.length}`);

    // Filter out test IPs
    const cleaned = ips.filter(ip => {
      const addr = ip.ip_address;

      // Remove test IPs
      if (testIPs.includes(addr)) {
        console.log(`제거: ${addr} (테스트 데이터)`);
        return false;
      }

      // Remove RFC 5737 test ranges
      if (addr.startsWith('192.0.2.') ||
          addr.startsWith('198.51.100.') ||
          addr.startsWith('203.0.113.')) {
        console.log(`제거: ${addr} (RFC 5737 테스트 범위)`);
        return false;
      }

      return true;
    });

    console.log(`\n정리 후 IP 수: ${cleaned.length}`);
    console.log(`제거된 IP 수: ${ips.length - cleaned.length}`);

    // Update KV
    const putCmd = `npx wrangler kv:key put --namespace-id=4ff8d185b96748a68e5f5147df108999 "blacklist:ips" '${JSON.stringify(cleaned)}'`;
    execSync(putCmd);

    console.log('✅ 테스트 데이터 제거 완료');

    // Show remaining IPs
    console.log('\n남은 IP 목록:');
    cleaned.forEach(ip => {
      console.log(`  - ${ip.ip_address}: ${ip.reason}`);
    });

  } catch (error) {
    console.error('오류:', error.message);
  }
}

cleanTestData();