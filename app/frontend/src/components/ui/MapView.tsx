import { Listing } from "@/types";
import { Shirt, Star, Percent } from "lucide-react";

type ProductGalleryProps = {
    listings: Listing[];
    highlightedListingId: string | null;
};

export default function ProductGallery({ listings, highlightedListingId }: ProductGalleryProps) {
    if (listings.length === 0) {
        return (
            <div className="flex h-[500px] items-center justify-center bg-gray-50 rounded-lg">
                <div className="text-center">
                    <Shirt className="mx-auto h-16 w-16 text-gray-400" />
                    <h3 className="mt-4 text-lg font-semibold text-gray-900">No products found</h3>
                    <p className="mt-2 text-gray-600">Try searching for clothing items using voice commands</p>
                </div>
            </div>
        );
    }

    const highlightedProduct = listings.find(l => l.id === highlightedListingId) || listings[0];

    return (
        <div className="h-[500px] bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-6">
            <div className="flex h-full">
                {/* Featured Product Display */}
                <div className="flex-1 flex flex-col justify-center items-center">
                    <div className="text-center max-w-md">
                        <div className="mb-4">
                            <div className="w-24 h-24 bg-white rounded-full flex items-center justify-center mx-auto shadow-lg">
                                <Shirt className="w-12 h-12 text-purple-600" />
                            </div>
                        </div>
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">
                            {highlightedProduct.title}
                        </h2>
                        <p className="text-lg text-purple-600 font-semibold mb-1">
                            {highlightedProduct.brand}
                        </p>
                        <div className="flex items-center justify-center gap-2 mb-4">
                            <span className="text-2xl font-bold text-gray-900">
                                €{highlightedProduct.sale_price || highlightedProduct.price}
                            </span>
                            {highlightedProduct.on_sale && highlightedProduct.sale_price && (
                                <span className="text-lg text-gray-500 line-through">
                                    €{highlightedProduct.price}
                                </span>
                            )}
                            {highlightedProduct.on_sale && (
                                <div className="flex items-center bg-red-100 text-red-800 px-2 py-1 rounded-full text-sm">
                                    <Percent className="w-3 h-3 mr-1" />
                                    SALE
                                </div>
                            )}
                        </div>
                        <div className="space-y-2 text-sm text-gray-600">
                            <p><strong>Category:</strong> {highlightedProduct.category}</p>
                            <p><strong>Colors:</strong> {highlightedProduct.colors.join(", ")}</p>
                            <p><strong>Sizes:</strong> {highlightedProduct.sizes.join(", ")}</p>
                            <p><strong>Materials:</strong> {highlightedProduct.materials.join(", ")}</p>
                        </div>
                        {highlightedProduct.ratings.average && (
                            <div className="flex items-center justify-center mt-3">
                                <Star className="w-4 h-4 text-yellow-500 fill-current" />
                                <span className="ml-1 text-sm text-gray-600">
                                    {highlightedProduct.ratings.average} ({highlightedProduct.ratings.count} reviews)
                                </span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Product Count */}
                <div className="w-32 flex flex-col items-center justify-center">
                    <div className="text-center bg-white rounded-lg p-4 shadow-sm">
                        <div className="text-3xl font-bold text-purple-600">{listings.length}</div>
                        <div className="text-sm text-gray-600">Products</div>
                        <div className="text-xs text-gray-500 mt-1">Found</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
