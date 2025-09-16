/**
 * Pricing utilities for products
 */

export interface PricingInfo {
  currentPrice: number;
  hasDiscount: boolean;
  originalPrice?: number;
}

/**
 * Calculate current price and discount information
 * @param price - Original price
 * @param salePrice - Sale price (if any)
 * @param onSale - Whether the item is on sale
 * @returns Pricing information object
 */
export const calculatePricing = (
  price: number, 
  salePrice: number | null | undefined, 
  onSale: boolean
): PricingInfo => {
  const hasDiscount = onSale && salePrice != null;
  const currentPrice = hasDiscount ? salePrice! : price;
  
  return {
    currentPrice,
    hasDiscount,
    originalPrice: hasDiscount ? price : undefined
  };
};