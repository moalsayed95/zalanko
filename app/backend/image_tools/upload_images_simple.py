#!/usr/bin/env python3
"""
Simple Azure Storage upload using Azure CLI authentication.
Run 'az login' first to authenticate.
"""

import os
import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def check_azure_cli():
    """Check if Azure CLI is installed and user is logged in."""
    try:
        result = subprocess.run(['az', 'account', 'show'], 
                              capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def upload_with_azure_cli():
    """Upload images using Azure CLI commands."""
    
    load_dotenv(override=True)
    
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "zalankoimages")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "product-images")
    
    print("🚀 Uploading sample images to Azure Storage (CLI method)...")
    print("=" * 60)
    print(f"Storage Account: {storage_account}")
    print(f"Container: {container_name}")
    
    # Check Azure CLI
    if not check_azure_cli():
        print("\n❌ Azure CLI not found or not logged in.")
        print("Please install Azure CLI and run: az login")
        return False
    
    print("✅ Azure CLI authenticated")
    
    # Find real product images
    images_dir = Path("../../../data/images")  # Corrected path
    product_images = list(images_dir.glob("*.png"))

    if not product_images:
        print(f"❌ No images found in {images_dir}")
        return False

    print(f"\n📁 Found {len(product_images)} product images")

    # Load product data to get all products
    data_file = Path("../../../data/clothing_data.json")
    if data_file.exists():
        with open(data_file, 'r') as f:
            products = json.load(f)
            product_ids = [p["id"] for p in products]  # All products
    else:
        # Extract product IDs from image filenames
        product_ids = [img.stem for img in product_images]

    print(f"📦 Will upload images for {len(product_ids)} products")
    print(f"📸 Available images: {[img.name for img in product_images]}")
    
    uploaded_count = 0
    
    # Upload images for each product
    for i, product_id in enumerate(product_ids):
        print(f"\n📤 Product {product_id} ({i+1}/{len(product_ids)}):")

        # Find matching image file for this product
        matching_image = None
        for img_file in product_images:
            if img_file.stem == product_id:
                matching_image = img_file
                break

        if not matching_image:
            print(f"  ⚠️ No image found for {product_id}")
            continue

        # Upload the product image directly (not in subfolder for simpler access)
        blob_name = f"{product_id}.png"

        try:
            # Azure CLI upload command with AD authentication
            cmd = [
                'az', 'storage', 'blob', 'upload',
                '--account-name', storage_account,
                '--container-name', container_name,
                '--name', blob_name,
                '--file', str(matching_image),
                '--overwrite', 'true',
                '--auth-mode', 'login'
            ]

            print(f"  Uploading {blob_name}...")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            blob_url = f"https://{storage_account}.blob.core.windows.net/{container_name}/{blob_name}"
            print(f"    ✅ {blob_url}")
            uploaded_count += 1

        except subprocess.CalledProcessError as e:
            print(f"    ❌ Failed: {e.stderr}")
            continue
    
    print(f"\n🎉 Upload complete! {uploaded_count} images uploaded.")
    print(f"\n🔗 Test URL example:")
    print(f"https://{storage_account}.blob.core.windows.net/{container_name}/CLO001.png")
    
    return True

if __name__ == "__main__":
    upload_with_azure_cli()