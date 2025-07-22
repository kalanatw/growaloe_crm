import React from 'react';
import { CheckCircle, XCircle, Clock } from 'lucide-react';

interface ReturnStatusBadgeProps {
  status: 'pending' | 'approved' | 'disposed';
  size?: 'sm' | 'md' | 'lg';
  showIcon?: boolean;
}

const STATUS_CONFIG = {
  pending: {
    label: 'Pending',
    color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    icon: Clock,
    iconColor: 'text-yellow-600'
  },
  approved: {
    label: 'Approved',
    color: 'bg-green-100 text-green-800 border-green-200',
    icon: CheckCircle,
    iconColor: 'text-green-600'
  },
  disposed: {
    label: 'Disposed',
    color: 'bg-red-100 text-red-800 border-red-200',
    icon: XCircle,
    iconColor: 'text-red-600'
  }
};

const SIZE_CONFIG = {
  sm: {
    badge: 'px-2 py-1 text-xs',
    icon: 'w-3 h-3'
  },
  md: {
    badge: 'px-3 py-1 text-sm',
    icon: 'w-4 h-4'
  },
  lg: {
    badge: 'px-4 py-2 text-base',
    icon: 'w-5 h-5'
  }
};

export const ReturnStatusBadge: React.FC<ReturnStatusBadgeProps> = ({
  status,
  size = 'md',
  showIcon = true
}) => {
  const statusConfig = STATUS_CONFIG[status];
  const sizeConfig = SIZE_CONFIG[size];
  const Icon = statusConfig.icon;

  return (
    <span className={`
      inline-flex items-center font-semibold rounded-full border
      ${statusConfig.color} ${sizeConfig.badge}
    `}>
      {showIcon && (
        <Icon className={`${sizeConfig.icon} ${statusConfig.iconColor} mr-1`} />
      )}
      {statusConfig.label}
    </span>
  );
};