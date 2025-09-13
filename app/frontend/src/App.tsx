import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import isEqual from "lodash.isequal";

import useRealTime from "@/hooks/useRealtime";
import useAudioRecorder from "@/hooks/useAudioRecorder";
import useAudioPlayer from "@/hooks/useAudioPlayer";
import { Listing, Preferences, AVAILABLE_FEATURES } from "./types";

import logo from "./assets/logo.svg";
import ListingCard from "./components/ui/ListingCard";
import ProductGallery from "./components/ui/MapView";
import { Mic, Home, Heart, MessageCircle, ShoppingBag } from "lucide-react";
import UserPreferences from "./components/ui/UserPreferences";
import Messages from "./components/ui/Messages";

function App() {
    const { t } = useTranslation();
    const [isRecording, setIsRecording] = useState(false);
    
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
    const [listings, setListings] = useState<Listing[]>([]);
    const [highlightedListingId, setHighlightedListingId] = useState<string | null>(null);

    // Favorites + Page + Cart
    const [favorites, setFavorites] = useState<string[]>([]);
    const [cartItems, setCartItems] = useState<string[]>([]);
    const [page, setPage] = useState<"main" | "favorites" | "messages" | "cart">("main");

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

    const [preferences, setPreferences] = useState<Preferences | undefined>();

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
            console.log("Received tool response", message);
            const result = JSON.parse(message.tool_result);

            if (result.action === "update_preferences") {
                setPreferences(prev => {
                    const newPreferences = {
                        ...prev,
                        features: prev?.features || [...AVAILABLE_FEATURES]
                    };

                    // Update basic preferences
                    if (result.preferences.budget) {
                        newPreferences.budget = result.preferences.budget;
                    }
                    if (result.preferences.sizes) {
                        newPreferences.sizes = result.preferences.sizes;
                    }
                    if (result.preferences.preferred_brands) {
                        newPreferences.preferred_brands = result.preferences.preferred_brands;
                    }
                    if (result.preferences.style_preferences) {
                        newPreferences.style_preferences = result.preferences.style_preferences;
                    }
                    if (result.preferences.preferred_colors) {
                        newPreferences.preferred_colors = result.preferences.preferred_colors;
                    }
                    if (result.preferences.avoided_materials) {
                        newPreferences.avoided_materials = result.preferences.avoided_materials;
                    }

                    // Update features
                    if (result.preferences.features) {
                        // Initialize features array if it doesn't exist
                        if (!newPreferences.features) {
                            newPreferences.features = [...AVAILABLE_FEATURES];
                        }

                        // Update each feature's enabled status
                        Object.entries(result.preferences.features).forEach(([id, enabled]) => {
                            const featureIndex = newPreferences.features.findIndex(f => f.id === id);
                            if (featureIndex !== -1) {
                                newPreferences.features[featureIndex] = {
                                    ...newPreferences.features[featureIndex],
                                    enabled: enabled as boolean
                                };
                            }
                        });
                    }

                    return newPreferences;
                });
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
                setHighlightedListingId(result.id);
            } else if (typeof result.favorite_id === "string") {
                // Add or remove from favorites
                setFavorites(prev => {
                    if (prev.includes(result.favorite_id)) {
                        return prev.filter(item => item !== result.favorite_id);
                    }
                    return [...prev, result.favorite_id];
                });
            } else if (typeof result.navigate_to === "string") {
                const destination = result.navigate_to as "main" | "favorites";
                setPage(destination);
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

    useEffect(() => {
        if (highlightedListingId && listingsContainerRef.current) {
            const container = listingsContainerRef.current;
            const highlightedCard = container.querySelector(`[data-listing-id="${highlightedListingId}"]`);

            if (highlightedCard) {
                highlightedCard.scrollIntoView({
                    behavior: "smooth",
                    block: "nearest",
                    inline: "center"
                });
            }
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
                                <Heart
                                    className={`mr-2 h-5 w-5 transition-colors ${
                                        page === "favorites"
                                            ? "text-white fill-current"
                                            : "text-gray-500 group-hover:text-white"
                                    }`}
                                />
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
                                            
                                            const currentPrice = listing.on_sale && listing.sale_price ? listing.sale_price : listing.price;
                                            
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
                                                    const price = listing.on_sale && listing.sale_price ? listing.sale_price : listing.price;
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
                                            
                                            const currentPrice = highlightedProduct.on_sale && highlightedProduct.sale_price ? highlightedProduct.sale_price : highlightedProduct.price;
                                            const hasDiscount = highlightedProduct.on_sale && highlightedProduct.sale_price;
                                            
                                            return (
                                                <div className="flex gap-8 bg-gray-800 rounded-xl p-6 shadow-lg">
                                                    {/* Large Product Image */}
                                                    <div className="w-1/2">
                                                        <div className="aspect-[3/4] bg-gradient-to-br from-gray-700 to-gray-600 rounded-lg overflow-hidden">
                                                            <img
                                                                src={getImageUrl()}
                                                                alt={highlightedProduct.title}
                                                                className="w-full h-full object-cover"
                                                                onError={(e) => {
                                                                    const target = e.target as HTMLImageElement;
                                                                    target.style.display = 'none';
                                                                }}
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
                                                                {hasDiscount && (
                                                                    <span className="text-xl text-gray-500 line-through">€{highlightedProduct.price}</span>
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
                                                        
                                                        {/* Add to Cart Button */}
                                                        <div className="mt-auto">
                                                            <button 
                                                                onClick={() => onAddToCart?.(highlightedProduct.id)}
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
                                                />
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="container mx-auto p-4">
                                <p className="text-center text-lg text-gray-400">{page === "favorites" ? t("No favorites yet.") : t("No products found.")}</p>
                            </div>
                        )}
                    </>
                )}
            </main>
        </div>
    );
}

export default App;
