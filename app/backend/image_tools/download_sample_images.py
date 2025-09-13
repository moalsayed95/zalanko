#!/usr/bin/env python3
"""
Download sample fashion images for testing the image integration.
Uses Unsplash API to get high-quality fashion placeholder images.
"""

import os
import requests
from pathlib import Path
import time

def download_sample_images():
    """Download sample fashion images for testing."""
    
    # Create images directory
    images_dir = Path("sample_images")
    images_dir.mkdir(exist_ok=True)
    
    print("📸 Downloading sample fashion images...")
    print("=" * 50)
    
    # Sample fashion images from Unsplash (free to use)
    # Using specific fashion-related image IDs for consistent results
    sample_images = [
        {
            "url": "https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?w=400&h=600&fit=crop&crop=center",
            "filename": "fashion_model_1.jpg",
            "description": "Fashion model in elegant dress"
        },
        {
            "url": "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=400&h=600&fit=crop&crop=center", 
            "filename": "fashion_model_2.jpg",
            "description": "Casual fashion style"
        },
        {
            "url": "https://images.unsplash.com/photo-1445205170230-053b83016050?w=400&h=600&fit=crop&crop=center",
            "filename": "fashion_accessories.jpg", 
            "description": "Fashion accessories and clothing"
        },
        {
            "url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=400&h=600&fit=crop&crop=center",
            "filename": "fashion_boutique.jpg",
            "description": "Fashion boutique display"
        },
        {
            "url": "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=400&h=600&fit=crop&crop=center",
            "filename": "fashion_portrait.jpg", 
            "description": "Fashion portrait style"
        }
    ]
    
    downloaded_files = []
    
    for i, image_info in enumerate(sample_images, 1):
        url = image_info["url"]
        filename = image_info["filename"]
        description = image_info["description"]
        filepath = images_dir / filename
        
        print(f"📥 Downloading {i}/5: {description}")
        print(f"   URL: {url}")
        print(f"   File: {filename}")
        
        try:
            # Add headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            downloaded_files.append(str(filepath))
            print(f"   ✅ Downloaded successfully ({len(response.content)} bytes)")
            
        except requests.RequestException as e:
            print(f"   ❌ Failed to download: {e}")
            continue
        
        # Small delay to be respectful to the server
        time.sleep(1)
        print()
    
    print("=" * 50)
    print(f"✅ Download complete! {len(downloaded_files)} images ready.")
    print("\nDownloaded files:")
    for file_path in downloaded_files:
        file_size = os.path.getsize(file_path) / 1024  # KB
        print(f"  • {os.path.basename(file_path)} ({file_size:.1f} KB)")
    
    print(f"\n📁 Files saved to: {images_dir.absolute()}")
    print("\n🎯 Next steps:")
    print("1. Run the Azure Storage upload script")
    print("2. Update the clothing data with image references")
    print("3. Test the frontend image display")
    
    return downloaded_files

if __name__ == "__main__":
    download_sample_images()