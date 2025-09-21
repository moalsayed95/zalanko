import { useState, useEffect } from "react";
import isEqual from "lodash.isequal";
import { Listing } from "@/types";

/**
 * Custom hook for managing product data and operations
 * Handles default product loading, product listing state, and highlighting
 */
export const useProductManagement = () => {
    const [listings, setListings] = useState<Listing[]>([]);
    const [highlightedListingId, setHighlightedListingId] = useState<string | null>(null);
    const [hasLoadedDefaults, setHasLoadedDefaults] = useState(false);

    // Default products data - moved from App.tsx
    const getDefaultProducts = (): Listing[] => [
        {
            id: "CLO001",
            title: "Essential Cotton T-Shirt",
            description: "A soft and comfortable organic cotton t-shirt with a modern relaxed fit. Perfect for everyday wear with its breathable fabric and timeless design. Features a crew neck and short sleeves.",
            brand: "Zara",
            category: "T-Shirts & Tops",
            subcategory: "Basic Tees",
            gender: "unisex",
            price: 19.99,
            sale_price: null,
            on_sale: false,
            colors: ["white", "black", "navy", "grey"],
            sizes: ["XS", "S", "M", "L", "XL", "XXL"],
            materials: ["100% Organic Cotton"],
            style_tags: ["casual", "basic", "everyday", "minimalist"],
            season: "all-season",
            care_instructions: "Machine wash cold, tumble dry low",
            availability: "in_stock",
            stock_count: 250,
            ratings: { average: 4.3, count: 892 },
            images: ["CLO001.png"],
            sustainability_score: 8,
            fit: "regular",
            imageUrls: ["http://localhost:8765/api/images/CLO001/CLO001.png"]
        },
        {
            id: "CLO002",
            title: "Premium Wool Blend Coat",
            description: "Luxurious wool blend coat with elegant tailoring. Features a double-breasted design with notched lapels, side pockets, and a sophisticated silhouette that works for both business and evening occasions.",
            brand: "Hugo Boss",
            category: "Outerwear",
            subcategory: "Coats",
            gender: "women",
            price: 299.99,
            sale_price: 219.99,
            on_sale: true,
            colors: ["black", "camel", "navy"],
            sizes: ["34", "36", "38", "40", "42", "44"],
            materials: ["70% Wool", "25% Polyester", "5% Cashmere"],
            style_tags: ["elegant", "business", "formal", "winter"],
            season: "fall-winter",
            care_instructions: "Dry clean only",
            availability: "in_stock",
            stock_count: 45,
            ratings: { average: 4.7, count: 234 },
            images: ["CLO002.png"],
            sustainability_score: 6,
            fit: "tailored",
            imageUrls: ["http://localhost:8765/api/images/CLO002/CLO002.png"]
        },
        {
            id: "CLO003",
            title: "Skinny Fit Denim Jeans",
            description: "Classic skinny fit jeans in premium stretch denim. These jeans offer comfort and style with a flattering silhouette. Features five pockets, zip fly, and signature stitching details.",
            brand: "Levi's",
            category: "Jeans & Trousers",
            subcategory: "Skinny Jeans",
            gender: "women",
            price: 89.99,
            sale_price: null,
            on_sale: false,
            colors: ["dark_blue", "light_blue", "black", "white"],
            sizes: ["24", "25", "26", "27", "28", "29", "30", "31", "32"],
            materials: ["98% Cotton", "2% Elastane"],
            style_tags: ["denim", "skinny", "casual", "versatile"],
            season: "all-season",
            care_instructions: "Machine wash cold, hang dry",
            availability: "in_stock",
            stock_count: 180,
            ratings: { average: 4.2, count: 1567 },
            images: ["CLO003.png"],
            sustainability_score: 7,
            fit: "skinny",
            imageUrls: ["http://localhost:8765/api/images/CLO003/CLO003.png"]
        },
        {
            id: "CLO004",
            title: "Athletic Performance Hoodie",
            description: "Technical hoodie designed for active lifestyles. Features moisture-wicking fabric, adjustable hood, kangaroo pocket, and reflective details. Perfect for workouts or casual wear.",
            brand: "Nike",
            category: "Sportswear",
            subcategory: "Hoodies",
            gender: "men",
            price: 65.99,
            sale_price: 45.99,
            on_sale: true,
            colors: ["black", "grey", "navy", "red"],
            sizes: ["S", "M", "L", "XL", "XXL"],
            materials: ["65% Cotton", "35% Polyester"],
            style_tags: ["athletic", "casual", "performance", "streetwear"],
            season: "fall-spring",
            care_instructions: "Machine wash cold, tumble dry medium",
            availability: "in_stock",
            stock_count: 95,
            ratings: { average: 4.5, count: 423 },
            images: ["CLO004.png"],
            sustainability_score: 5,
            fit: "regular",
            imageUrls: ["http://localhost:8765/api/images/CLO004/CLO004.png"]
        },
        {
            id: "CLO005",
            title: "Silk Blend Midi Dress",
            description: "Elegant midi dress in luxurious silk blend fabric. Features a wrap design, 3/4 sleeves, and a flattering A-line silhouette. Perfect for special occasions or professional settings.",
            brand: "Massimo Dutti",
            category: "Dresses",
            subcategory: "Midi Dresses",
            gender: "women",
            price: 179.99,
            sale_price: null,
            on_sale: false,
            colors: ["burgundy", "navy", "emerald", "black"],
            sizes: ["XS", "S", "M", "L", "XL"],
            materials: ["60% Silk", "40% Viscose"],
            style_tags: ["elegant", "formal", "midi", "wrap"],
            season: "all-season",
            care_instructions: "Hand wash cold or dry clean",
            availability: "in_stock",
            stock_count: 78,
            ratings: { average: 4.6, count: 156 },
            images: ["CLO005.png"],
            sustainability_score: 7,
            fit: "regular",
            imageUrls: ["http://localhost:8765/api/images/CLO005/CLO005.png"]
        }
    ];

    /**
     * Load default products to show on page load
     * Creates better initial user experience
     */
    const loadDefaultProducts = async () => {
        if (hasLoadedDefaults || listings.length > 0) return;

        console.log("🏠 Loading default products for better UX...");
        setHasLoadedDefaults(true);

        const defaultQueries = [
            "trending fashion items",
            "popular dresses",
            "bestselling shoes",
            "stylish outerwear",
            "casual wear"
        ];

        const hour = new Date().getHours();
        const selectedQuery = defaultQueries[hour % defaultQueries.length];

        try {
            console.log(`🔍 Using default query: "${selectedQuery}"`);

            // Add realistic loading delay
            await new Promise(resolve => setTimeout(resolve, 1500));

            const mockProducts = getDefaultProducts();
            console.log("📦 Setting default products:", mockProducts.length);

            setListings(mockProducts);
            if (mockProducts.length > 0) {
                setHighlightedListingId(mockProducts[0].id);
            }

            console.log("✅ Default products loaded successfully!");
        } catch (error) {
            console.error("❌ Failed to load default products:", error);
        }
    };

    /**
     * Update product listings from search results
     */
    const updateListings = (newListings: Listing[]) => {
        if (!isEqual(listings, newListings)) {
            setListings(newListings);
            // Highlight first product by default
            if (newListings.length > 0) {
                setHighlightedListingId(newListings[0].id);
            } else {
                setHighlightedListingId(null);
            }
        }
    };

    /**
     * Highlight a specific product
     */
    const highlightProduct = (productId: string) => {
        console.log("🎯 HIGHLIGHTING PRODUCT:", productId);
        setHighlightedListingId(productId);
    };

    // Load default products on mount
    useEffect(() => {
        loadDefaultProducts();
    }, []);

    return {
        listings,
        highlightedListingId,
        setListings: updateListings,
        setHighlightedListingId: highlightProduct,
        loadDefaultProducts
    };
};

export default useProductManagement;