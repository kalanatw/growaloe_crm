/**
 * Date utility functions for formatting dates consistently across the application
 */

/**
 * Format a date string or Date object to a readable format
 * @param date - The date to format (string or Date object)
 * @param options - Formatting options
 * @returns Formatted date string
 */
export const formatDate = (
  date: string | Date,
  options?: {
    includeTime?: boolean;
    dateStyle?: 'short' | 'medium' | 'long' | 'full';
    timeStyle?: 'short' | 'medium' | 'long' | 'full';
  }
): string => {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) {
    return 'Invalid Date';
  }
  
  const { includeTime = false, dateStyle = 'medium', timeStyle = 'short' } = options || {};
  
  if (includeTime) {
    return dateObj.toLocaleString('en-US', {
      dateStyle,
      timeStyle,
    });
  } else {
    return dateObj.toLocaleDateString('en-US', {
      dateStyle,
    });
  }
};

/**
 * Format a date to a short format (MM/dd/yyyy)
 * @param date - The date to format
 * @returns Short formatted date string
 */
export const formatDateShort = (date: string | Date): string => {
  return formatDate(date, { dateStyle: 'short' });
};

/**
 * Format a date to include time (MM/dd/yyyy, HH:mm AM/PM)
 * @param date - The date to format
 * @returns Formatted date string with time
 */
export const formatDateTime = (date: string | Date): string => {
  return formatDate(date, { includeTime: true });
};

/**
 * Format a date for display in tables (MMM dd, yyyy)
 * @param date - The date to format
 * @returns Table-friendly date format
 */
export const formatDateForTable = (date: string | Date): string => {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) {
    return 'Invalid Date';
  }
  
  return dateObj.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
};

/**
 * Get relative time string (e.g., "2 days ago", "in 3 hours")
 * @param date - The date to compare
 * @returns Relative time string
 */
export const getRelativeTime = (date: string | Date): string => {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) {
    return 'Invalid Date';
  }
  
  const now = new Date();
  const diffInMs = now.getTime() - dateObj.getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMinutes / 60);
  const diffInDays = Math.floor(diffInHours / 24);
  
  if (diffInDays > 0) {
    return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
  } else if (diffInHours > 0) {
    return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
  } else if (diffInMinutes > 0) {
    return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
  } else {
    return 'Just now';
  }
};

/**
 * Check if a date is today
 * @param date - The date to check
 * @returns True if the date is today
 */
export const isToday = (date: string | Date): boolean => {
  if (!date) return false;
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const today = new Date();
  
  return (
    dateObj.getDate() === today.getDate() &&
    dateObj.getMonth() === today.getMonth() &&
    dateObj.getFullYear() === today.getFullYear()
  );
};

/**
 * Check if a date is expired (past today)
 * @param date - The date to check
 * @returns True if the date is expired
 */
export const isExpired = (date: string | Date): boolean => {
  if (!date) return false;
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const today = new Date();
  
  // Set time to start of day for accurate comparison
  today.setHours(0, 0, 0, 0);
  dateObj.setHours(0, 0, 0, 0);
  
  return dateObj < today;
};

/**
 * Calculate days until expiry
 * @param date - The expiry date
 * @returns Number of days until expiry (negative if expired)
 */
export const daysUntilExpiry = (date: string | Date): number => {
  if (!date) return 0;
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  const today = new Date();
  
  // Set time to start of day for accurate comparison
  today.setHours(0, 0, 0, 0);
  dateObj.setHours(0, 0, 0, 0);
  
  const diffInMs = dateObj.getTime() - today.getTime();
  return Math.ceil(diffInMs / (1000 * 60 * 60 * 24));
};

/**
 * Format a date for input fields (yyyy-MM-dd)
 * @param date - The date to format
 * @returns Date string in input format
 */
export const formatDateForInput = (date: string | Date): string => {
  if (!date) return '';
  
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  
  if (isNaN(dateObj.getTime())) {
    return '';
  }
  
  return dateObj.toISOString().split('T')[0];
};
