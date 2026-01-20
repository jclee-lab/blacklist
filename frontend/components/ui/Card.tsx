'use client';

import { LucideIcon } from 'lucide-react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  'data-testid'?: string;
}

export function Card({ children, className = '', padding = 'md', 'data-testid': testId }: CardProps) {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  };

  return (
    <div 
      className={`bg-white rounded-xl shadow-lg ${paddingClasses[padding]} ${className}`}
      data-testid={testId}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  title: string;
  subtitle?: string;
  icon?: LucideIcon;
  iconColor?: string;
  actions?: React.ReactNode;
}

export function CardHeader({ title, subtitle, icon: Icon, iconColor = 'text-blue-600', actions }: CardHeaderProps) {
  return (
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center space-x-3">
        {Icon && <Icon className={`h-6 w-6 ${iconColor}`} />}
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="flex items-center space-x-2">{actions}</div>}
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  iconBg?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  loading?: boolean;
  'data-testid'?: string;
}

export function StatCard({ 
  title, 
  value, 
  icon: Icon, 
  iconBg = 'bg-blue-500', 
  trend,
  loading,
  'data-testid': testId
}: StatCardProps) {
  if (loading) {
    return (
      <Card data-testid={testId}>
        <div className="flex items-center justify-between animate-pulse">
          <div className="flex-1">
            <div className="h-4 bg-gray-200 rounded w-20 mb-2" />
            <div className="h-8 bg-gray-200 rounded w-24" />
          </div>
          <div className="h-12 w-12 bg-gray-200 rounded-xl" />
        </div>
      </Card>
    );
  }

  return (
    <Card data-testid={testId}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 font-medium">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
          {trend && (
            <p className={`text-xs mt-1 ${trend.isPositive ? 'text-green-600' : 'text-red-600'}`}>
              {trend.isPositive ? '+' : ''}{trend.value}%
            </p>
          )}
        </div>
        <div className={`${iconBg} p-3 rounded-xl text-white`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </Card>
  );
}
