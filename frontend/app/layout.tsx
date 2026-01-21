import type { Metadata } from 'next';
import './globals.css';
import NavBar from '@/components/NavBar';
import { Providers } from './providers';

export const metadata: Metadata = {
  title: 'Blacklist Management Platform',
  description: '실시간 IP 블랙리스트 모니터링 및 관리 플랫폼',
  manifest: '/manifest.json',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko">
      <body className="bg-gray-50">
        <Providers>
          <NavBar />
          {children}
        </Providers>
      </body>
    </html>
  );
}
