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
    
    # Find sample images
    images_dir = Path("sample_images")
    sample_files = list(images_dir.glob("*.jpg"))
    
    if not sample_files:
        print(f"❌ No images found in {images_dir}")
        return False
    
    print(f"\n📁 Found {len(sample_files)} sample images")
    
    # Load product data for first few products
    data_file = Path("../../data/clothing_data.json")
    if data_file.exists():
        with open(data_file, 'r') as f:
            products = json.load(f)
            product_ids = [p["id"] for p in products[:5]]  # First 5 products
    else:
        product_ids = ["CLO001", "CLO002", "CLO003", "CLO004", "CLO005"]
    
    print(f"📦 Will upload images for {len(product_ids)} products")
    
    uploaded_count = 0
    
    # Upload images for each product
    for i, product_id in enumerate(product_ids):
        print(f"\n📤 Product {product_id} ({i+1}/{len(product_ids)}):")
        
        # Upload 2-3 images per product
        for j, img_file in enumerate(sample_files[:3]):  # Use first 3 images
            blob_name = f"{product_id}/{img_file.name}"
            
            try:
                # Azure CLI upload command with AD authentication
                cmd = [
                    'az', 'storage', 'blob', 'upload',
                    '--account-name', storage_account,
                    '--container-name', container_name,
                    '--name', blob_name,
                    '--file', str(img_file),
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
    print(f"https://{storage_account}.blob.core.windows.net/{container_name}/CLO001/fashion_model_1.jpg")
    
    return True

if __name__ == "__main__":
    upload_with_azure_cli()