import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import isEqual from "lodash.isequal";

import useRealTime from "@/hooks/useRealtime";
import useAudioRecorder from "@/hooks/useAudioRecorder";
import useAudioPlayer from "@/hooks/useAudioPlayer";
import { Listing } from "./types";

import ListingCard from "./components/ui/ListingCard";
import ProductImage from "./components/ui/ProductImage";
import VirtualTryOn from "./components/ui/VirtualTryOn";
import { Mic, Home, Heart, MessageCircle, ShoppingBag, Camera } from "lucide-react";
import Messages from "./components/ui/Messages";
import { getColorHex } from "./utils/colors";
import { calculatePricing } from "./utils/pricing";

function App() {
    const { t } = useTranslation();
    const [isRecording, setIsRecording] = useState(false);
    const [listings, setListings] = useState<Listing[]>([]);
    const [highlightedListingId, setHighlightedListingId] = useState<string | null>(null);

    // Favorites + Page + Cart
    const [favorites, setFavorites] = useState<string[]>([]);
    const [cartItems, setCartItems] = useState<string[]>([]);
    const [page, setPage] = useState<"main" | "favorites" | "messages" | "cart">("main");

    // Virtual Try-On
    const [showTryOnModal, setShowTryOnModal] = useState(false);
    const [tryOnProduct, setTryOnProduct] = useState<Listing | null>(null);
    const [isGeneratingTryOn, setIsGeneratingTryOn] = useState(false);
    const [tryOnResult, setTryOnResult] = useState<{
        imageUrl: string;
        timestamp: Date;
    } | null>(null);

    const [activeContact, setActiveContact] = useState<
        | {
              listingId: string;
              email: string;
              lastMessage?: string;
              timestamp?: Date;
              initialMessage?: string;
          }
        | undefined
    >();

    const listingsContainerRef = useRef<HTMLDivElement>(null);

    const { startSession, addUserAudio, inputAudioBufferClear } = useRealTime({
        onWebSocketOpen: () => console.log("WebSocket connection opened"),
        onWebSocketClose: () => console.log("WebSocket connection closed"),
        onWebSocketError: event => console.error("WebSocket error:", event),
        onReceivedError: message => console.error("error", message),
        onReceivedResponseAudioDelta: message => {
            isRecording && playAudio(message.delta);
        },
        onReceivedInputAudioBufferSpeechStarted: () => {
            stopAudioPlayer();
        },
        onReceivedExtensionMiddleTierToolResponse: message => {
            console.log("🛠️ TOOL RESPONSE:", message.tool_name, message);
            const result = JSON.parse(message.tool_result);
            console.log("📋 PARSED RESULT:", result);

            if (result.action === "update_preferences") {
                // Preferences handling removed since UserPreferences component is not being used
                console.log("Preferences updated:", result.preferences);
            } else if (result.products) {
                const newListings = result.products;
                if (!isEqual(listings, newListings)) {
                    setListings(newListings);
                    // Highlight first product by default
                    if (newListings.length > 0) {
                        setHighlightedListingId(newListings[0].id);
                    } else {
                        setHighlightedListingId(null);
                    }
                }
            } else if (result.action === "send_message") {
                setActiveContact({
                    listingId: result.listing_id,
                    email: result.contact,
                    timestamp: new Date(),
                    initialMessage: result.message
                });
                setPage("messages");
            } else if (typeof result.id === "string") {
                // Highlight the product
                console.log("🎯 HIGHLIGHTING PRODUCT:", result.id);
                setHighlightedListingId(result.id);
            } else if (typeof result.favorite_id === "string") {
                // Add or remove from favorites
                console.log("💖 FAVORITES ACTION: Toggling favorite for", result.favorite_id);
                setFavorites(prev => {
                    if (prev.includes(result.favorite_id)) {
                        console.log("➖ FAVORITES: Removing from favorites");
                        return prev.filter(item => item !== result.favorite_id);
                    }
                    console.log("➕ FAVORITES: Adding to favorites");
                    return [...prev, result.favorite_id];
                });
            } else if (result.action === "add_to_cart") {
                // Add to cart from AI tool
                console.log("🛒 CART ACTION: Adding to cart", result.product_id);
                handleAddToCart(result.product_id);
            } else if (typeof result.navigate_to === "string") {
                const destination = result.navigate_to as "main" | "favorites";
                setPage(destination);
            } else if (result.action === "virtual_try_on_request") {
                // Handle virtual try-on request
                console.log("👗 VIRTUAL TRY-ON REQUEST:", result);
                const product = listings.find(l => l.id === result.product_id);
                if (product) {
                    setTryOnProduct(product);
                    setShowTryOnModal(true);
                    setTryOnResult(null);
                }
            } else if (result.action === "virtual_try_on_result") {
                // Handle virtual try-on result
                console.log("🎉 VIRTUAL TRY-ON RESULT:", result);
                setIsGeneratingTryOn(false);
                if (result.image_url) {
                    setTryOnResult({
                        imageUrl: result.image_url,
                        timestamp: new Date()
                    });
                }
            } else if (result.action === "virtual_try_on_error") {
                // Handle virtual try-on error
                console.log("❌ VIRTUAL TRY-ON ERROR:", result.error);
                setIsGeneratingTryOn(false);
                // You could show an error toast here
            }
        }
    });

    const { reset: resetAudioPlayer, play: playAudio, stop: stopAudioPlayer } = useAudioPlayer();
    const { start: startAudioRecording, stop: stopAudioRecording } = useAudioRecorder({ onAudioRecorded: addUserAudio });

    const onToggleListening = async () => {
        if (!isRecording) {
            startSession();
            await startAudioRecording();
            resetAudioPlayer();
            setIsRecording(true);
        } else {
            await stopAudioRecording();
            stopAudioPlayer();
            inputAudioBufferClear();
            setIsRecording(false);
        }
    };

    // Which products to display
    const displayedListings = page === "favorites" ? listings.filter(l => favorites.includes(l.id)) : listings;

    // Cart functionality
    const handleAddToCart = (listingId: string) => {
        if (!cartItems.includes(listingId)) {
            setCartItems(prev => [...prev, listingId]);
        }
    };

    // Virtual Try-On functionality
    const handleTryOn = (listingId: string) => {
        const product = listings.find(l => l.id === listingId);
        if (product) {
            setTryOnProduct(product);
            setShowTryOnModal(true);
            setTryOnResult(null);
        }
    };

    const handleGenerateTryOn = async (productId: string, personImageBase64: string) => {
        console.log("🎨 GENERATING VIRTUAL TRY-ON:", productId);
        console.log("📸 Person image size:", personImageBase64.length, "characters");
        setIsGeneratingTryOn(true);

        try {
            // Make a direct API call to test the virtual try-on backend
            console.log("📡 Sending virtual try-on request to backend...");

            const requestBody = {
                product_id: productId,
                person_image_base64: personImageBase64,
                user_message: "Testing virtual try-on from UI"
            };

            console.log("🔍 Request details:", {
                product_id: productId,
                person_image_length: personImageBase64.length,
                timestamp: new Date().toISOString()
            });

            // Try to call the backend API directly first
            try {
                const backendUrl = 'http://localhost:8765/api/virtual-tryon';
                console.log("🌐 Calling backend URL:", backendUrl);

                const response = await fetch(backendUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestBody)
                });

                if (response.ok) {
                    const result = await response.json();
                    console.log("✅ Backend response:", result);

                    if (result.image_url) {
                        // Convert relative URL to full backend URL
                        const fullImageUrl = result.image_url.startsWith('http')
                            ? result.image_url
                            : `http://localhost:8765${result.image_url}`;

                        console.log("🖼️ Generated image URL:", fullImageUrl);

                        setTryOnResult({
                            imageUrl: fullImageUrl,
                            timestamp: new Date()
                        });
                    } else {
                        console.log("⚠️ No image URL in response");
                    }
                } else {
                    console.log("❌ Backend API not available, status:", response.status);
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (fetchError) {
                console.log("⚠️ Direct API call failed, falling back to simulation:", fetchError);

                // Fallback: simulate the try-on with detailed logging
                console.log("💾 Simulated backend call with data:", {
                    action: "virtual_try_on",
                    product_id: productId,
                    person_image_base64: personImageBase64.substring(0, 100) + "...",
                    timestamp: new Date().toISOString()
                });

                // Simulate processing time
                await new Promise(resolve => setTimeout(resolve, 3000));

                // Return a test result
                setTryOnResult({
                    imageUrl: "/api/placeholder/400/600",
                    timestamp: new Date()
                });

                console.log("✅ Virtual try-on simulation completed");
            }

        } catch (error) {
            console.error("❌ Virtual try-on failed:", error);
            // Handle error state
        } finally {
            setIsGeneratingTryOn(false);
        }
    };

    const handleCloseTryOnModal = () => {
        setShowTryOnModal(false);
        setTryOnProduct(null);
        setTryOnResult(null);
        setIsGeneratingTryOn(false);
    };

    useEffect(() => {
        if (highlightedListingId && listingsContainerRef.current) {
            console.log("🔄 SCROLL EFFECT: Scrolling to product", highlightedListingId);
            const container = listingsContainerRef.current;
            const highlightedCard = container.querySelector(`[data-listing-id="${highlightedListingId}"]`);

            if (highlightedCard) {
                console.log("✅ SCROLL: Found card element, scrolling into view");
                highlightedCard.scrollIntoView({
                    behavior: "smooth",
                    block: "nearest",
                    inline: "center"
                });
            } else {
                console.log("❌ SCROLL: Could not find card element for", highlightedListingId);
            }
        } else {
            console.log("⏭️ SCROLL: No highlighted listing or container not ready");
        }
    }, [highlightedListingId]);

    return (
        <div className="flex min-h-screen flex-col bg-gray-900 text-white transition-colors">
            {/* Fixed Header */}
            <header className="sticky top-0 z-50 border-b border-gray-800 bg-gray-900/95 backdrop-blur-sm py-4 shadow-sm">
                <div className="container mx-auto flex flex-wrap items-center justify-between px-4">
                    {/* Brand + Title */}
                    <div className="flex items-center gap-4">
                        <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-purple-600 via-pink-500 to-orange-400 rounded-2xl shadow-lg">
                            <span className="text-white font-bold text-xl">Z</span>
                        </div>
                        <h1 className="bg-gradient-to-r from-purple-600 via-pink-500 to-orange-400 bg-clip-text text-2xl font-black text-transparent sm:text-4xl tracking-tight">
                            Zalanko
                        </h1>
                        <span className="hidden sm:inline-block px-3 py-1 bg-gradient-to-r from-purple-900/30 to-pink-900/30 text-purple-300 text-sm font-semibold rounded-full border border-purple-700/50">
                            Fashion Forward
                        </span>
                    </div>
                    {/* Recording Section - Enhanced Design */}
                    <div className="flex items-center justify-end min-w-[400px]">
                        <div className="flex items-center mb-2">
                            {!isRecording ? (
                                <div className="flex items-center gap-3 px-6 py-3 bg-gray-700 rounded-full border border-gray-600 hover:border-purple-500 transition-all duration-300 hover:shadow-md">
                                    <div className="text-gray-300 font-medium text-sm">
                                        Start Conversation
                                    </div>
                                    <button
                                        onClick={onToggleListening}
                                        className="group relative flex items-center justify-center w-12 h-12 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 rounded-full shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300"
                                        aria-label={t("app.startRecording")}
                                    >
                                        <Mic className="w-5 h-5 text-white" />
                                        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-purple-600 to-pink-600 opacity-30 scale-110 animate-pulse"></div>
                                    </button>
                                </div>
                            ) : (
                                <div className="flex flex-col items-center gap-2 px-6 py-3 bg-gray-700 rounded-xl border border-purple-500 min-w-[350px]">
                                    {/* Top row with mic and close button */}
                                    <div className="flex items-center justify-between w-full">
                                        <div className="flex items-center gap-3">
                                            {/* Animated voice waves */}
                                            <div className="flex items-center gap-1">
                                                {[1,2,3,4,5].map(i => (
                                                    <div key={i} className={`w-1 bg-gradient-to-t from-purple-500 to-pink-500 rounded-full animate-pulse`} 
                                                         style={{
                                                            height: `${12 + (i % 3) * 8}px`,
                                                            animationDelay: `${i * 0.1}s`,
                                                            animationDuration: '0.8s'
                                                         }} 
                                                    />
                                                ))}
                                            </div>
                                            <div className="text-purple-400 font-medium text-sm animate-pulse">
                                                Listening...
                                            </div>
                                        </div>
                                        <button
                                            onClick={onToggleListening}
                                            className="group relative flex items-center justify-center w-10 h-10 bg-gradient-to-r from-red-500 to-pink-500 rounded-full shadow-xl transition-all duration-300 hover:scale-105"
                                            aria-label={t("app.stopRecording")}
                                        >
                                            <Mic className="w-5 h-5 text-white animate-pulse" />
                                            {/* Breathing rings */}
                                            {[1,2,3].map(ring => (
                                                <div key={ring} 
                                                     className="absolute inset-0 border-2 border-red-400/30 rounded-full animate-ping" 
                                                     style={{
                                                        animationDelay: `${ring * 0.4}s`,
                                                        animationDuration: '2s'
                                                     }} 
                                                />
                                            ))}
                                        </button>
                                    </div>
                                    {/* Voice query display */}
                                    <div className="w-full text-center">
                                        <div className="text-gray-300 text-sm italic">
                                            "Tell me about fashionable dresses..."
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
                {/* Navigation Tabs */}
                <div className="border-t border-gray-800 bg-gray-800/50 pb-4">
                    <div className="container mx-auto px-6">
                        <div className="flex gap-2 sm:gap-6 py-4">
                            <button
                                onClick={() => setPage("main")}
                                className={`group relative inline-flex items-center px-6 py-4 text-sm font-semibold transition-all duration-300 rounded-t-xl ${
                                    page === "main"
                                        ? "bg-gray-700 text-white shadow-sm"
                                        : "text-gray-400 hover:text-white hover:bg-gray-700/70"
                                }`}
                            >
                                <Home
                                    className={`mr-2 h-5 w-5 transition-colors ${
                                        page === "main"
                                            ? "text-white"
                                            : "text-gray-500 group-hover:text-white"
                                    }`}
                                />
                                Fashion Catalog
                                {page === "main" && (
                                    <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></div>
                                )}
                            </button>

                            <button
                                onClick={() => setPage("favorites")}
                                className={`group relative inline-flex items-center px-6 py-4 text-sm font-semibold transition-all duration-300 rounded-t-xl ${
                                    page === "favorites"
                                        ? "bg-gray-700 text-white shadow-sm"
                                        : "text-gray-400 hover:text-white hover:bg-gray-700/70"
                                }`}
                            >
                                <div className="relative">
                                    <Heart
                                        className={`mr-2 h-5 w-5 transition-colors ${
                                            page === "favorites"
                                                ? "text-white fill-current"
                                                : "text-gray-500 group-hover:text-white"
                                        }`}
                                    />
                                    {favorites.length > 0 && (
                                        <div className="absolute -top-2 -right-1 w-5 h-5 bg-gradient-to-r from-red-500 to-pink-500 rounded-full flex items-center justify-center animate-pulse">
                                            <span className="text-white text-xs font-bold">{favorites.length}</span>
                                        </div>
                                    )}
                                </div>
                                Your Favorites
                                {page === "favorites" && (
                                    <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-pink-500 to-rose-500 rounded-full"></div>
                                )}
                            </button>

                            <button
                                onClick={() => setPage("messages")}
                                className={`group relative inline-flex items-center px-6 py-4 text-sm font-semibold transition-all duration-300 rounded-t-xl ${
                                    page === "messages"
                                        ? "bg-gray-700 text-white shadow-sm"
                                        : "text-gray-400 hover:text-white hover:bg-gray-700/70"
                                }`}
                            >
                                <MessageCircle
                                    className={`mr-2 h-5 w-5 transition-colors ${
                                        page === "messages"
                                            ? "text-white"
                                            : "text-gray-500 group-hover:text-white"
                                    }`}
                                />
                                Messages
                                {page === "messages" && (
                                    <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-pink-500 to-rose-500 rounded-full"></div>
                                )}
                            </button>

                            <button
                                onClick={() => setPage("cart")}
                                className={`group relative inline-flex items-center px-6 py-4 text-sm font-semibold transition-all duration-300 rounded-t-xl ${
                                    page === "cart"
                                        ? "bg-gray-700 text-white shadow-sm"
                                        : "text-gray-400 hover:text-white hover:bg-gray-700/70"
                                }`}
                            >
                                <div className="relative">
                                    <ShoppingBag
                                        className={`mr-2 h-5 w-5 transition-colors ${
                                            page === "cart"
                                                ? "text-white"
                                                : "text-gray-500 group-hover:text-white"
                                        }`}
                                    />
                                    {cartItems.length > 0 && (
                                        <div className="absolute -top-2 -right-1 w-5 h-5 bg-gradient-to-r from-orange-500 to-red-500 rounded-full flex items-center justify-center">
                                            <span className="text-white text-xs font-bold">{cartItems.length}</span>
                                        </div>
                                    )}
                                </div>
                                Shopping Cart
                                {page === "cart" && (
                                    <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-gradient-to-r from-pink-500 to-rose-500 rounded-full"></div>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content - Updated Layout */}
            <main className="flex flex-grow flex-col">
                {page === "messages" ? (
                    <div className="container mx-auto h-[calc(100vh-200px)] p-4">
                        <Messages activeContact={activeContact} />
                    </div>
                ) : page === "cart" ? (
                    <div className="container mx-auto h-[calc(100vh-200px)] p-4">
                        <div className="bg-gray-800 rounded-lg shadow-sm p-8 h-full">
                            {cartItems.length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-full">
                                    <ShoppingBag className="w-16 h-16 text-purple-400 mb-4" />
                                    <h2 className="text-2xl font-bold text-white mb-2">Your Shopping Cart</h2>
                                    <p className="text-gray-400 text-center">
                                        Your cart is empty. Start shopping to add items!
                                    </p>
                                </div>
                            ) : (
                                <div>
                                    <div className="flex items-center justify-between mb-6">
                                        <h2 className="text-2xl font-bold text-white">Shopping Cart ({cartItems.length})</h2>
                                        <button 
                                            onClick={() => setCartItems([])}
                                            className="text-red-400 hover:text-red-300 text-sm font-medium"
                                        >
                                            Clear Cart
                                        </button>
                                    </div>
                                    <div className="space-y-4">
                                        {cartItems.map(itemId => {
                                            const listing = listings.find(l => l.id === itemId);
                                            if (!listing) return null;
                                            
                                            const { currentPrice } = calculatePricing(listing.price, listing.sale_price, listing.on_sale);
                                            
                                            return (
                                                <div key={itemId} className="flex items-center gap-4 p-4 border border-gray-700 rounded-lg bg-gray-700/30">
                                                    <div className="w-16 h-16 bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg flex items-center justify-center">
                                                        <span className="text-2xl">{listing.category === 'Dresses' ? '👗' : listing.category === 'Shoes' ? '👠' : '👕'}</span>
                                                    </div>
                                                    <div className="flex-1">
                                                        <h3 className="font-semibold text-white">{listing.title}</h3>
                                                        <p className="text-gray-400 text-sm">{listing.brand} • {listing.category}</p>
                                                        <p className="text-purple-400 font-bold">€{currentPrice}</p>
                                                    </div>
                                                    <button 
                                                        onClick={() => setCartItems(prev => prev.filter(id => id !== itemId))}
                                                        className="text-red-400 hover:text-red-300 px-3 py-1 text-sm"
                                                    >
                                                        Remove
                                                    </button>
                                                </div>
                                            );
                                        })}
                                    </div>
                                    <div className="mt-6 pt-6 border-t border-gray-700">
                                        <div className="flex justify-between items-center">
                                            <span className="text-lg font-semibold text-white">Total: €{
                                                cartItems.reduce((total, itemId) => {
                                                    const listing = listings.find(l => l.id === itemId);
                                                    if (!listing) return total;
                                                    const { currentPrice: price } = calculatePricing(listing.price, listing.sale_price, listing.on_sale);
                                                    return total + price;
                                                }, 0).toFixed(2)
                                            }</span>
                                            <button className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-6 py-2 rounded-lg font-semibold hover:from-purple-700 hover:to-pink-700 transition-all">
                                                Checkout
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    <>
                        {displayedListings.length > 0 ? (
                            <>
                                {/* Favorites Page - Vertical List Layout */}
                                {page === "favorites" ? (
                                    <div className="container mx-auto p-4">
                                        <div className="bg-gray-800 rounded-xl shadow-lg">
                                            {/* Favorites Header */}
                                            <div className="flex items-center justify-between p-6 border-b border-gray-700">
                                                <h1 className="text-2xl font-bold text-white">Your Favorites ({favorites.length})</h1>
                                                {favorites.length > 0 && (
                                                    <button
                                                        onClick={() => setFavorites([])}
                                                        className="text-red-400 hover:text-red-300 text-sm font-medium transition-colors"
                                                    >
                                                        Clear All
                                                    </button>
                                                )}
                                            </div>

                                            {/* Favorites List */}
                                            <div className="divide-y divide-gray-700">
                                                {displayedListings.map((listing) => {
                                                    const { currentPrice, hasDiscount, originalPrice } = calculatePricing(
                                                        listing.price,
                                                        listing.sale_price,
                                                        listing.on_sale
                                                    );

                                                    const getImageUrl = (): string => {
                                                        if (listing.imageUrls && listing.imageUrls.length > 0) {
                                                            return listing.imageUrls[0];
                                                        }
                                                        return '/api/placeholder/300/400';
                                                    };

                                                    return (
                                                        <div key={listing.id} className="flex gap-4 p-6 hover:bg-gray-700/30 transition-colors">
                                                            {/* Product Image */}
                                                            <div className="w-24 h-32 flex-shrink-0">
                                                                <ProductImage
                                                                    src={getImageUrl()}
                                                                    alt={listing.title}
                                                                    category={listing.category}
                                                                    className="w-full h-full object-cover rounded-lg"
                                                                />
                                                            </div>

                                                            {/* Product Details */}
                                                            <div className="flex-1 min-w-0">
                                                                <div className="mb-2">
                                                                    <h3 className="text-lg font-semibold text-white truncate">{listing.title}</h3>
                                                                    <p className="text-gray-400 text-sm">{listing.brand} • {listing.category}</p>
                                                                </div>

                                                                {/* Price */}
                                                                <div className="mb-2">
                                                                    <div className="flex items-center gap-2">
                                                                        <span className="text-xl font-bold text-purple-300">€{currentPrice}</span>
                                                                        {hasDiscount && originalPrice && (
                                                                            <span className="text-sm text-gray-500 line-through">€{originalPrice}</span>
                                                                        )}
                                                                        {hasDiscount && (
                                                                            <span className="bg-red-900/30 text-red-400 px-2 py-1 rounded-full text-xs">SALE</span>
                                                                        )}
                                                                    </div>
                                                                </div>

                                                                {/* Colors and Tags */}
                                                                <div className="mb-3">
                                                                    <div className="flex items-center gap-2 flex-wrap">
                                                                        {/* Colors */}
                                                                        <div className="flex gap-1">
                                                                            {listing.colors.slice(0, 3).map((color, index) => (
                                                                                <div
                                                                                    key={index}
                                                                                    className="w-4 h-4 rounded-full border border-gray-500"
                                                                                    style={{ backgroundColor: getColorHex(color) }}
                                                                                    title={color}
                                                                                />
                                                                            ))}
                                                                            {listing.colors.length > 3 && (
                                                                                <span className="text-xs text-gray-400 ml-1">+{listing.colors.length - 3}</span>
                                                                            )}
                                                                        </div>

                                                                        {/* Material Tag */}
                                                                        <span className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded-full">
                                                                            {listing.materials[0]}
                                                                        </span>
                                                                    </div>
                                                                </div>

                                                                {/* Ratings */}
                                                                {listing.ratings.average && (
                                                                    <div className="flex items-center text-sm mb-3">
                                                                        <div className="flex items-center">
                                                                            {[1,2,3,4,5].map((star) => (
                                                                                <span key={star} className={`text-sm ${star <= Math.floor(listing.ratings.average || 0) ? 'text-yellow-400' : 'text-gray-600'}`}>★</span>
                                                                            ))}
                                                                        </div>
                                                                        <span className="text-gray-300 ml-1">{listing.ratings.average}</span>
                                                                        <span className="text-gray-500 ml-1">({listing.ratings.count})</span>
                                                                    </div>
                                                                )}
                                                            </div>

                                                            {/* Actions */}
                                                            <div className="flex flex-col gap-2 items-end justify-center">
                                                                <button
                                                                    onClick={() => setFavorites(prev => prev.filter(id => id !== listing.id))}
                                                                    className="text-red-400 hover:text-red-300 p-2 rounded-lg hover:bg-red-900/20 transition-all"
                                                                    title="Remove from favorites"
                                                                >
                                                                    <Heart className="w-5 h-5 fill-current" />
                                                                </button>
                                                                <button
                                                                    onClick={() => handleTryOn(listing.id)}
                                                                    className="bg-gradient-to-r from-purple-500 to-pink-500 text-white px-3 py-2 rounded-lg text-sm font-medium hover:from-purple-600 hover:to-pink-600 transition-all transform hover:scale-105 mr-2"
                                                                >
                                                                    Try On
                                                                </button>
                                                                <button
                                                                    onClick={() => handleAddToCart(listing.id)}
                                                                    className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:from-purple-700 hover:to-pink-700 transition-all transform hover:scale-105"
                                                                >
                                                                    Add to Cart
                                                                </button>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        {/* Main Product Detail View - Centered in Container */}
                                        {highlightedListingId && (
                                    <div className="container mx-auto p-4 mb-8">
                                        {(() => {
                                            const highlightedProduct = displayedListings.find(l => l.id === highlightedListingId) || displayedListings[0];
                                            if (!highlightedProduct) return null;
                                            
                                            const getImageUrl = (): string => {
                                                if (highlightedProduct.imageUrls && highlightedProduct.imageUrls.length > 0) {
                                                    return highlightedProduct.imageUrls[0];
                                                }
                                                return '/api/placeholder/600/800';
                                            };
                                            
                                            const { currentPrice, hasDiscount, originalPrice } = calculatePricing(
                                                highlightedProduct.price, 
                                                highlightedProduct.sale_price, 
                                                highlightedProduct.on_sale
                                            );
                                            
                                            return (
                                                <div className="flex gap-8 bg-gray-800 rounded-xl p-6 shadow-lg">
                                                    {/* Large Product Image */}
                                                    <div className="w-1/2">
                                                        <div className="aspect-[3/4] rounded-lg overflow-hidden">
                                                            <ProductImage
                                                                src={getImageUrl()}
                                                                alt={highlightedProduct.title}
                                                                category={highlightedProduct.category}
                                                                className="w-full h-full object-cover rounded-lg"
                                                            />
                                                        </div>
                                                    </div>
                                                    
                                                    {/* Product Details Panel */}
                                                    <div className="w-1/2 flex flex-col">
                                                        <div className="mb-4">
                                                            <h1 className="text-3xl font-bold text-white mb-2">{highlightedProduct.title}</h1>
                                                            <p className="text-gray-400 text-lg">{highlightedProduct.brand}</p>
                                                        </div>
                                                        
                                                        {/* Price */}
                                                        <div className="mb-6">
                                                            <div className="flex items-center gap-3 mb-2">
                                                                <span className="text-4xl font-bold text-white">€{currentPrice}</span>
                                                                {hasDiscount && originalPrice && (
                                                                    <span className="text-xl text-gray-500 line-through">€{originalPrice}</span>
                                                                )}
                                                            </div>
                                                            {hasDiscount && (
                                                                <div className="inline-flex items-center bg-red-900/30 text-red-400 px-3 py-1 rounded-full text-sm">
                                                                    SALE
                                                                </div>
                                                            )}
                                                        </div>
                                                        
                                                        {/* Ratings */}
                                                        {highlightedProduct.ratings.average && (
                                                            <div className="flex items-center mb-6">
                                                                <div className="flex items-center">
                                                                    {[1,2,3,4,5].map((star) => (
                                                                        <span key={star} className={`text-xl ${star <= Math.floor(highlightedProduct.ratings.average || 0) ? 'text-yellow-400' : 'text-gray-600'}`}>★</span>
                                                                    ))}
                                                                </div>
                                                                <span className="text-gray-300 ml-2">{highlightedProduct.ratings.average}</span>
                                                                <span className="text-gray-500 ml-1">({highlightedProduct.ratings.count} reviews)</span>
                                                            </div>
                                                        )}
                                                        
                                                        {/* Colors */}
                                                        <div className="mb-6">
                                                            <h3 className="text-white font-medium mb-3">Colors</h3>
                                                            <div className="flex gap-2">
                                                                {highlightedProduct.colors.slice(0, 5).map((color, index) => (
                                                                    <div 
                                                                        key={index} 
                                                                        className="w-8 h-8 rounded-full border-2 border-gray-400 hover:border-white cursor-pointer transition-all hover:scale-110" 
                                                                        style={{ backgroundColor: getColorHex(color) }}
                                                                        title={color}
                                                                    />
                                                                ))}
                                                            </div>
                                                        </div>
                                                        
                                                        {/* Sizes */}
                                                        <div className="mb-6">
                                                            <h3 className="text-white font-medium mb-3">Sizes</h3>
                                                            <div className="flex gap-2">
                                                                {highlightedProduct.sizes.map((size, index) => (
                                                                    <div key={index} className="px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 hover:border-purple-500 cursor-pointer transition-colors">
                                                                        {size}
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                        
                                                        {/* Materials and Style Tags */}
                                                        <div className="mb-6">
                                                            <div className="flex flex-wrap gap-2">
                                                                {highlightedProduct.materials.map((material, index) => (
                                                                    <span key={index} className="px-3 py-1 bg-gray-700 text-gray-300 text-sm rounded-full">
                                                                        {material}
                                                                    </span>
                                                                ))}
                                                                {highlightedProduct.style_tags.slice(0, 3).map((tag, index) => (
                                                                    <span key={index} className="px-3 py-1 bg-purple-900/30 text-purple-300 text-sm rounded-full">
                                                                        {tag}
                                                                    </span>
                                                                ))}
                                                            </div>
                                                        </div>
                                                        
                                                        {/* Action Buttons */}
                                                        <div className="mt-auto space-y-3">
                                                            <button
                                                                onClick={() => handleTryOn(highlightedProduct.id)}
                                                                className="w-full bg-gradient-to-r from-purple-500 to-pink-500 text-white py-4 rounded-lg font-semibold text-lg hover:from-purple-600 hover:to-pink-600 transition-all transform hover:scale-105 flex items-center justify-center gap-3"
                                                            >
                                                                <Camera className="w-5 h-5" />
                                                                Try On Virtually
                                                            </button>
                                                            <button
                                                                onClick={() => handleAddToCart(highlightedProduct.id)}
                                                                className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white py-4 rounded-lg font-semibold text-lg hover:from-purple-700 hover:to-pink-700 transition-all transform hover:scale-105"
                                                            >
                                                                Add to Cart
                                                            </button>
                                                        </div>
                                                    </div>
                                                </div>
                                            );
                                        })()}
                                    </div>
                                )}
                                
                                        {/* Other Suggestions Section - Full Width */}
                                        <div className="w-full px-4">
                                            <div className="mb-6">
                                                <h2 className="text-2xl font-bold text-white text-center">Other Suggestions</h2>
                                            </div>
                                            <div
                                                ref={listingsContainerRef}
                                                className="flex gap-4 overflow-x-auto pb-4 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
                                            >
                                                {displayedListings.filter(l => l.id !== highlightedListingId).map(l => (
                                                    <div key={l.id} className="w-[300px] flex-none" data-listing-id={l.id}>
                                                        <ListingCard
                                                            listing={l}
                                                            highlight={false}
                                                            isFavorite={favorites.includes(l.id)}
                                                            onAddToCart={handleAddToCart}
                                                            onTryOn={handleTryOn}
                                                        />
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </>
                                )}
                            </>
                        ) : (
                            <div className="container mx-auto p-4">
                                <p className="text-center text-lg text-gray-400">{page === "favorites" ? t("products.noFavoritesYet") : t("products.noProductsFound")}</p>
                            </div>
                        )}
                    </>
                )}
            </main>

            {/* Virtual Try-On Modal */}
            <VirtualTryOn
                isOpen={showTryOnModal}
                onClose={handleCloseTryOnModal}
                product={tryOnProduct}
                onGenerateTryOn={handleGenerateTryOn}
                isGenerating={isGeneratingTryOn}
                tryOnResult={tryOnResult}
            />
        </div>
    );
}

export default App;