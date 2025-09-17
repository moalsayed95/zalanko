import { useState, useCallback, useRef } from "react";
import { Upload, X, Camera, Loader2, Download, Share2, RefreshCw } from "lucide-react";
import { Listing } from "@/types";

interface VirtualTryOnProps {
    isOpen: boolean;
    onClose: () => void;
    product: Listing | null;
    onGenerateTryOn: (productId: string, personImageBase64: string) => void;
    isGenerating?: boolean;
    tryOnResult?: {
        imageUrl: string;
        timestamp: Date;
    } | null;
}

export default function VirtualTryOn({
    isOpen,
    onClose,
    product,
    onGenerateTryOn,
    isGenerating = false,
    tryOnResult = null
}: VirtualTryOnProps) {
    const [userPhoto, setUserPhoto] = useState<string | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileUpload = useCallback((file: File) => {
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                const base64 = e.target?.result as string;
                setUserPhoto(base64);
            };
            reader.readAsDataURL(file);
        }
    }, []);

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    }, [handleFileUpload]);

    const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            handleFileUpload(e.target.files[0]);
        }
    }, [handleFileUpload]);

    const handleGenerateTryOn = () => {
        if (product && userPhoto) {
            // Extract base64 data from data URL
            const base64Data = userPhoto.split(',')[1];
            onGenerateTryOn(product.id, base64Data);
        }
    };

    const handleShareResult = () => {
        if (tryOnResult) {
            navigator.share({
                title: `Virtual Try-On: ${product?.title}`,
                text: `Check out how I look in this ${product?.brand} ${product?.category}!`,
                url: tryOnResult.imageUrl
            }).catch(() => {
                // Fallback: copy to clipboard
                navigator.clipboard.writeText(tryOnResult.imageUrl);
            });
        }
    };

    const handleDownloadResult = () => {
        if (tryOnResult) {
            const link = document.createElement('a');
            link.href = tryOnResult.imageUrl;
            link.download = `virtual-tryon-${product?.id}-${Date.now()}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-gray-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-700">
                    <div>
                        <h2 className="text-2xl font-bold text-white">Virtual Try-On</h2>
                        {product && (
                            <p className="text-gray-400">{product.brand} • {product.title}</p>
                        )}
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-white transition-colors"
                        aria-label="Close"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <div className="p-6">
                    {/* Results View */}
                    {tryOnResult ? (
                        <div className="space-y-6">
                            <div className="text-center">
                                <h3 className="text-xl font-semibold text-white mb-4">Your Virtual Try-On Result</h3>
                                <div className="relative inline-block">
                                    <img
                                        src={tryOnResult.imageUrl}
                                        alt="Virtual try-on result"
                                        className="max-w-full h-auto rounded-lg shadow-lg"
                                        style={{ maxHeight: '500px' }}
                                    />
                                </div>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex justify-center gap-4">
                                <button
                                    onClick={handleDownloadResult}
                                    className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg transition-colors"
                                >
                                    <Download className="w-4 h-4" />
                                    Download
                                </button>
                                <button
                                    onClick={handleShareResult}
                                    className="flex items-center gap-2 bg-pink-600 hover:bg-pink-700 text-white px-4 py-2 rounded-lg transition-colors"
                                >
                                    <Share2 className="w-4 h-4" />
                                    Share
                                </button>
                                <button
                                    onClick={() => {
                                        setUserPhoto(null);
                                        // Clear result by calling onGenerateTryOn with empty data
                                    }}
                                    className="flex items-center gap-2 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
                                >
                                    <RefreshCw className="w-4 h-4" />
                                    Try Again
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                            {/* User Photo Upload */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-white">Upload Your Photo</h3>

                                {userPhoto ? (
                                    <div className="relative">
                                        <img
                                            src={userPhoto}
                                            alt="User photo"
                                            className="w-full h-64 object-cover rounded-lg border border-gray-600"
                                        />
                                        <button
                                            onClick={() => setUserPhoto(null)}
                                            className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white p-1 rounded-full transition-colors"
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                    </div>
                                ) : (
                                    <div
                                        className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer ${
                                            dragActive
                                                ? "border-purple-500 bg-purple-900/20"
                                                : "border-gray-600 hover:border-purple-500"
                                        }`}
                                        onDragEnter={handleDrag}
                                        onDragLeave={handleDrag}
                                        onDragOver={handleDrag}
                                        onDrop={handleDrop}
                                        onClick={() => fileInputRef.current?.click()}
                                    >
                                        <div className="space-y-4">
                                            <div className="mx-auto w-16 h-16 bg-gray-700 rounded-full flex items-center justify-center">
                                                <Upload className="w-8 h-8 text-gray-400" />
                                            </div>
                                            <div>
                                                <p className="text-white font-medium">Upload your photo</p>
                                                <p className="text-gray-400 text-sm">
                                                    Drag & drop or click to browse
                                                </p>
                                                <p className="text-gray-500 text-xs mt-2">
                                                    For best results, use a clear full-body photo
                                                </p>
                                            </div>
                                        </div>
                                        <input
                                            ref={fileInputRef}
                                            type="file"
                                            className="hidden"
                                            accept="image/*"
                                            onChange={handleFileInput}
                                        />
                                    </div>
                                )}

                                {/* Camera Capture Button */}
                                <button
                                    onClick={() => {
                                        // TODO: Implement camera capture
                                        console.log("Camera capture not implemented yet");
                                    }}
                                    className="w-full flex items-center justify-center gap-2 bg-gray-700 hover:bg-gray-600 text-white py-3 rounded-lg transition-colors"
                                >
                                    <Camera className="w-4 h-4" />
                                    Take Photo
                                </button>
                            </div>

                            {/* Product Preview */}
                            <div className="space-y-4">
                                <h3 className="text-lg font-semibold text-white">Product to Try On</h3>

                                {product && (
                                    <div className="bg-gray-700/30 rounded-lg p-4">
                                        <div className="flex gap-4">
                                            <div className="w-20 h-24 bg-gradient-to-br from-purple-600 to-pink-600 rounded-lg flex items-center justify-center">
                                                <span className="text-2xl">
                                                    {product.category === 'Dresses' ? '👗' :
                                                     product.category === 'Shoes' ? '👠' : '👕'}
                                                </span>
                                            </div>
                                            <div className="flex-1">
                                                <h4 className="font-semibold text-white">{product.title}</h4>
                                                <p className="text-gray-400 text-sm">{product.brand}</p>
                                                <p className="text-purple-400 font-bold">€{product.price}</p>

                                                {/* Colors */}
                                                <div className="flex gap-1 mt-2">
                                                    {product.colors.slice(0, 3).map((color, index) => (
                                                        <div
                                                            key={index}
                                                            className="w-4 h-4 rounded-full border border-gray-500"
                                                            style={{ backgroundColor: color }}
                                                            title={color}
                                                        />
                                                    ))}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Generate Button */}
                    {!tryOnResult && (
                        <div className="mt-8 text-center">
                            <button
                                onClick={handleGenerateTryOn}
                                disabled={!userPhoto || !product || isGenerating}
                                className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 disabled:from-gray-600 disabled:to-gray-600 text-white px-8 py-3 rounded-lg font-semibold text-lg transition-all transform hover:scale-105 disabled:hover:scale-100 disabled:cursor-not-allowed flex items-center gap-3 mx-auto"
                            >
                                {isGenerating ? (
                                    <>
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                        Generating Virtual Try-On...
                                    </>
                                ) : (
                                    <>
                                        <Camera className="w-5 h-5" />
                                        Generate Virtual Try-On
                                    </>
                                )}
                            </button>

                            {(!userPhoto || !product) && (
                                <p className="text-gray-400 text-sm mt-2">
                                    {!userPhoto && "Please upload your photo "}
                                    {!userPhoto && !product && "and "}
                                    {!product && "select a product "}
                                    to continue
                                </p>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}