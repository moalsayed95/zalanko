import { Listing } from "@/types";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "./card";
import ProductImage from "./ProductImage";
import { Shirt, Star, Tag, Package, Palette, Euro, Heart, Percent, ShoppingCart, Camera } from "lucide-react";
import { getColorHex, getAvailabilityColor } from "@/utils/colors";
import { calculatePricing } from "@/utils/pricing";

interface ProductCardProps {
    listing: Listing;
    highlight?: boolean;
    isFavorite?: boolean;
    onAddToCart?: (listingId: string) => void;
    onToggleFavorite?: (listingId: string) => void;
    onTryOn?: (listingId: string) => void;
}

export default function ListingCard({ listing, highlight = false, isFavorite = false, onAddToCart, onToggleFavorite, onTryOn }: ProductCardProps) {
    const { currentPrice, hasDiscount, originalPrice } = calculatePricing(
        listing.price, 
        listing.sale_price, 
        listing.on_sale
    );

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
            <div className="relative w-full h-48 overflow-hidden group">
                <ProductImage
                    src={getImageUrl()}
                    alt={listing.title}
                    category={listing.category}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                />
                {hasDiscount && (
                    <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded-full text-xs font-bold">
                        SALE
                    </div>
                )}
                <Heart
                    onClick={() => onToggleFavorite?.(listing.id)}
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
                        {hasDiscount && originalPrice && (
                            <span className="text-sm text-gray-500 line-through">€{originalPrice}</span>
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
                <div className="flex gap-2 w-full">
                    <button
                        onClick={() => onTryOn?.(listing.id)}
                        className="flex-1 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white py-2 rounded-lg font-semibold text-sm transition-all transform hover:scale-105 flex items-center justify-center gap-2"
                    >
                        <Camera className="w-4 h-4" />
                        Try On
                    </button>
                    <button
                        onClick={() => onAddToCart?.(listing.id)}
                        className="flex-1 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white py-2 rounded-lg font-semibold text-sm transition-all transform hover:scale-105 flex items-center justify-center gap-2"
                    >
                        <ShoppingCart className="w-4 h-4" />
                        Add to Cart
                    </button>
                </div>
            </CardFooter>
        </Card>
    );
}
