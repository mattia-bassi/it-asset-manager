import React from 'react';
import type { ComponentType } from 'react';

const BORDER_CLASSES: Record<string, string> = {
  yellow: 'border-l-yellow-400',
  green: 'border-l-green-500',
  red: 'border-l-red-500',
  blue: 'border-l-blue-500',
  purple: 'border-l-purple-500',
  orange: 'border-l-orange-500',
};

const ICON_CLASSES: Record<string, string> = {
  yellow: 'text-yellow-500',
  green: 'text-green-500',
  red: 'text-red-500',
  blue: 'text-blue-500',
  purple: 'text-purple-500',
  orange: 'text-orange-500',
};

export interface StatsCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: ComponentType<{ className?: string }>;
  gradient: 'yellow' | 'green' | 'red' | 'blue' | 'purple' | 'orange';
  badge?: {
    text: string;
    variant: 'success' | 'warning';
  };
}

export default function StatsCard({
  title,
  value,
  subtitle,
  icon: Icon,
  gradient,
  badge,
}: StatsCardProps) {
  const borderClass = BORDER_CLASSES[gradient] ?? BORDER_CLASSES.yellow;
  const iconClass = ICON_CLASSES[gradient] ?? ICON_CLASSES.yellow;

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border border-gray-100 border-l-4 ${borderClass} hover:shadow-md transition-all duration-200`}
    >
      <div className="flex items-center justify-between p-5">
        <div>
          <h3 className="text-4xl font-bold text-gray-800">{value}</h3>
          <p className="text-sm text-gray-500 mt-1">{title}</p>
          {subtitle && (
            <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>
          )}
          {badge && (
            <div className="mt-2">
              <span
                className={`inline-block text-xs px-3 py-1 rounded-full font-semibold ${
                  badge.variant === 'success'
                    ? 'bg-green-50 text-green-700'
                    : 'bg-amber-50 text-amber-700'
                }`}
              >
                {badge.variant === 'success' ? '✓ ' : '⚠️ '}
                {badge.text}
              </span>
            </div>
          )}
        </div>
        <Icon className={`w-10 h-10 ${iconClass} opacity-80`} />
      </div>
    </div>
  );
}
