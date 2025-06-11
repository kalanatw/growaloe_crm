/**
 * Currency utility functions for formatting prices in LKR (Sri Lankan Rupees)
 */

/**
 * Format a number as LKR currency
 * @param amount - The amount to format
 * @param options - Formatting options
 * @returns Formatted currency string
 */
export const formatCurrency = (
  amount: number | string,
  options?: {
    showDecimals?: boolean;
    useLocaleString?: boolean;
  }
): string => {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  
  if (isNaN(numAmount)) {
    return 'LKR 0.00';
  }

  const { showDecimals = true, useLocaleString = true } = options || {};
  
  if (useLocaleString) {
    // Use locale-specific formatting with LKR currency
    if (showDecimals) {
      return `LKR ${numAmount.toLocaleString('en-LK', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })}`;
    } else {
      return `LKR ${numAmount.toLocaleString('en-LK', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      })}`;
    }
  } else {
    // Simple formatting without locale
    if (showDecimals) {
      return `LKR ${numAmount.toFixed(2)}`;
    } else {
      return `LKR ${Math.round(numAmount).toString()}`;
    }
  }
};

/**
 * Format currency for large amounts (with abbreviations like K, M)
 * @param amount - The amount to format
 * @returns Formatted currency string with abbreviations
 */
export const formatCurrencyCompact = (amount: number | string): string => {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  
  if (isNaN(numAmount)) {
    return 'LKR 0';
  }

  const absAmount = Math.abs(numAmount);
  const sign = numAmount < 0 ? '-' : '';
  
  if (absAmount >= 1_000_000_000) {
    return `${sign}LKR ${(absAmount / 1_000_000_000).toFixed(1)}B`;
  } else if (absAmount >= 1_000_000) {
    return `${sign}LKR ${(absAmount / 1_000_000).toFixed(1)}M`;
  } else if (absAmount >= 1_000) {
    return `${sign}LKR ${(absAmount / 1_000).toFixed(1)}K`;
  } else {
    return `${sign}LKR ${absAmount.toFixed(0)}`;
  }
};

/**
 * Format currency with sign for positive/negative amounts
 * @param amount - The amount to format
 * @param options - Formatting options
 * @returns Formatted currency string with appropriate sign
 */
export const formatCurrencyWithSign = (
  amount: number | string,
  options?: {
    showDecimals?: boolean;
    showPositiveSign?: boolean;
  }
): string => {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  
  if (isNaN(numAmount)) {
    return 'LKR 0.00';
  }

  const { showDecimals = true, showPositiveSign = false } = options || {};
  const sign = numAmount > 0 && showPositiveSign ? '+' : '';
  
  return `${sign}${formatCurrency(numAmount, { showDecimals })}`;
};

/**
 * Format balance with credit/debit indication
 * @param amount - The balance amount
 * @returns Formatted balance string
 */
export const formatBalance = (amount: number | string): string => {
  const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
  
  if (isNaN(numAmount)) {
    return 'LKR 0.00';
  }

  const absAmount = Math.abs(numAmount);
  const formattedAmount = formatCurrency(absAmount);
  
  if (numAmount < 0) {
    return `${formattedAmount} (Credit)`;
  }
  
  return formattedAmount;
};

// Legacy function names for backward compatibility
export const formatPrice = formatCurrency;
export const formatAmount = formatCurrency;
