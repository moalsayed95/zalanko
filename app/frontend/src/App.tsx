import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { Mic, Home, Heart, MessageCircle, ShoppingBag, Camera } from "lucide-react";

import useVoiceInterface from "@/hooks/useVoiceInterface";
import useProductManagement from "@/hooks/useProductManagement";
import useShoppingFeatures from "@/hooks/useShoppingFeatures";
import useVirtualTryOn from "@/hooks/useVirtualTryOn";
import useToolResponseHandler from "@/hooks/useToolResponseHandler";

import ListingCard from "./components/ui/ListingCard";
import ProductImage from "./components/ui/ProductImage";
import VirtualTryOn from "./components/ui/VirtualTryOn";
import Messages from "./components/ui/Messages";
import { getColorHex } from "./utils/colors";

function App() {
    const { t } = useTranslation();
    const listingsContainerRef = useRef<HTMLDivElement>(null);

    // Initialize all custom hooks
    const productManagement = useProductManagement();
    const shoppingFeatures = useShoppingFeatures();
    const virtualTryOn = useVirtualTryOn();

    // Messages state (could be extracted to another hook later)
    const [activeContact, setActiveContact] = useState<{
        listingId: string;
        email: string;
        lastMessage?: string;
        timestamp?: Date;
        initialMessage?: string;
    } | undefined>();

    // Setup tool response handler with all hook dependencies
    const toolResponseHandler = useToolResponseHandler({
        // Product management
        setListings: productManagement.setListings,
        setHighlightedListingId: productManagement.setHighlightedListingId,
        listings: productManagement.listings,

        // Shopping features
        handleAddToCart: shoppingFeatures.handleAddToCart,
        toggleFavorite: shoppingFeatures.toggleFavorite,
        navigateTo: shoppingFeatures.navigateTo,

        // Virtual try-on
        handleTryOnRequest: virtualTryOn.handleTryOnRequest,
        handleVoiceTryOnModal: virtualTryOn.handleVoiceTryOnModal,
        handleTryOnResult: virtualTryOn.handleTryOnResult,
        handleTryOnError: virtualTryOn.handleTryOnError,

        // Messages
        setActiveContact
    });

    // Initialize voice interface with tool response handler
    const { isRecording, onToggleListening } = useVoiceInterface({
        onToolResponse: toolResponseHandler.handleToolResponse
    });

    // Product display logic using shopping features
    const displayedListings = shoppingFeatures.page === "favorites"
        ? productManagement.listings.filter(l => shoppingFeatures.favorites.includes(l.id))
        : productManagement.listings;

    // Auto-scroll to highlighted product
    useEffect(() => {
        if (productManagement.highlightedListingId && listingsContainerRef.current) {
            const container = listingsContainerRef.current;
            const highlightedCard = container.querySelector(
                `[data-listing-id="${productManagement.highlightedListingId}"]`
            );
            if (highlightedCard) {
                highlightedCard.scrollIntoView({
                    behavior: "smooth",
                    block: "center"
                });
            }
        }
    }, [productManagement.highlightedListingId]);

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex flex-col">
            {/* Header */}
            <header className="sticky top-0 z-40 bg-gray-800/95 backdrop-blur-sm border-b border-gray-700">
                <div className="container mx-auto px-4 py-4">
                    <div className="flex items-center justify-between">
                        <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                            Zalanko
                        </h1>

                        {/* Voice Interface */}
                        <div className="flex items-center gap-4">
                            <button
                                onClick={onToggleListening}
                                className={`relative flex items-center justify-center w-12 h-12 rounded-full transition-all duration-300 shadow-lg ${
                                    isRecording
                                        ? "bg-gradient-to-r from-red-500 to-pink-500 animate-pulse shadow-red-500/50"
                                        : "bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 hover:scale-105 shadow-purple-500/50"
                                }`}
                                title={isRecording ? t("app.stopRecording") : t("app.startRecording")}
                            >
                                <Mic className="w-6 h-6 text-white" />
                                {isRecording && (
                                    <div className="absolute inset-0 rounded-full border-2 border-white/30 animate-ping"></div>
                                )}
                            </button>
                            <div className="text-sm text-gray-400 hidden sm:block">
                                {isRecording ? (
                                    <span className="text-red-400 font-medium">🎤 {t("voice.listening")}</span>
                                ) : (
                                    <span>{t("voice.startListening")}</span>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            {/* Navigation */}
            <nav className="bg-gray-800 border-b border-gray-700">
                <div className="container mx-auto px-4">
                    <div className="flex gap-2 sm:gap-6 py-4">
                        <button
                            onClick={() => shoppingFeatures.navigateTo("main")}
                            className={`group relative inline-flex items-center px-6 py-4 text-sm font-semibold transition-all duration-300 rounded-t-xl ${
                                shoppingFeatures.page === "main"
                                    ? "bg-gray-700 text-white shadow-sm"
                                    : "text-gray-400 hover:text-white hover:bg-gray-700/70"
                            }`}
                        >
                            <Home
                                className={`mr-2 h-5 w-5 transition-colors ${
                                    shoppingFeatures.page === "main"
                                        ? "text-white"
                                        : "text-gray-500 group-hover:text-white"
                                }`}
                            />
                            Fashion Catalog
                            {shoppingFeatures.page === "main" && (
                                <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></div>
                            )}
                        </button>

                        <button
                            onClick={() => shoppingFeatures.navigateTo("favorites")}
                            className={`group relative inline-flex items-center px-6 py-4 text-sm font-semibold transition-all duration-300 rounded-t-xl ${
                                shoppingFeatures.page === "favorites"
                                    ? "bg-gray-700 text-white shadow-sm"
                                    : "text-gray-400 hover:text-white hover:bg-gray-700/70"
                            }`}
                        >
                            <Heart
                                className={`mr-2 h-5 w-5 transition-colors ${
                                    shoppingFeatures.page === "favorites"
                                        ? "text-white"
                                        : "text-gray-500 group-hover:text-white"
                                }`}
                            />
                            Favorites ({shoppingFeatures.favorites.length})
                            {shoppingFeatures.page === "favorites" && (
                                <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></div>
                            )}
                        </button>

                        <button
                            onClick={() => shoppingFeatures.navigateTo("cart")}
                            className={`group relative inline-flex items-center px-6 py-4 text-sm font-semibold transition-all duration-300 rounded-t-xl ${
                                shoppingFeatures.page === "cart"
                                    ? "bg-gray-700 text-white shadow-sm"
                                    : "text-gray-400 hover:text-white hover:bg-gray-700/70"
                            }`}
                        >
                            <ShoppingBag
                                className={`mr-2 h-5 w-5 transition-colors ${
                                    shoppingFeatures.page === "cart"
                                        ? "text-white"
                                        : "text-gray-500 group-hover:text-white"
                                }`}
                            />
                            Cart ({shoppingFeatures.cartItems.length})
                            {shoppingFeatures.page === "cart" && (
                                <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></div>
                            )}
                        </button>

                        <button
                            onClick={() => shoppingFeatures.navigateTo("messages")}
                            className={`group relative inline-flex items-center px-6 py-4 text-sm font-semibold transition-all duration-300 rounded-t-xl ${
                                shoppingFeatures.page === "messages"
                                    ? "bg-gray-700 text-white shadow-sm"
                                    : "text-gray-400 hover:text-white hover:bg-gray-700/70"
                            }`}
                        >
                            <MessageCircle
                                className={`mr-2 h-5 w-5 transition-colors ${
                                    shoppingFeatures.page === "messages"
                                        ? "text-white"
                                        : "text-gray-500 group-hover:text-white"
                                }`}
                            />
                            Messages
                            {shoppingFeatures.page === "messages" && (
                                <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></div>
                            )}
                        </button>
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="flex-1 relative">
                {shoppingFeatures.page === "main" && (
                    <>
                        {displayedListings.length > 0 ? (
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 container mx-auto p-4">
                                {/* Product Grid */}
                                <div className="lg:col-span-2">
                                    <div
                                        ref={listingsContainerRef}
                                        className="grid grid-cols-1 sm:grid-cols-2 gap-4"
                                    >
                                        {displayedListings.map((listing) => (
                                            <ListingCard
                                                key={listing.id}
                                                listing={listing}
                                                data-listing-id={listing.id}
                                                isFavorite={shoppingFeatures.favorites.includes(listing.id)}
                                                onAddToCart={() => shoppingFeatures.handleAddToCart(listing.id)}
                                                onToggleFavorite={() => shoppingFeatures.toggleFavorite(listing.id)}
                                                onTryOn={() => virtualTryOn.handleTryOn(listing.id, productManagement.listings)}
                                            />
                                        ))}
                                    </div>
                                </div>

                                {/* Product Details */}
                                <div className="lg:col-span-1">
                                    {productManagement.highlightedListingId && (
                                        <div className="sticky top-24">
                                            {(() => {
                                                const highlightedListing = displayedListings.find(
                                                    (l) => l.id === productManagement.highlightedListingId
                                                );
                                                return highlightedListing ? (
                                                    <div className="bg-gray-800 rounded-xl p-6 shadow-xl border border-gray-700">
                                                        <div className="mb-6">
                                                            <ProductImage
                                                                src={highlightedListing.imageUrls?.[0] || ""}
                                                                alt={highlightedListing.title}
                                                                className="w-full h-64 object-cover rounded-lg"
                                                            />
                                                        </div>

                                                        <div className="space-y-4">
                                                            <div>
                                                                <h2 className="text-2xl font-bold text-white mb-2">
                                                                    {highlightedListing.title}
                                                                </h2>
                                                                <p className="text-gray-400 text-sm mb-2">
                                                                    {highlightedListing.brand} • {highlightedListing.category}
                                                                </p>
                                                                <div className="flex items-center gap-2">
                                                                    {highlightedListing.on_sale && highlightedListing.sale_price ? (
                                                                        <>
                                                                            <span className="text-2xl font-bold text-green-400">
                                                                                €{highlightedListing.sale_price}
                                                                            </span>
                                                                            <span className="text-lg text-gray-500 line-through">
                                                                                €{highlightedListing.price}
                                                                            </span>
                                                                            <span className="bg-red-500 text-white text-xs px-2 py-1 rounded">
                                                                                SALE
                                                                            </span>
                                                                        </>
                                                                    ) : (
                                                                        <span className="text-2xl font-bold text-white">
                                                                            €{highlightedListing.price}
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            </div>

                                                            <p className="text-gray-300 text-sm">
                                                                {highlightedListing.description}
                                                            </p>

                                                            {/* Colors */}
                                                            <div>
                                                                <h4 className="text-sm font-semibold text-gray-300 mb-2">Colors</h4>
                                                                <div className="flex gap-2">
                                                                    {highlightedListing.colors.map((color, index) => (
                                                                        <div
                                                                            key={index}
                                                                            className="w-6 h-6 rounded-full border border-gray-500"
                                                                            style={{ backgroundColor: getColorHex(color) }}
                                                                            title={color}
                                                                        />
                                                                    ))}
                                                                </div>
                                                            </div>

                                                            {/* Sizes */}
                                                            <div>
                                                                <h4 className="text-sm font-semibold text-gray-300 mb-2">Sizes</h4>
                                                                <div className="flex gap-2">
                                                                    {highlightedListing.sizes.map((size, index) => (
                                                                        <span
                                                                            key={index}
                                                                            className="px-3 py-1 bg-gray-700 text-white text-sm rounded border border-gray-600"
                                                                        >
                                                                            {size}
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                            </div>

                                                            {/* Materials */}
                                                            <div>
                                                                <h4 className="text-sm font-semibold text-gray-300 mb-2">Materials</h4>
                                                                <div className="flex flex-wrap gap-2">
                                                                    {highlightedListing.materials.map((material, index) => (
                                                                        <span
                                                                            key={index}
                                                                            className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded"
                                                                        >
                                                                            {material}
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                            </div>

                                                            {/* Action Buttons */}
                                                            <div className="space-y-3 pt-4">
                                                                <button
                                                                    onClick={() => virtualTryOn.handleTryOn(highlightedListing.id, productManagement.listings)}
                                                                    className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 transition-all transform hover:scale-105 flex items-center justify-center gap-2"
                                                                >
                                                                    <Camera className="w-4 h-4" />
                                                                    Virtual Try-On
                                                                </button>

                                                                <button
                                                                    onClick={() => shoppingFeatures.handleAddToCart(highlightedListing.id)}
                                                                    className="w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-all transform hover:scale-105 flex items-center justify-center gap-2"
                                                                >
                                                                    <ShoppingBag className="w-4 h-4" />
                                                                    Add to Cart
                                                                </button>

                                                                <button
                                                                    onClick={() => shoppingFeatures.toggleFavorite(highlightedListing.id)}
                                                                    className={`w-full py-3 rounded-lg font-semibold transition-all transform hover:scale-105 flex items-center justify-center gap-2 ${
                                                                        shoppingFeatures.favorites.includes(highlightedListing.id)
                                                                            ? "bg-red-600 text-white hover:bg-red-700"
                                                                            : "bg-gray-700 text-white hover:bg-gray-600"
                                                                    }`}
                                                                >
                                                                    <Heart className={`w-4 h-4 ${shoppingFeatures.favorites.includes(highlightedListing.id) ? "fill-current" : ""}`} />
                                                                    {shoppingFeatures.favorites.includes(highlightedListing.id) ? "Remove from Favorites" : "Add to Favorites"}
                                                                </button>
                                                            </div>
                                                        </div>
                                                    </div>
                                                ) : null;
                                            })()}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ) : (
                            <div className="container mx-auto p-4">
                                <div className="text-center py-12">
                                    <div className="mb-8">
                                        <div className="flex items-center justify-center mb-4">
                                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
                                        </div>
                                        <h2 className="text-2xl font-bold text-white mb-2">Curating Your Fashion Feed</h2>
                                        <p className="text-gray-400 mb-6">We're selecting the best trending items for you...</p>
                                    </div>

                                    <div className="bg-gray-800 rounded-xl p-6 max-w-md mx-auto">
                                        <h3 className="text-lg font-semibold text-white mb-4">Try Voice Search</h3>
                                        <div className="space-y-2 text-sm text-gray-300">
                                            <p>💬 "Show me black leather jackets"</p>
                                            <p>💬 "Find summer dresses under €100"</p>
                                            <p>💬 "I need casual sneakers"</p>
                                        </div>
                                        <button
                                            onClick={onToggleListening}
                                            className="mt-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition-all flex items-center gap-2 mx-auto"
                                        >
                                            <Mic className="w-4 h-4" />
                                            {t("voice.startListening")}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        )}
                    </>
                )}

                {shoppingFeatures.page === "favorites" && (
                    <div className="container mx-auto p-4">
                        {shoppingFeatures.favorites.length > 0 ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {displayedListings.map((listing) => (
                                    <ListingCard
                                        key={listing.id}
                                        listing={listing}
                                        isFavorite={true}
                                        onAddToCart={() => shoppingFeatures.handleAddToCart(listing.id)}
                                        onToggleFavorite={() => shoppingFeatures.toggleFavorite(listing.id)}
                                        onTryOn={() => virtualTryOn.handleTryOn(listing.id, productManagement.listings)}
                                    />
                                ))}
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <Heart className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                                <h2 className="text-2xl font-bold text-white mb-2">No Favorites Yet</h2>
                                <p className="text-gray-400 mb-6">Start exploring and save items you love!</p>
                                <button
                                    onClick={() => shoppingFeatures.navigateTo("main")}
                                    className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition-all"
                                >
                                    Discover Fashion
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {shoppingFeatures.page === "cart" && (
                    <div className="container mx-auto p-4">
                        {shoppingFeatures.cartItems.length > 0 ? (
                            <div className="space-y-6">
                                {/* Cart Items */}
                                <div className="grid gap-4">
                                    {shoppingFeatures.cartItems.map((itemId) => {
                                        const listing = productManagement.listings.find((l) => l.id === itemId);
                                        return listing ? (
                                            <div key={itemId} className="bg-gray-800 rounded-lg p-4 flex items-center gap-4">
                                                <ProductImage
                                                    src={listing.imageUrls?.[0] || ""}
                                                    alt={listing.title}
                                                    className="w-20 h-20 object-cover rounded"
                                                />
                                                <div className="flex-1">
                                                    <h3 className="font-semibold text-white">{listing.title}</h3>
                                                    <p className="text-gray-400 text-sm">{listing.brand}</p>
                                                    <p className="text-white font-bold">€{listing.sale_price || listing.price}</p>
                                                </div>
                                                <button
                                                    onClick={() => shoppingFeatures.removeFromCart(itemId)}
                                                    className="text-red-400 hover:text-red-300 transition-colors"
                                                >
                                                    Remove
                                                </button>
                                            </div>
                                        ) : null;
                                    })}
                                </div>

                                {/* Cart Summary */}
                                <div className="bg-gray-800 rounded-lg p-6">
                                    <h3 className="text-xl font-bold text-white mb-4">Order Summary</h3>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-white">
                                            <span>Total Items:</span>
                                            <span>{shoppingFeatures.cartItems.length}</span>
                                        </div>
                                        <div className="flex justify-between text-xl font-bold text-white">
                                            <span>Total:</span>
                                            <span>
                                                €{shoppingFeatures.cartItems.reduce((total, itemId) => {
                                                    const listing = productManagement.listings.find((l) => l.id === itemId);
                                                    return total + (listing ? (listing.sale_price || listing.price) : 0);
                                                }, 0).toFixed(2)}
                                            </span>
                                        </div>
                                    </div>
                                    <button className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-3 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 transition-all mt-4">
                                        Proceed to Checkout
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <ShoppingBag className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                                <h2 className="text-2xl font-bold text-white mb-2">Your Cart is Empty</h2>
                                <p className="text-gray-400 mb-6">Add some items to get started!</p>
                                <button
                                    onClick={() => shoppingFeatures.navigateTo("main")}
                                    className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-3 rounded-lg font-medium hover:from-purple-700 hover:to-pink-700 transition-all"
                                >
                                    Start Shopping
                                </button>
                            </div>
                        )}
                    </div>
                )}

                {shoppingFeatures.page === "messages" && (
                    <div className="container mx-auto p-4">
                        <Messages activeContact={activeContact} />
                    </div>
                )}
            </main>

            {/* Virtual Try-On Modal */}
            <VirtualTryOn
                isOpen={virtualTryOn.showTryOnModal}
                onClose={virtualTryOn.handleCloseTryOnModal}
                product={virtualTryOn.tryOnProduct}
                onGenerateTryOn={virtualTryOn.handleGenerateTryOn}
                isGenerating={virtualTryOn.isGeneratingTryOn}
                tryOnResult={virtualTryOn.tryOnResult}
            />
        </div>
    );
}

export default App;