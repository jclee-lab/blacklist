'use client';

import { RefreshCw } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export default function LoadingSpinner({ message = '로딩 중...', size = 'md' }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-5 w-5',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <div className="flex items-center justify-center py-12">
      <RefreshCw className={`${sizeClasses[size]} animate-spin text-blue-500`} />
      {message && <span className="ml-3 text-gray-600">{message}</span>}
    </div>
  );
}
