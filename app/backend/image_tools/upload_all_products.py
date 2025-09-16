#!/usr/bin/env python3
"""
Upload sample images for ALL products in the database.
This script creates image folders for all 15 products using the sample images.
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

def upload_images_for_all_products():
    """Upload images for all 15 products using the 5 sample images."""

    load_dotenv(override=True)

    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "zalankoimages")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "product-images")

    print("🚀 Uploading images for ALL products...")
    print("=" * 60)
    print(f"Storage Account: {storage_account}")
    print(f"Container: {container_name}")

    # Check Azure CLI
    if not check_azure_cli():
        print("\n❌ Azure CLI not found or not logged in.")
        print("Please install Azure CLI and run: az login")
        return False

    print("✅ Azure CLI authenticated")

    # Find sample images - try multiple possible paths
    possible_paths = [
        Path("../../sample_images"),  # Original relative path
        Path("../../../sample_images"),  # From backend/image_tools to root
        Path("/home/moalsayed/workspace/personal/kontrol/sample_images"),  # Absolute path
    ]

    images_dir = None
    for path in possible_paths:
        if path.exists():
            images_dir = path
            break

    if images_dir is None:
        print(f"❌ Sample images not found in any of these locations:")
        for path in possible_paths:
            print(f"  - {path}")
        return False

    sample_files = list(images_dir.glob("*.jpg"))

    if not sample_files:
        print(f"❌ No images found in {images_dir}")
        return False

    print(f"\n📁 Found {len(sample_files)} sample images:")
    for img in sample_files:
        print(f"  - {img.name}")

    # Load product data - try multiple possible paths
    possible_data_paths = [
        Path("../../data/clothing_data.json"),  # Original relative path
        Path("../../../data/clothing_data.json"),  # From backend/image_tools to root
        Path("/home/moalsayed/workspace/personal/kontrol/data/clothing_data.json"),  # Absolute path
    ]

    data_file = None
    for path in possible_data_paths:
        if path.exists():
            data_file = path
            break

    if data_file is None:
        print("❌ Product data file not found in any of these locations:")
        for path in possible_data_paths:
            print(f"  - {path}")
        return False

    with open(data_file, 'r') as f:
        products = json.load(f)
        product_ids = [p["id"] for p in products]

    print(f"\n📦 Will upload images for {len(product_ids)} products:")
    for product_id in product_ids:
        print(f"  - {product_id}")

    uploaded_count = 0
    failed_uploads = []

    # Upload images for each product
    for i, product_id in enumerate(product_ids):
        print(f"\n📤 Product {product_id} ({i+1}/{len(product_ids)}):")

        # Use different images for variety (cycle through the 5 sample images)
        for j, img_file in enumerate(sample_files):
            blob_name = f"{product_id}/{img_file.name}"

            try:
                # Azure CLI upload command with Azure AD authentication
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
                print(f"    ✅ Uploaded")
                uploaded_count += 1

            except subprocess.CalledProcessError as e:
                print(f"    ❌ Failed: {e.stderr}")
                failed_uploads.append(f"{product_id}/{img_file.name}")
                continue

    print(f"\n🎉 Upload Summary:")
    print(f"  ✅ Successfully uploaded: {uploaded_count} images")
    if failed_uploads:
        print(f"  ❌ Failed uploads: {len(failed_uploads)}")
        for failed in failed_uploads[:5]:  # Show first 5 failures
            print(f"    - {failed}")
        if len(failed_uploads) > 5:
            print(f"    ... and {len(failed_uploads) - 5} more")

    print(f"\n🔗 Test URLs:")
    print(f"  CLO001: https://{storage_account}.blob.core.windows.net/{container_name}/CLO001/fashion_model_1.jpg")
    print(f"  CLO015: https://{storage_account}.blob.core.windows.net/{container_name}/CLO015/fashion_model_1.jpg")

    return len(failed_uploads) == 0

if __name__ == "__main__":
    success = upload_images_for_all_products()
    exit(0 if success else 1)