import { Listing } from "@/types";

interface ToolResponseHandlerConfig {
    // Product management
    setListings: (listings: Listing[]) => void;
    setHighlightedListingId: (id: string) => void;
    listings: Listing[];

    // Shopping features
    handleAddToCart: (id: string) => void;
    toggleFavorite: (id: string) => void;
    navigateTo: (page: "main" | "favorites" | "messages" | "cart") => void;

    // Virtual try-on
    handleTryOnRequest: (productId: string, listings: Listing[]) => void;
    handleVoiceTryOnModal: (productId: string, listings: Listing[]) => void;
    handleTryOnResult: (result: any) => void;
    handleTryOnError: (error: string) => void;

    // Messages
    setActiveContact: (contact: any) => void;
}

/**
 * Custom hook for handling tool responses from voice interface
 * Centralizes all tool response logic and delegates to appropriate handlers
 */
export const useToolResponseHandler = (config: ToolResponseHandlerConfig) => {
    const handleToolResponse = (message: any) => {
        console.log("🛠️ TOOL RESPONSE:", message.tool_name, message);
        const result = JSON.parse(message.tool_result);
        console.log("📋 PARSED RESULT:", result);

        // Product search results
        if (result.products) {
            config.setListings(result.products);
            return;
        }

        // Product highlighting
        if (typeof result.id === "string") {
            config.setHighlightedListingId(result.id);
            return;
        }

        // Action-based responses
        switch (result.action) {
            case "update_preferences":
                console.log("Preferences updated:", result.preferences);
                break;

            case "send_message":
                config.setActiveContact({
                    listingId: result.listing_id,
                    email: result.contact,
                    timestamp: new Date(),
                    initialMessage: result.message
                });
                config.navigateTo("messages");
                break;

            case "add_to_cart":
                console.log("🛒 CART ACTION: Adding to cart", result.product_id);
                config.handleAddToCart(result.product_id);
                break;

            case "virtual_try_on_request":
                config.handleTryOnRequest(result.product_id, config.listings);
                break;

            case "open_virtual_try_on_modal":
                config.handleVoiceTryOnModal(result.product_id, config.listings);
                break;

            case "virtual_try_on_result":
                config.handleTryOnResult(result);
                break;

            case "virtual_try_on_error":
                config.handleTryOnError(result.error);
                break;

            default:
                console.log("🤷‍♂️ Unknown tool response action:", result.action);
        }

        // Handle navigation
        if (typeof result.navigate_to === "string") {
            config.navigateTo(result.navigate_to as "main" | "favorites");
        }

        // Handle favorites
        if (typeof result.favorite_id === "string") {
            console.log("💖 FAVORITES ACTION: Toggling favorite for", result.favorite_id);
            config.toggleFavorite(result.favorite_id);
        }
    };

    return { handleToolResponse };
};

export default useToolResponseHandler;