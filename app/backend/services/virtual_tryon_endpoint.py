"""
Test endpoint for virtual try-on functionality.
This allows direct testing of the virtual try-on pipeline.
"""

import json
import logging
import os
import sys
from pathlib import Path
from aiohttp import web

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from ragtools import _virtual_try_on_tool
from search_manager import SearchManager
from image_tools.image_utils import ImageService

logger = logging.getLogger("virtual_tryon_endpoint")


async def virtual_tryon_handler(request):
    """Direct endpoint to test virtual try-on functionality."""
    try:
        # Parse request body
        data = await request.json()
        product_id = data.get('product_id')
        person_image_base64 = data.get('person_image_base64')
        user_message = data.get('user_message', '')

        logger.info(f"🎬 Virtual try-on endpoint called for product: {product_id}")

        if not product_id or not person_image_base64:
            return web.json_response({
                'error': 'Missing product_id or person_image_base64'
            }, status=400)

        # Initialize services (same as in main app)
        search_manager = SearchManager(
            service_name=os.getenv("AZURE_SEARCH_SERVICE_NAME"),
            api_key=os.getenv("AZURE_SEARCH_API_KEY"),
            index_name=os.getenv("AZURE_SEARCH_INDEX"),
            embedding_model=os.getenv("AZURE_OPENAI_EMBEDDING_MODEL"),
        )

        image_service = ImageService(
            storage_account=os.getenv("AZURE_STORAGE_ACCOUNT_NAME", "zalankoimages"),
            container=os.getenv("AZURE_STORAGE_CONTAINER_NAME", "product-images")
        )

        # Call the virtual try-on tool directly
        args = {
            'product_id': product_id,
            'person_image_base64': person_image_base64,
            'user_message': user_message
        }

        result = await _virtual_try_on_tool(search_manager, image_service, args)

        # Convert ToolResult to JSON response
        if hasattr(result, 'text'):
            response_data = json.loads(result.to_text()) if isinstance(result.text, str) else result.text
        else:
            response_data = {'error': 'Invalid response from virtual try-on tool'}

        logger.info(f"✅ Virtual try-on endpoint completed: {response_data.get('action', 'unknown')}")

        return web.json_response(response_data, headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        })

    except Exception as e:
        logger.error(f"❌ Virtual try-on endpoint error: {e}")
        import traceback
        logger.error(f"📚 Traceback: {traceback.format_exc()}")

        return web.json_response({
            'error': f'Server error: {str(e)}'
        }, status=500, headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        })


async def virtual_tryon_options_handler(request):
    """Handle CORS preflight OPTIONS requests."""
    return web.Response(
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        }
    )

async def virtual_tryon_result_handler(request):
    """Serve virtual try-on result images."""
    try:
        filename = request.match_info['filename']

        # Security: only allow specific pattern
        if not filename.startswith('tryon_') or not filename.endswith('.png'):
            return web.Response(status=404, text="File not found")

        # Get the file path
        results_dir = Path("virtual_tryon_results")
        file_path = results_dir / filename

        if not file_path.exists():
            logger.warning(f"Virtual try-on result file not found: {file_path}")
            return web.Response(status=404, text="File not found")

        logger.info(f"📥 Serving virtual try-on result: {filename} ({file_path.stat().st_size} bytes)")

        return web.FileResponse(
            file_path,
            headers={
                'Content-Type': 'image/png',
                'Access-Control-Allow-Origin': '*',
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        logger.error(f"❌ Error serving virtual try-on result: {e}")
        return web.Response(status=500, text="Server error")

def setup_virtual_tryon_routes(app):
    """Add virtual try-on test routes to the app."""
    app.router.add_post('/api/virtual-tryon', virtual_tryon_handler)
    app.router.add_options('/api/virtual-tryon', virtual_tryon_options_handler)
    app.router.add_get('/api/virtual-tryon-results/{filename}', virtual_tryon_result_handler)
    logger.info("🔗 Virtual try-on test endpoint added: POST /api/virtual-tryon")
    logger.info("🔗 Virtual try-on OPTIONS endpoint added: OPTIONS /api/virtual-tryon")
    logger.info("🔗 Virtual try-on results endpoint added: GET /api/virtual-tryon-results/{filename}")