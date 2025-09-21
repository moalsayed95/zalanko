"""
Image proxy service to serve authenticated Azure Storage blob images.
Provides secure image access without exposing storage account keys.
"""

import os
from typing import Optional
from aiohttp import web, ClientSession
from azure.identity import DefaultAzureCredential
from azure.storage.blob.aio import BlobServiceClient
from dotenv import load_dotenv

load_dotenv(override=True)

class ImageProxy:
    """Proxy service for serving authenticated blob storage images."""
    
    def __init__(self):
        self.storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "zalankoimages")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "product-images")
        
        # Use Azure AD authentication
        self.credential = DefaultAzureCredential()
        account_url = f"https://{self.storage_account}.blob.core.windows.net"
        self.blob_service_client = BlobServiceClient(account_url, credential=self.credential)
    
    async def get_blob_stream(self, product_id: str, filename: str):
        """Get blob data stream with authentication."""
        try:
            blob_name = filename
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            )
            
            # Download blob data
            blob_data = await blob_client.download_blob()
            content = await blob_data.readall()
            
            # Get content type from blob properties
            properties = await blob_client.get_blob_properties()
            content_type = properties.content_settings.content_type or "image/jpeg"
            
            return content, content_type
            
        except Exception as e:
            print(f"Error fetching blob {filename}: {e}")
            return None, None
    
    async def cleanup(self):
        """Clean up the blob service client."""
        if hasattr(self.blob_service_client, 'close'):
            await self.blob_service_client.close()


# Global instance
image_proxy = ImageProxy()

async def serve_product_image(request):
    """Serve product image through authenticated proxy."""
    product_id = request.match_info.get('product_id')
    filename = request.match_info.get('filename')
    
    if not product_id or not filename:
        return web.Response(text="Missing product_id or filename", status=400)
    
    # Security: basic validation
    if '..' in filename or '/' in filename:
        return web.Response(text="Invalid filename", status=400)
    
    content, content_type = await image_proxy.get_blob_stream(product_id, filename)
    
    if content is None:
        return web.Response(text="Image not found", status=404)
    
    # Return image with appropriate headers
    return web.Response(
        body=content,
        content_type=content_type,
        headers={
            'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
            'Access-Control-Allow-Origin': '*'  # Allow frontend access
        }
    )

def setup_image_routes(app):
    """Add image proxy routes to the app."""
    app.router.add_get('/api/images/{product_id}/{filename}', serve_product_image)
    
    # Cleanup on app shutdown
    async def cleanup_image_proxy(app):
        await image_proxy.cleanup()
    
    app.on_cleanup.append(cleanup_image_proxy)