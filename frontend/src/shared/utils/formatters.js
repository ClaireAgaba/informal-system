import { format, parseISO } from 'date-fns';

/**
 * Format date string to readable format
 * @param {string} dateString - ISO date string
 * @param {string} formatStr - Date format string (default: 'MMM dd, yyyy')
 * @returns {string} Formatted date
 */
export const formatDate = (dateString, formatStr = 'MMM dd, yyyy') => {
  if (!dateString) return '-';
  try {
    return format(parseISO(dateString), formatStr);
  } catch (error) {
    return dateString;
  }
};

/**
 * Format date and time string
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date and time
 */
export const formatDateTime = (dateString) => {
  return formatDate(dateString, 'MMM dd, yyyy HH:mm');
};

/**
 * Format currency
 * @param {number} amount - Amount to format
 * @param {string} currency - Currency code (default: 'UGX')
 * @returns {string} Formatted currency
 */
export const formatCurrency = (amount, currency = 'UGX') => {
  if (amount === null || amount === undefined) return '-';
  return new Intl.NumberFormat('en-UG', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
  }).format(amount);
};

/**
 * Format phone number
 * @param {string} phone - Phone number
 * @returns {string} Formatted phone number
 */
export const formatPhone = (phone) => {
  if (!phone) return '-';
  // Remove all non-numeric characters
  const cleaned = phone.replace(/\D/g, '');
  // Format as: 0XXX XXX XXX
  if (cleaned.length === 10) {
    return `${cleaned.slice(0, 4)} ${cleaned.slice(4, 7)} ${cleaned.slice(7)}`;
  }
  return phone;
};

/**
 * Truncate text
 * @param {string} text - Text to truncate
 * @param {number} length - Maximum length
 * @returns {string} Truncated text
 */
export const truncate = (text, length = 50) => {
  if (!text) return '';
  if (text.length <= length) return text;
  return `${text.slice(0, length)}...`;
};

/**
 * Get initials from name
 * @param {string} name - Full name
 * @returns {string} Initials
 */
export const getInitials = (name) => {
  if (!name) return '';
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
};
