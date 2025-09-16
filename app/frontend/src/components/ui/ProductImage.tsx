import React, { useState } from 'react';

interface ProductImageProps {
  src?: string;
  alt: string;
  className?: string;
  fallbackIcon?: React.ReactNode;
  category?: string;
}

// Generate category-based fallback icons
const getCategoryIcon = (category?: string) => {
  switch (category?.toLowerCase()) {
    case 'shoes':
      return <span className="text-6xl">👠</span>;
    case 'dresses':
      return <span className="text-6xl">👗</span>;
    case 'outerwear':
    case 'blazers & suits':
      return <span className="text-6xl">🧥</span>;
    case 'sportswear':
      return <span className="text-6xl">👕</span>;
    case 'jeans & trousers':
      return <span className="text-6xl">👖</span>;
    case 'knitwear':
      return <span className="text-6xl">🧶</span>;
    case 'shirts':
    case 't-shirts & tops':
    default:
      return <span className="text-6xl">👕</span>;
  }
};

const ProductImage: React.FC<ProductImageProps> = ({
  src,
  alt,
  className = "w-full h-full object-cover",
  fallbackIcon,
  category
}) => {
  const [imageError, setImageError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const handleImageError = () => {
    setImageError(true);
    setIsLoading(false);
  };

  const handleImageLoad = () => {
    setIsLoading(false);
  };

  // If no src provided or image error, show fallback
  if (!src || imageError) {
    return (
      <div className={`${className} bg-gradient-to-br from-gray-700 to-gray-600 rounded-lg flex items-center justify-center`}>
        {fallbackIcon || getCategoryIcon(category)}
      </div>
    );
  }

  return (
    <div className="relative w-full h-full">
      {/* Loading placeholder */}
      {isLoading && (
        <div className="absolute inset-0 bg-gradient-to-br from-gray-700 to-gray-600 rounded-lg flex items-center justify-center animate-pulse">
          <div className="w-8 h-8 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}

      {/* Actual image */}
      <img
        src={src}
        alt={alt}
        className={className}
        onError={handleImageError}
        onLoad={handleImageLoad}
        style={{ display: imageError ? 'none' : 'block' }}
      />
    </div>
  );
};

export default ProductImage;