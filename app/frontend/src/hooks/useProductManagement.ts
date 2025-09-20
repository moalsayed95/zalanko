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
            id: "CLO_DEFAULT_001",
            title: "Essential Cotton T-Shirt",
            description: "Soft organic cotton t-shirt perfect for everyday wear",
            brand: "Zara",
            category: "T-Shirts & Tops",
            price: 19.99,
            on_sale: false,
            colors: ["white", "black", "navy"],
            sizes: ["XS", "S", "M", "L", "XL"],
            materials: ["100% Organic Cotton"],
            style_tags: ["casual", "basic", "everyday"],
            ratings: { average: 4.3, count: 892 },
            images: ["placeholder_tshirt.jpg"],
            availability: "in_stock",
            imageUrls: ["/api/placeholder/300/400"]
        },
        {
            id: "CLO_DEFAULT_002",
            title: "Classic Denim Jacket",
            description: "Timeless denim jacket with a modern fit - ON SALE!",
            brand: "H&M",
            category: "Outerwear",
            price: 79.99,
            sale_price: 59.99,
            on_sale: true,
            colors: ["blue", "black", "light-blue"],
            sizes: ["S", "M", "L", "XL"],
            materials: ["100% Cotton Denim"],
            style_tags: ["casual", "classic", "versatile"],
            ratings: { average: 4.5, count: 1204 },
            images: ["placeholder_jacket.jpg"],
            availability: "in_stock",
            imageUrls: ["/api/placeholder/300/400"]
        },
        {
            id: "CLO_DEFAULT_003",
            title: "Floral Summer Dress",
            description: "Light and breezy floral dress perfect for summer days",
            brand: "Mango",
            category: "Dresses",
            price: 45.99,
            on_sale: false,
            colors: ["floral-blue", "floral-pink", "floral-yellow"],
            sizes: ["XS", "S", "M", "L"],
            materials: ["100% Viscose"],
            style_tags: ["feminine", "summer", "floral"],
            ratings: { average: 4.7, count: 567 },
            images: ["placeholder_dress.jpg"],
            availability: "in_stock",
            imageUrls: ["/api/placeholder/300/400"]
        },
        {
            id: "CLO_DEFAULT_004",
            title: "Nike Air Max Sneakers",
            description: "Comfortable athletic sneakers for everyday wear",
            brand: "Nike",
            category: "Shoes",
            price: 120.00,
            sale_price: 89.99,
            on_sale: true,
            colors: ["white", "black", "red"],
            sizes: ["36", "37", "38", "39", "40", "41", "42"],
            materials: ["Synthetic", "Rubber"],
            style_tags: ["sporty", "casual", "athletic"],
            ratings: { average: 4.6, count: 2341 },
            images: ["placeholder_sneakers.jpg"],
            availability: "in_stock",
            imageUrls: ["/api/placeholder/300/400"]
        },
        {
            id: "CLO_DEFAULT_005",
            title: "Elegant Black Blazer",
            description: "Professional blazer perfect for office or special occasions",
            brand: "Massimo Dutti",
            category: "Blazers",
            price: 159.99,
            on_sale: false,
            colors: ["black", "navy", "grey"],
            sizes: ["XS", "S", "M", "L", "XL"],
            materials: ["Wool Blend", "Polyester"],
            style_tags: ["formal", "professional", "elegant"],
            ratings: { average: 4.4, count: 423 },
            images: ["placeholder_blazer.jpg"],
            availability: "in_stock",
            imageUrls: ["/api/placeholder/300/400"]
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