import { formatCurrency } from './currency';

/**
 * Utility function to get responsive font size based on amount length
 * @param amount - The numeric amount or string to analyze
 * @returns Tailwind CSS classes for responsive font sizing
 */
export const getResponsiveFontSize = (amount: number | string): string => {
  const amountStr = typeof amount === 'number' ? formatCurrency(amount) : amount;
  const length = amountStr.length;
  
  // More granular breakpoints for better responsiveness
  if (length <= 6) return 'text-2xl sm:text-3xl'; // Very small amounts like $100
  if (length <= 8) return 'text-xl sm:text-2xl';  // Small amounts like $1,000
  if (length <= 10) return 'text-lg sm:text-xl';  // Medium amounts like $10,000
  if (length <= 12) return 'text-base sm:text-lg'; // Large amounts like $100,000
  if (length <= 16) return 'text-sm sm:text-base'; // Very large amounts like $1,000,000
  return 'text-xs sm:text-sm'; // Extremely large amounts
};

/**
 * Utility function to get responsive font size for card content
 * @param amount - The numeric amount or string to style
 * @returns Complete CSS classes for card amount display
 */
export const getCardAmountClass = (amount: number | string): string => {
  const baseClasses = 'font-semibold break-words leading-tight';
  const sizeClass = getResponsiveFontSize(amount);
  return `${baseClasses} ${sizeClass}`;
};

/**
 * Utility function to get responsive font size for table amounts
 * @param amount - The numeric amount or string to style
 * @returns Complete CSS classes for table amount display
 */
export const getTableAmountClass = (amount: number | string): string => {
  const baseClasses = 'font-semibold';
  const sizeClass = getResponsiveFontSize(amount);
  return `${baseClasses} ${sizeClass}`;
};

/**
 * Get responsive classes for status badges based on amount size
 * @param amount - The amount to base sizing on
 * @returns Font size classes for status badges
 */
export const getStatusBadgeSize = (amount: number | string): string => {
  const amountStr = typeof amount === 'number' ? formatCurrency(amount) : amount;
  const length = amountStr.length;
  
  if (length <= 8) return 'text-xs';
  if (length <= 12) return 'text-xs';
  return 'text-2xs'; // Very small for large amounts
};
