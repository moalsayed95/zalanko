# Image Tools Directory

This directory contains all image-related utilities and scripts for the Zalanko fashion e-commerce application.

## 📁 Files Overview

### Core Service
- **`image_utils.py`** - Main ImageService class for Azure Storage integration
  - Converts image filenames to full Azure Storage URLs
  - Enhances product data with imageUrls field
  - Used by the main application in `app.py` and `ragtools.py`

### Setup & Testing Scripts
- **`download_sample_images.py`** - Downloads sample fashion images from Unsplash
  - Run once to get placeholder images for testing
  - Creates `sample_images/` directory with 5 fashion photos

- **`upload_images_simple.py`** - Uploads sample images to Azure Storage
  - Uses Azure CLI authentication (`--auth-mode login`)
  - Organizes images by product ID in storage container
  - Requires "Storage Blob Data Contributor" role

- **`test_image_service.py`** - Tests ImageService functionality
  - Verifies URL generation and product enhancement
  - Run to validate service before integration

### Data Management
- **`update_clothing_data.py`** - Updates clothing_data.json with image references
  - Creates backup of original data
  - Assigns sample images to all products
  - Updates the images field with proper filenames

## 🚀 Usage Workflow

1. **Download sample images**:
   ```bash
   python3 download_sample_images.py
   ```

2. **Upload to Azure Storage**:
   ```bash
   python3 upload_images_simple.py
   ```

3. **Update product data**:
   ```bash
   python3 update_clothing_data.py
   ```

4. **Test the service**:
   ```bash
   python3 test_image_service.py
   ```

## 🔗 Integration

The ImageService is automatically integrated into the main application:
- **`app.py`** initializes the service
- **`ragtools.py`** enhances search results with imageUrls
- Frontend receives product data with both `images` (filenames) and `imageUrls` (full URLs)

## 📦 Generated URL Format

```
https://zalankoimages.blob.core.windows.net/product-images/{product_id}/{filename}
```

Example:
```
https://zalankoimages.blob.core.windows.net/product-images/CLO001/fashion_model_1.jpg
```