import { Listing } from "@/types";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "./card";
import { Shirt, Star, Tag, Package, Palette, Euro, Heart, Percent, ShoppingCart } from "lucide-react";

interface ProductCardProps {
    listing: Listing;
    highlight?: boolean;
    isFavorite?: boolean;
    onAddToCart?: (listingId: string) => void;
}

export default function ListingCard({ listing, highlight = false, isFavorite = false, onAddToCart }: ProductCardProps) {
    const getAvailabilityColor = (availability: string) => {
        if (availability.toLowerCase() === 'in stock') return 'text-green-400 bg-green-900/30';
        if (availability.toLowerCase() === 'low stock') return 'text-orange-400 bg-orange-900/30';
        return 'text-red-400 bg-red-900/30';
    };

    // Color mapping function for displaying actual colors
    const getColorHex = (colorName: string): string => {
        const colorMap: { [key: string]: string } = {
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
        
        return colorMap[colorName.toLowerCase()] || '#6B7280'; // fallback to gray
    };

    const currentPrice = listing.on_sale && listing.sale_price ? listing.sale_price : listing.price;
    const hasDiscount = listing.on_sale && listing.sale_price;

    // Get the first image URL, fallback to placeholder
    const getImageUrl = (): string => {
        if (listing.imageUrls && listing.imageUrls.length > 0) {
            return listing.imageUrls[0];
        }
        // Fallback placeholder for testing
        return '/api/placeholder/300/400';
    };

    return (
        <Card className={`w-full overflow-hidden border border-gray-700 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 bg-gray-800 rounded-xl ${highlight ? "ring-2 ring-purple-500 ring-opacity-50" : ""}`}>
            {/* Product Image Section */}
            <div className="relative w-full h-48 bg-gradient-to-br from-gray-700 to-gray-600 overflow-hidden group">
                <img
                    src={getImageUrl()}
                    alt={listing.title}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                    onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                    }}
                />
                {hasDiscount && (
                    <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded-full text-xs font-bold">
                        SALE
                    </div>
                )}
                <Heart 
                    className={`absolute top-2 left-2 h-5 w-5 cursor-pointer transition-all duration-200 hover:scale-110 ${
                        isFavorite 
                            ? "fill-current text-pink-400 hover:text-pink-300" 
                            : "text-gray-300 hover:text-pink-400"
                    }`} 
                />
            </div>

            <CardContent className="p-4">
                <div className="mb-3">
                    <h3 className="text-lg font-bold text-white mb-1 leading-tight">{listing.title}</h3>
                    <p className="text-gray-400 text-sm">{listing.brand}</p>
                </div>
                
                {/* Price */}
                <div className="mb-3">
                    <div className="flex items-center gap-2">
                        <span className="text-xl font-bold text-purple-300">€{currentPrice}</span>
                        {hasDiscount && (
                            <span className="text-sm text-gray-500 line-through">€{listing.price}</span>
                        )}
                    </div>
                </div>

                {/* Colors */}
                <div className="mb-3">
                    <div className="flex gap-1">
                        {listing.colors.slice(0, 4).map((color, index) => (
                            <div 
                                key={index} 
                                className="w-4 h-4 rounded-full border border-gray-400 hover:border-white cursor-pointer transition-all hover:scale-110" 
                                style={{ backgroundColor: getColorHex(color) }}
                                title={color}
                            />
                        ))}
                        {listing.colors.length > 4 && (
                            <span className="text-xs text-gray-400 ml-1">+{listing.colors.length - 4}</span>
                        )}
                    </div>
                </div>

                {/* Materials and Tags */}
                <div className="mb-3">
                    <div className="flex flex-wrap gap-1">
                        <span className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded-full">
                            {listing.materials[0]}
                        </span>
                        {listing.style_tags.slice(0, 2).map((tag, index) => (
                            <span key={index} className="px-2 py-1 bg-purple-900/30 text-purple-300 text-xs rounded-full">
                                {tag}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Ratings */}
                {listing.ratings.average && (
                    <div className="flex items-center mb-3 text-sm">
                        <Star className="h-3 w-3 text-yellow-400 fill-current mr-1" />
                        <span className="text-gray-300">{listing.ratings.average}</span>
                        <span className="text-gray-500 ml-1">({listing.ratings.count})</span>
                    </div>
                )}
            </CardContent>
            
            <CardFooter className="px-4 py-3 bg-gray-700/30 border-t border-gray-700">
                <button 
                    onClick={() => onAddToCart?.(listing.id)}
                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-2 rounded-lg font-semibold text-sm hover:from-purple-700 hover:to-pink-700 transition-all transform hover:scale-105"
                >
                    Add to Cart
                </button>
            </CardFooter>
        </Card>
    );
}
