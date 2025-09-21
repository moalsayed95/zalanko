"""
Image utility service for handling product image URLs and Azure Storage integration.
"""
import os
import aiohttp
from typing import List, Dict, Any, Optional


class ImageService:
    """Service for converting product image filenames to full Azure Storage URLs."""
    
    def __init__(self, storage_account: Optional[str] = None, container: Optional[str] = None):
        """
        Initialize ImageService with Azure Storage configuration.
        
        Args:
            storage_account: Azure Storage account name
            container: Container name for product images
        """
        self.storage_account = storage_account or os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "zalankoimages")
        self.container = container or os.getenv("AZURE_STORAGE_CONTAINER_NAME", "product-images")
        self.base_url = f"https://{self.storage_account}.blob.core.windows.net/{self.container}"
        
    def get_image_urls(self, product_id: str, image_filenames: List[str]) -> List[str]:
        """
        Convert image filenames to authenticated backend proxy URLs.
        
        Args:
            product_id: Unique product identifier
            image_filenames: List of image filenames
            
        Returns:
            List of backend proxy URLs for authenticated image access
        """
        if not image_filenames or not product_id:
            return []
            
        # Use backend proxy URLs instead of direct Azure Storage URLs
        backend_base = os.getenv("BACKEND_URL", "http://localhost:8765")
        return [
            f"{backend_base}/api/images/{product_id}/{filename}"
            for filename in image_filenames
            if filename and filename.strip()
        ]
    
    def enhance_product_with_images(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add imageUrls field to product data while preserving original images field.
        
        Args:
            product: Product dictionary from search results
            
        Returns:
            Enhanced product dictionary with imageUrls field
        """
        # Create a copy to avoid mutating the original
        enhanced_product = product.copy()
        
        # Add imageUrls field if images exist
        if 'images' in product and product['images']:
            enhanced_product['imageUrls'] = self.get_image_urls(
                product.get('id', ''), 
                product['images']
            )
        else:
            enhanced_product['imageUrls'] = []
            
        return enhanced_product
    
    def enhance_products_batch(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance multiple products with image URLs in batch.
        
        Args:
            products: List of product dictionaries
            
        Returns:
            List of enhanced product dictionaries with imageUrls
        """
        return [self.enhance_product_with_images(product) for product in products]
    
    def get_placeholder_image_url(self) -> str:
        """
        Get URL for placeholder image when no product images are available.
        
        Returns:
            URL to placeholder image
        """
        return f"{self.base_url}/placeholders/no-image.jpg"
    
    def validate_storage_config(self) -> bool:
        """
        Validate that storage configuration is properly set.

        Returns:
            True if configuration is valid
        """
        return bool(self.storage_account and self.container)

    async def get_product_image(self, product_id: str) -> Optional[bytes]:
        """
        Fetch the actual image bytes for a product for virtual try-on.

        Args:
            product_id: The product ID to fetch image for

        Returns:
            Image bytes if found, None otherwise
        """
        try:
            # Handle default products with specific image mappings
            default_product_images = {
                "CLO_DEFAULT_001": "placeholder_tshirt.jpg",
                "CLO_DEFAULT_002": "placeholder_jacket.jpg",
                "CLO_DEFAULT_003": "placeholder_dress.jpg",
                "CLO_DEFAULT_004": "placeholder_sneakers.jpg",
                "CLO_DEFAULT_005": "placeholder_blazer.jpg"
            }

            # Determine image filename
            if product_id in default_product_images:
                image_filename = default_product_images[product_id]
            else:
                # For regular products, assume ID-based naming
                image_filename = f"{product_id}.jpg"

            # Try to fetch the image
            image_url = f"{self.base_url}/{image_filename}"

            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        return await response.read()

                # If specific image not found, try fallbacks
                fallback_images = ["fashion_model_1.jpg", "fashion_model_2.jpg", "fashion_accessories.jpg"]
                for fallback in fallback_images:
                    fallback_url = f"{self.base_url}/{fallback}"
                    async with session.get(fallback_url) as alt_response:
                        if alt_response.status == 200:
                            return await alt_response.read()

                return None
        except Exception as e:
            print(f"Error fetching product image for {product_id}: {e}")
            return None


# Global instance for easy importing
image_service = ImageService()