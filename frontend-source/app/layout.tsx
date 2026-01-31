import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";
import Providers from "./providers";
import { Shield } from "lucide-react";

export const metadata: Metadata = {
  title: "Blacklist Platform",
  description: "IP Blacklist Management System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-100">
        <Providers>
          <nav className="bg-gray-900 text-white shadow-lg">
            <div className="max-w-7xl mx-auto px-4">
              <div className="flex items-center justify-between h-16">
                <div className="flex items-center space-x-8">
                  <Link href="/" className="flex items-center space-x-2 font-bold text-xl">
                    <Shield className="w-6 h-6 text-blue-500" />
                    <span>Blacklist Platform</span>
                  </Link>
                  <div className="hidden md:flex space-x-4">
                    <Link href="/" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-800 hover:text-white transition-colors">
                      대시보드
                    </Link>
                    <Link href="/ip-management" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-800 hover:text-white transition-colors">
                      IP관리
                    </Link>
                    <Link href="/fortinet" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-800 hover:text-white transition-colors">
                      FortiGate
                    </Link>
                    <Link href="/collection" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-800 hover:text-white transition-colors">
                      데이터수집
                    </Link>
                    <Link href="/database" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-800 hover:text-white transition-colors">
                      데이터베이스
                    </Link>
                    <Link href="/monitoring" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-800 hover:text-white transition-colors">
                      모니터링
                    </Link>
                    <Link href="/settings" className="px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-800 hover:text-white transition-colors">
                      설정
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </nav>
          <main className="max-w-7xl mx-auto px-4 py-8">
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}
