import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  // API rewrites는 제거 - 클라이언트에서 NEXT_PUBLIC_API_URL 환경 변수 직접 사용
};

export default nextConfig;
