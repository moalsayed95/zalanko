import { useState } from "react";

/**
 * Custom hook for managing shopping cart and favorites functionality
 * Handles cart operations, favorites management, and page navigation
 */
export const useShoppingFeatures = () => {
    const [favorites, setFavorites] = useState<string[]>([]);
    const [cartItems, setCartItems] = useState<string[]>([]);
    const [page, setPage] = useState<"main" | "favorites" | "messages" | "cart">("main");

    /**
     * Add item to shopping cart if not already present
     */
    const handleAddToCart = (listingId: string) => {
        if (!cartItems.includes(listingId)) {
            setCartItems(prev => [...prev, listingId]);
            console.log("🛒 Added to cart:", listingId);
        }
    };

    /**
     * Remove item from shopping cart
     */
    const removeFromCart = (listingId: string) => {
        setCartItems(prev => prev.filter(id => id !== listingId));
        console.log("🛒 Removed from cart:", listingId);
    };

    /**
     * Clear all items from shopping cart
     */
    const clearCart = () => {
        setCartItems([]);
        console.log("🛒 Cart cleared");
    };

    /**
     * Toggle item in favorites list
     */
    const toggleFavorite = (listingId: string) => {
        setFavorites(prev => {
            if (prev.includes(listingId)) {
                console.log("💖 Removed from favorites:", listingId);
                return prev.filter(item => item !== listingId);
            } else {
                console.log("💖 Added to favorites:", listingId);
                return [...prev, listingId];
            }
        });
    };

    /**
     * Clear all favorites
     */
    const clearFavorites = () => {
        setFavorites([]);
        console.log("💖 Favorites cleared");
    };

    /**
     * Navigate to different pages
     */
    const navigateTo = (destination: "main" | "favorites" | "messages" | "cart") => {
        setPage(destination);
        console.log("📱 Navigated to:", destination);
    };

    return {
        // State
        favorites,
        cartItems,
        page,

        // Cart operations
        handleAddToCart,
        removeFromCart,
        clearCart,

        // Favorites operations
        toggleFavorite,
        clearFavorites,

        // Navigation
        navigateTo,
        setPage
    };
};

export default useShoppingFeatures;