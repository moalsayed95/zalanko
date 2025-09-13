#!/usr/bin/env python3
"""
Test script for ImageService functionality.
Tests image URL generation without requiring full backend setup.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the path so we can import our modules
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from image_utils import ImageService

def test_image_service():
    """Test ImageService functionality with sample data."""
    
    print("🧪 Testing ImageService...")
    print("=" * 50)
    
    # Initialize ImageService with test storage account
    image_service = ImageService(
        storage_account="zalankoimages",
        container="product-images"
    )
    
    print(f"✓ ImageService initialized")
    print(f"  Storage Account: {image_service.storage_account}")
    print(f"  Container: {image_service.container}")
    print(f"  Base URL: {image_service.base_url}")
    print()
    
    # Test image URL generation
    print("📸 Testing image URL generation...")
    product_id = "CLO001"
    image_filenames = ["tshirt_white_front.jpg", "tshirt_white_back.jpg"]
    
    image_urls = image_service.get_image_urls(product_id, image_filenames)
    
    print(f"Product ID: {product_id}")
    print(f"Image filenames: {image_filenames}")
    print(f"Generated URLs:")
    for i, url in enumerate(image_urls, 1):
        print(f"  {i}. {url}")
    print()
    
    # Test product enhancement
    print("🔧 Testing product enhancement...")
    sample_product = {
        "id": "CLO001",
        "title": "Essential Cotton T-Shirt",
        "brand": "Zara",
        "price": 19.99,
        "images": ["tshirt_white_front.jpg", "tshirt_white_back.jpg"]
    }
    
    print("Original product:")
    print(f"  ID: {sample_product['id']}")
    print(f"  Images: {sample_product['images']}")
    
    enhanced_product = image_service.enhance_product_with_images(sample_product)
    
    print("Enhanced product:")
    print(f"  Images (original): {enhanced_product['images']}")
    print(f"  ImageUrls (new): {enhanced_product.get('imageUrls', [])}")
    print()
    
    # Test edge cases
    print("🎯 Testing edge cases...")
    
    # Empty images list
    empty_product = {"id": "CLO002", "images": []}
    enhanced_empty = image_service.enhance_product_with_images(empty_product)
    print(f"✓ Empty images: {enhanced_empty.get('imageUrls', [])}")
    
    # No images field
    no_images_product = {"id": "CLO003", "title": "Product without images"}
    enhanced_no_images = image_service.enhance_product_with_images(no_images_product)
    print(f"✓ No images field: {enhanced_no_images.get('imageUrls', [])}")
    
    # Test batch enhancement
    print("📦 Testing batch enhancement...")
    products_batch = [
        {"id": "CLO001", "images": ["img1.jpg", "img2.jpg"]},
        {"id": "CLO002", "images": ["img3.jpg"]},
        {"id": "CLO003", "images": []}
    ]
    
    enhanced_batch = image_service.enhance_products_batch(products_batch)
    print(f"✓ Enhanced {len(enhanced_batch)} products in batch")
    for product in enhanced_batch:
        print(f"  {product['id']}: {len(product.get('imageUrls', []))} URLs")
    
    print()
    print("✅ All tests completed successfully!")
    print("The ImageService is ready for integration.")

if __name__ == "__main__":
    test_image_service()