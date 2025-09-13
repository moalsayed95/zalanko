#!/usr/bin/env python3
"""
Update clothing_data.json with proper image filenames that correspond to uploaded images.
This script modifies the existing data to reference the uploaded sample images.
"""

import json
import shutil
from pathlib import Path
from typing import List, Dict, Any

def backup_original_data():
    """Create a backup of the original data file."""
    # Use absolute path to avoid relative path issues
    script_dir = Path(__file__).parent
    data_file = script_dir / "../../../data/clothing_data.json"
    data_file = data_file.resolve()  # Convert to absolute path
    backup_file = data_file.with_suffix('.json.backup')
    
    if data_file.exists() and not backup_file.exists():
        shutil.copy2(data_file, backup_file)
        print(f"✅ Backup created: {backup_file}")
    return data_file

def update_clothing_data():
    """Update clothing data with sample image references."""
    
    print("🔄 Updating clothing_data.json with sample images...")
    print("=" * 60)
    
    # Backup original data
    data_file = backup_original_data()
    
    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return False
    
    # Load existing data
    with open(data_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"📦 Loaded {len(products)} products from {data_file}")
    
    # Sample image filenames that we uploaded
    sample_image_files = [
        "fashion_model_1.jpg",
        "fashion_model_2.jpg", 
        "fashion_accessories.jpg",
        "fashion_boutique.jpg",
        "fashion_portrait.jpg"
    ]
    
    print(f"🖼️  Available sample images: {len(sample_image_files)}")
    for img in sample_image_files:
        print(f"   • {img}")
    
    updated_count = 0
    
    # Update each product with sample images
    for i, product in enumerate(products):
        product_id = product.get("id", f"UNKNOWN_{i}")
        
        # Assign 2-3 images per product for variety
        if i % 3 == 0:
            # Every 3rd product gets first 3 images
            assigned_images = sample_image_files[:3]
        elif i % 3 == 1:
            # Next product gets different combination
            assigned_images = [sample_image_files[1], sample_image_files[3], sample_image_files[4]]
        else:
            # Remaining products get another combination
            assigned_images = [sample_image_files[0], sample_image_files[2], sample_image_files[4]]
        
        # Update the images field
        product["images"] = assigned_images
        updated_count += 1
        
        if i < 5:  # Show first 5 as examples
            print(f"   {product_id}: {len(assigned_images)} images -> {assigned_images}")
    
    # Save updated data
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Updated {updated_count} products with sample images")
    print(f"💾 Data saved to: {data_file}")
    
    # Show summary
    print(f"\n📊 Summary:")
    total_image_references = sum(len(p.get("images", [])) for p in products)
    print(f"   • Products updated: {updated_count}")
    print(f"   • Total image references: {total_image_references}")
    print(f"   • Average images per product: {total_image_references/updated_count:.1f}")
    
    print(f"\n🎯 Next steps:")
    print(f"1. Restart the backend server to load new data")
    print(f"2. Test search API - should now include imageUrls in responses") 
    print(f"3. Update frontend components to display the images")
    print(f"4. Test end-to-end image loading")
    
    return True

def verify_data_structure():
    """Verify the updated data structure looks correct."""
    data_file = Path("../../data/clothing_data.json")
    
    if not data_file.exists():
        return False
    
    with open(data_file, 'r', encoding='utf-8') as f:
        products = json.load(f)
    
    print(f"\n🔍 Verification of updated data:")
    print(f"   • Total products: {len(products)}")
    
    # Check first few products
    for i, product in enumerate(products[:3]):
        images = product.get("images", [])
        print(f"   • {product.get('id', 'NO_ID')}: {len(images)} images")
        for img in images:
            print(f"     - {img}")
    
    return True

if __name__ == "__main__":
    if update_clothing_data():
        verify_data_structure()