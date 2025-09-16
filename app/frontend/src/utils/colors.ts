/**
 * Color utilities for fashion product colors
 */

export const COLOR_MAP: { [key: string]: string } = {
  'white': '#FFFFFF',
  'black': '#000000',
  'navy': '#1B263B',
  'grey': '#6B7280',
  'gray': '#6B7280',
  'red': '#DC2626',
  'blue': '#2563EB',
  'green': '#059669',
  'yellow': '#D97706',
  'purple': '#7C3AED',
  'pink': '#DB2777',
  'brown': '#92400E',
  'beige': '#D2B48C',
  'orange': '#EA580C',
  'maroon': '#7F1D1D',
  'cream': '#FEF3C7',
  'olive': '#65A30D',
  'teal': '#0D9488',
  'coral': '#FB7185',
  'mustard': '#D97706',
  'emerald': '#059669',
  'charcoal': '#374151',
  'ivory': '#FFFBEB',
  'khaki': '#CA8A04',
  'salmon': '#FB7185',
  'turquoise': '#06B6D4',
  'burgundy': '#7F1D1D',
  'mint': '#6EE7B7',
  'lavender': '#C4B5FD',
  'rose': '#FB7185'
};

/**
 * Get hex color code for a color name
 * @param colorName - The color name (e.g., "white", "black", "navy")
 * @returns Hex color code with fallback to gray
 */
export const getColorHex = (colorName: string): string => {
  return COLOR_MAP[colorName.toLowerCase()] || '#6B7280';
};

/**
 * Get availability status styling classes
 * @param availability - The availability status
 * @returns Tailwind CSS classes for styling
 */
export const getAvailabilityColor = (availability: string): string => {
  const status = availability.toLowerCase();
  if (status === 'in stock') return 'text-green-400 bg-green-900/30';
  if (status === 'low stock') return 'text-orange-400 bg-orange-900/30';
  return 'text-red-400 bg-red-900/30';
};