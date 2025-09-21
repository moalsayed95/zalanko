import { useState } from "react";
import { Listing } from "@/types";

/**
 * Custom hook for managing virtual try-on functionality
 * Handles try-on modal state, image generation, and results display
 */
export const useVirtualTryOn = () => {
    const [showTryOnModal, setShowTryOnModal] = useState(false);
    const [tryOnProduct, setTryOnProduct] = useState<Listing | null>(null);
    const [isGeneratingTryOn, setIsGeneratingTryOn] = useState(false);
    const [tryOnResult, setTryOnResult] = useState<{
        imageUrl: string;
        timestamp: Date;
    } | null>(null);

    /**
     * Open virtual try-on modal for a specific product
     */
    const handleTryOn = (listingId: string, listings: Listing[]) => {
        const product = listings.find(l => l.id === listingId);
        if (product) {
            setTryOnProduct(product);
            setShowTryOnModal(true);
            setTryOnResult(null);
            console.log("🎨 Opening try-on modal for:", product.title);
        }
    };

    /**
     * Handle virtual try-on generation request
     */
    const handleGenerateTryOn = async (productId: string, personImageBase64: string) => {
        console.log("🎨 GENERATING VIRTUAL TRY-ON:", productId);
        console.log("📸 Person image size:", personImageBase64.length, "characters");
        setIsGeneratingTryOn(true);

        try {
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

            // Try direct backend API call
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

                    if (result.tryon_image) {
                        // Convert base64 image to data URL for display
                        const fullImageUrl = `data:image/png;base64,${result.tryon_image}`;

                        console.log("🖼️ Generated virtual try-on image (base64)");

                        setTryOnResult({
                            imageUrl: fullImageUrl,
                            timestamp: new Date()
                        });
                    } else if (result.image_url) {
                        // Fallback for URL-based responses
                        const fullImageUrl = result.image_url.startsWith('http')
                            ? result.image_url
                            : `http://localhost:8765${result.image_url}`;

                        console.log("🖼️ Generated image URL:", fullImageUrl);

                        setTryOnResult({
                            imageUrl: fullImageUrl,
                            timestamp: new Date()
                        });
                    } else {
                        console.log("⚠️ No image data in response");
                    }
                } else {
                    console.log("❌ Backend API not available, status:", response.status);
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (fetchError) {
                console.log("⚠️ Direct API call failed, falling back to simulation:", fetchError);

                // Fallback: simulate the try-on
                console.log("💾 Simulated backend call with data");

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
        } finally {
            setIsGeneratingTryOn(false);
        }
    };

    /**
     * Handle virtual try-on result from voice/tool response
     */
    const handleTryOnResult = (result: any) => {
        console.log("🎉 VIRTUAL TRY-ON RESULT:", result);
        setIsGeneratingTryOn(false);
        if (result.image_url) {
            setTryOnResult({
                imageUrl: result.image_url,
                timestamp: new Date()
            });
        }
    };

    /**
     * Handle virtual try-on error
     */
    const handleTryOnError = (errorMessage: string) => {
        console.log("❌ VIRTUAL TRY-ON ERROR:", errorMessage);
        setIsGeneratingTryOn(false);
    };

    /**
     * Handle virtual try-on request from voice
     */
    const handleTryOnRequest = (productId: string, listings: Listing[]) => {
        console.log("👗 VIRTUAL TRY-ON REQUEST:", productId);
        const product = listings.find(l => l.id === productId);
        if (product) {
            setTryOnProduct(product);
            setShowTryOnModal(true);
            setTryOnResult(null);
        }
    };

    /**
     * Handle voice-activated try-on modal opening
     */
    const handleVoiceTryOnModal = (productId: string, listings: Listing[]) => {
        console.log("🎙️ VOICE TRY-ON: Opening modal for product", productId);
        const product = listings.find(l => l.id === productId);
        if (product) {
            setTryOnProduct(product);
            setShowTryOnModal(true);
            setTryOnResult(null);
            console.log("✅ Try-on modal opened for voice request");
        }
    };

    /**
     * Close the virtual try-on modal and reset state
     */
    const handleCloseTryOnModal = () => {
        setShowTryOnModal(false);
        setTryOnProduct(null);
        setTryOnResult(null);
        setIsGeneratingTryOn(false);
        console.log("❌ Try-on modal closed");
    };

    return {
        // State
        showTryOnModal,
        tryOnProduct,
        isGeneratingTryOn,
        tryOnResult,

        // Actions
        handleTryOn,
        handleGenerateTryOn,
        handleCloseTryOnModal,

        // Tool response handlers
        handleTryOnResult,
        handleTryOnError,
        handleTryOnRequest,
        handleVoiceTryOnModal
    };
};

export default useVirtualTryOn;