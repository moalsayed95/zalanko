"""
Improved RAG Tools for Zalanko Fashion Assistant.
Production-ready implementation with proper error handling, logging, and validation.
"""

import base64
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import aiohttp
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential

from search_manager import SearchManager
from rtmt import RTMiddleTier, Tool, ToolResult, ToolResultDirection
from utils.logger import get_logger
from exceptions import ExternalServiceError, VirtualTryOnError

# Import virtual_tryon_service with fallback
try:
    from services.virtual_tryon_service import virtual_tryon_service
except ImportError as e:
    logger = get_logger(__name__)
    logger.warning(f"Virtual try-on service not available: {e}")
    virtual_tryon_service = None

logger = get_logger(__name__)


async def fetch_image_from_url(url: str) -> bytes:
    """
    Fetch image data from URL with proper error handling.

    Args:
        url: URL to fetch image from

    Returns:
        Image data as bytes

    Raises:
        ExternalServiceError: If image fetch fails
    """
    session = None
    try:
        logger.info(f"Fetching image from: {url}")
        session = aiohttp.ClientSession()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                image_data = await response.read()
                logger.info(f"Successfully fetched {len(image_data)} bytes from {url}")
                return image_data
            else:
                logger.error(f"Failed to fetch image: HTTP {response.status}")
                raise ExternalServiceError(f"Image fetch failed with HTTP {response.status}")
    except Exception as e:
        logger.error(f"Error fetching image from {url}: {e}")
        raise ExternalServiceError(f"Image fetch failed: {e}")
    finally:
        if session:
            await session.close()


# Tool schema definitions
_search_tool_schema = {
    "type": "function",
    "name": "search",
    "description": "Search for clothing items in the fashion catalog. Use this to find products based on style descriptions, brands, categories, or specific features.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query for clothing items (e.g., 'black leather jacket', 'summer dresses', 'Nike sneakers')"
            },
            "filters": {
                "type": "object",
                "properties": {
                    "brand": {"type": "string", "description": "Filter by brand (e.g., 'Nike', 'Zara')"},
                    "category": {"type": "string", "description": "Filter by category (e.g., 'T-Shirts & Tops', 'Outerwear')"},
                    "gender": {"type": "string", "description": "Filter by gender (men, women, unisex)"},
                    "max_price": {"type": "number", "description": "Maximum price filter"},
                    "min_price": {"type": "number", "description": "Minimum price filter"},
                    "color": {"type": "string", "description": "Filter by color"},
                    "size": {"type": "string", "description": "Filter by size"},
                    "material": {"type": "string", "description": "Filter by material (e.g., 'Cotton', 'Polyester', 'Leather')"},
                    "on_sale": {"type": "boolean", "description": "Filter for items on sale"}
                }
            }
        },
        "required": ["query"],
        "additionalProperties": False
    }
}

_get_product_details_schema = {
    "type": "function",
    "name": "get_product_details",
    "description": "Switch focus to and get detailed information about a specific clothing item. Use when user asks about 'that product', 'the blue one', 'the second option', or wants to see details of a specific product from the suggestions.",
    "parameters": {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "The ID of the clothing item to focus on and get details for (e.g., 'CLO001', 'CLO005')"
            }
        },
        "required": ["product_id"],
        "additionalProperties": False
    }
}

_add_to_cart_schema = {
    "type": "function",
    "name": "add_to_cart",
    "description": "Add a clothing item to the shopping cart with specified size and color. Use when users say 'add this to cart', 'buy this item', 'I want to purchase this', or similar phrases about the currently discussed product.",
    "parameters": {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "The ID of the clothing item to add to cart"
            },
            "size": {
                "type": "string",
                "description": "Selected size for the item"
            },
            "color": {
                "type": "string",
                "description": "Selected color for the item"
            },
            "quantity": {
                "type": "integer",
                "description": "Quantity to add to cart",
                "default": 1
            }
        },
        "required": ["product_id", "size", "color"],
        "additionalProperties": False
    }
}

_manage_wishlist_schema = {
    "type": "function",
    "name": "manage_wishlist",
    "description": "Add or remove items from the user's wishlist. Use when users say 'add this to favorites', 'save this item', 'I like this one', or 'remove from wishlist' about a specific product.",
    "parameters": {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "The ID of the clothing item to add/remove from wishlist"
            },
            "action": {
                "type": "string",
                "enum": ["add", "remove"],
                "description": "Whether to add or remove from wishlist"
            }
        },
        "required": ["product_id", "action"],
        "additionalProperties": False
    }
}

_navigate_page_schema = {
    "type": "function",
    "name": "navigate_page",
    "description": "Navigate to different sections of the fashion store (main, favorites, cart, messages).",
    "parameters": {
        "type": "object",
        "properties": {
            "destination": {
                "type": "string",
                "enum": ["main", "favorites", "cart", "messages", "home", "wishlist"],
                "description": "The page/section to navigate to (home/main for main page, wishlist/favorites for favorites page)"
            }
        },
        "required": ["destination"],
        "additionalProperties": False
    }
}

_get_recommendations_schema = {
    "type": "function",
    "name": "get_recommendations",
    "description": "Get personalized product recommendations based on user preferences or similar items.",
    "parameters": {
        "type": "object",
        "properties": {
            "based_on_product_id": {
                "type": "string",
                "description": "Get recommendations similar to this product ID"
            },
            "category": {
                "type": "string",
                "description": "Get recommendations from this category"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of recommendations",
                "default": 5
            }
        },
        "additionalProperties": False
    }
}

_update_style_preferences_schema = {
    "type": "function",
    "name": "update_style_preferences",
    "description": "Store and update the user's fashion preferences, sizes, and style choices for personalized recommendations.",
    "parameters": {
        "type": "object",
        "properties": {
            "preferred_brands": {
                "type": "array",
                "items": {"type": "string"},
                "description": "User's preferred clothing brands"
            },
            "preferred_categories": {
                "type": "array",
                "items": {"type": "string"},
                "description": "User's preferred clothing categories"
            },
            "sizes": {
                "type": "object",
                "description": "User's sizes for different categories (e.g., {'shirts': 'M', 'pants': '32', 'shoes': '10'})"
            },
            "budget_range": {
                "type": "object",
                "properties": {
                    "min": {"type": "number"},
                    "max": {"type": "number"}
                },
                "description": "User's budget range"
            },
            "style_preferences": {
                "type": "array",
                "items": {"type": "string"},
                "description": "User's style preferences (e.g., 'casual', 'formal', 'sporty')"
            },
            "colors": {
                "type": "array",
                "items": {"type": "string"},
                "description": "User's preferred colors"
            }
        },
        "additionalProperties": False
    }
}

_virtual_try_on_schema = {
    "type": "function",
    "name": "virtual_try_on",
    "description": "Generate virtual try-on images when users ask to 'try on', 'see how it looks on me', or 'show me wearing this'. Creates realistic visualizations of how clothing items would look on the user.",
    "parameters": {
        "type": "object",
        "properties": {
            "product_id": {
                "type": "string",
                "description": "The ID of the clothing item to try on"
            },
            "user_image": {
                "type": "string",
                "description": "Base64 encoded user image for virtual try-on (optional - if not provided, opens try-on modal)"
            }
        },
        "required": ["product_id"],
        "additionalProperties": False
    }
}

_get_application_state_schema = {
    "type": "function",
    "name": "get_application_state",
    "description": "Get the current state of the user's shopping session including favorites, cart items, and currently viewed product. Use this to stay synchronized with the user's actual application state.",
    "parameters": {
        "type": "object",
        "properties": {
            "include_details": {
                "type": "boolean",
                "description": "Whether to include detailed product information for items in favorites/cart",
                "default": False
            }
        },
        "additionalProperties": False
    }
}


def _validate_product_data(product: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize product data."""
    return {
        "id": product.get("id", "unknown_id"),
        "title": product.get("title", ""),
        "description": product.get("description", ""),
        "brand": product.get("brand", ""),
        "category": product.get("category", ""),
        "price": product.get("price", 0.0),
        "sale_price": product.get("sale_price"),
        "on_sale": product.get("on_sale", False),
        "colors": product.get("colors", []),
        "sizes": product.get("sizes", []),
        "materials": product.get("materials", []),
        "style_tags": product.get("style_tags", []),
        "ratings": product.get("ratings", {}),
        "images": product.get("images", []),
        "availability": product.get("availability", "")
    }


async def _search_tool(
    search_manager: SearchManager,
    image_service: Optional[Any],
    args: Dict[str, Any]
) -> ToolResult:
    """
    Search for clothing items with proper error handling.

    Args:
        search_manager: Search manager instance
        image_service: Image service instance (optional)
        args: Search arguments containing query and filters

    Returns:
        ToolResult with search results
    """
    try:
        query = args.get('query', '')
        filters = args.get('filters', {})

        if not query:
            logger.warning("Empty search query provided")
            return ToolResult({"error": "Search query is required"}, ToolResultDirection.TO_CLIENT)

        logger.info(f"Performing search for: '{query}' with filters: {filters}")

        # Use filters if provided, otherwise just do vector search
        if filters:
            results = await search_manager.search_with_vector_and_filters(
                text_query=query,
                k=10,
                brand=filters.get('brand'),
                category=filters.get('category'),
                gender=filters.get('gender'),
                max_price=filters.get('max_price'),
                min_price=filters.get('min_price'),
                color=filters.get('color'),
                size=filters.get('size'),
                material=filters.get('material'),
                on_sale=filters.get('on_sale')
            )
        else:
            results = await search_manager.search_by_embedding(query, k=10)

        products = []
        for r in results:
            product = _validate_product_data(r)

            # Enhance product with image URLs if image_service is available
            if image_service:
                try:
                    product = image_service.enhance_product_with_images(product)
                except Exception as e:
                    logger.warning(f"Failed to enhance product {product['id']} with images: {e}")

            products.append(product)

        # Log the search results
        product_ids = [p['id'] for p in products]
        logger.info(f"Search completed: Found {len(products)} products: {product_ids}")

        return ToolResult({"products": products}, ToolResultDirection.TO_CLIENT)

    except Exception as e:
        logger.error(f"Search tool failed: {e}")
        return ToolResult({"error": f"Search failed: {str(e)}"}, ToolResultDirection.TO_CLIENT)


async def _get_product_details_tool(args: Dict[str, Any]) -> ToolResult:
    """Get detailed information about a specific product."""
    try:
        product_id = args.get('product_id')
        if not product_id:
            logger.warning("Product ID not provided for get_product_details")
            return ToolResult({"error": "Product ID is required"}, ToolResultDirection.TO_CLIENT)

        logger.info(f"Switching main view to product: {product_id}")

        # Return the product ID in the format that triggers frontend highlighting
        result = {"id": product_id}

        return ToolResult(result, ToolResultDirection.TO_CLIENT)

    except Exception as e:
        logger.error(f"Get product details tool failed: {e}")
        return ToolResult({"error": f"Failed to get product details: {str(e)}"}, ToolResultDirection.TO_CLIENT)


async def _add_to_cart_tool(args: Dict[str, Any]) -> ToolResult:
    """Add item to shopping cart with validation."""
    try:
        product_id = args.get('product_id')
        size = args.get('size')
        color = args.get('color')
        quantity = args.get('quantity', 1)

        if not all([product_id, size, color]):
            logger.warning("Missing required parameters for add_to_cart")
            return ToolResult({"error": "Product ID, size, and color are required"}, ToolResultDirection.TO_CLIENT)

        logger.info(f"Adding to cart: {product_id} (size: {size}, color: {color}, qty: {quantity})")

        result = {
            "action": "add_to_cart",
            "product_id": product_id,
            "size": size,
            "color": color,
            "quantity": quantity,
            "timestamp": datetime.now().isoformat()
        }

        return ToolResult(result, ToolResultDirection.TO_CLIENT)

    except Exception as e:
        logger.error(f"Add to cart tool failed: {e}")
        return ToolResult({"error": f"Failed to add to cart: {str(e)}"}, ToolResultDirection.TO_CLIENT)


async def _manage_wishlist_tool(args: Dict[str, Any]) -> ToolResult:
    """Manage wishlist items with validation."""
    try:
        product_id = args.get('product_id')
        action = args.get('action')

        if not all([product_id, action]):
            logger.warning("Missing required parameters for manage_wishlist")
            return ToolResult({"error": "Product ID and action are required"}, ToolResultDirection.TO_CLIENT)

        if action not in ['add', 'remove']:
            logger.warning(f"Invalid wishlist action: {action}")
            return ToolResult({"error": "Action must be 'add' or 'remove'"}, ToolResultDirection.TO_CLIENT)

        logger.info(f"Managing wishlist: {action} product {product_id}")

        # Return the product ID in the format frontend expects for favorites
        result = {"favorite_id": product_id}

        return ToolResult(result, ToolResultDirection.TO_CLIENT)

    except Exception as e:
        logger.error(f"Manage wishlist tool failed: {e}")
        return ToolResult({"error": f"Failed to manage wishlist: {str(e)}"}, ToolResultDirection.TO_CLIENT)


async def _navigate_page_tool(args: Dict[str, Any]) -> ToolResult:
    """Navigate to different pages with validation."""
    try:
        destination = args.get('destination')
        if not destination:
            logger.warning("Destination not provided for navigate_page")
            return ToolResult({"error": "Destination is required"}, ToolResultDirection.TO_CLIENT)

        # Map common aliases to frontend-expected page names
        page_mapping = {
            "home": "main",
            "wishlist": "favorites",
            "main": "main",
            "favorites": "favorites",
            "cart": "cart",
            "messages": "messages"
        }

        mapped_destination = page_mapping.get(destination, destination)
        logger.info(f"Navigating to: {destination} -> {mapped_destination}")

        # Return the requested page to navigate to in the format frontend expects
        result = {"navigate_to": mapped_destination}

        return ToolResult(result, ToolResultDirection.TO_CLIENT)

    except Exception as e:
        logger.error(f"Navigate page tool failed: {e}")
        return ToolResult({"error": f"Failed to navigate: {str(e)}"}, ToolResultDirection.TO_CLIENT)


async def _get_recommendations_tool(args: Dict[str, Any]) -> ToolResult:
    """Get product recommendations with validation."""
    try:
        based_on_product_id = args.get('based_on_product_id')
        category = args.get('category')
        limit = args.get('limit', 5)

        logger.info(f"Getting recommendations (product: {based_on_product_id}, category: {category}, limit: {limit})")

        result = {
            "action": "get_recommendations",
            "based_on_product_id": based_on_product_id,
            "category": category,
            "limit": limit,
            "timestamp": datetime.now().isoformat()
        }

        return ToolResult(result, ToolResultDirection.TO_CLIENT)

    except Exception as e:
        logger.error(f"Get recommendations tool failed: {e}")
        return ToolResult({"error": f"Failed to get recommendations: {str(e)}"}, ToolResultDirection.TO_CLIENT)


async def _update_style_preferences_tool(args: Dict[str, Any]) -> ToolResult:
    """Update user style preferences with validation."""
    try:
        logger.info(f"Updating style preferences: {args}")

        result = {
            "action": "update_style_preferences",
            "preferences": args,
            "timestamp": datetime.now().isoformat()
        }

        return ToolResult(result, ToolResultDirection.TO_CLIENT)

    except Exception as e:
        logger.error(f"Update style preferences tool failed: {e}")
        return ToolResult({"error": f"Failed to update preferences: {str(e)}"}, ToolResultDirection.TO_CLIENT)


async def _virtual_try_on_tool(args: Dict[str, Any], image_service=None) -> ToolResult:
    """
    Virtual try-on tool with proper error handling.

    Args:
        args: Arguments containing product_id and optional user_image

    Returns:
        ToolResult with try-on results or error
    """
    try:
        product_id = args.get('product_id')
        user_image_b64 = args.get('user_image')

        if not product_id:
            logger.warning("Product ID not provided for virtual_try_on")
            return ToolResult({"error": "Product ID is required"}, ToolResultDirection.TO_CLIENT)

        logger.info(f"Starting virtual try-on for product: {product_id}")

        if not user_image_b64:
            # No user image provided, return action to open upload modal
            logger.info("No user image provided, opening try-on modal")
            result = {
                "action": "open_virtual_try_on_modal",
                "product_id": product_id,
                "message": f"I'll open the virtual try-on for this item. Please upload your photo to see how it looks on you!"
            }
            return ToolResult(result, ToolResultDirection.TO_CLIENT)

        try:
            # Decode base64 image
            user_image_data = base64.b64decode(user_image_b64)
            logger.info(f"Decoded user image: {len(user_image_data)} bytes")
        except Exception as e:
            logger.error(f"Failed to decode user image: {e}")
            raise VirtualTryOnError(f"Invalid image data: {e}")

        # Process virtual try-on
        try:
            if virtual_tryon_service is None:
                logger.error("Virtual try-on service not available")
                raise VirtualTryOnError("Virtual try-on service is not configured")

            # Fetch the actual product image from blob storage
            try:
                if image_service:
                    clothing_image_data = await image_service.get_product_image(product_id)
                    if not clothing_image_data:
                        logger.warning(f"Could not fetch image for product {product_id} from blob storage")
                        # Fallback to test image if blob storage fails
                        from pathlib import Path
                        test_image_path = Path(__file__).parent / "tests" / "virtual_tryon_tests" / "data" / "item.png"
                        if test_image_path.exists():
                            with open(test_image_path, "rb") as f:
                                clothing_image_data = f.read()
                            logger.info(f"Fallback: Using test clothing image: {len(clothing_image_data)} bytes")
                        else:
                            raise VirtualTryOnError(f"Product image not found for {product_id} and no fallback available")
                    else:
                        logger.info(f"Fetched product image from blob storage: {len(clothing_image_data)} bytes")
                else:
                    logger.warning("Image service not available")
                    raise VirtualTryOnError("Image service not configured")

                success, result_image, error = await virtual_tryon_service.generate_virtual_tryon(
                    person_image=user_image_data,
                    clothing_image=clothing_image_data,
                    product_info={'id': product_id}
                )
            except Exception as e:
                logger.error(f"Failed to fetch product image: {e}")
                raise VirtualTryOnError(f"Failed to get product image: {e}")

            if success and result_image:
                logger.info(f"Virtual try-on completed successfully for product {product_id}")

                # Convert result image bytes to base64 for frontend
                result_image_b64 = base64.b64encode(result_image).decode('utf-8')

                result = {
                    "action": "virtual_try_on_result",
                    "product_id": product_id,
                    "tryon_image": result_image_b64,
                    "timestamp": datetime.now().isoformat()
                }

                return ToolResult(result, ToolResultDirection.TO_CLIENT)
            else:
                logger.error(f"Virtual try-on failed for product {product_id}: {error}")
                raise VirtualTryOnError(f"Try-on generation failed: {error}")

        except Exception as e:
            logger.error(f"Virtual try-on processing failed: {e}")
            raise VirtualTryOnError(f"Try-on processing failed: {e}")

    except VirtualTryOnError as e:
        logger.error(f"Virtual try-on tool failed: {e}")
        return ToolResult({"error": str(e)}, ToolResultDirection.TO_CLIENT)
    except Exception as e:
        logger.error(f"Unexpected error in virtual try-on tool: {e}")
        return ToolResult({"error": f"Virtual try-on failed: {str(e)}"}, ToolResultDirection.TO_CLIENT)


async def _get_application_state_tool(args: Dict[str, Any]) -> ToolResult:
    """
    Get current application state for AI awareness.

    This tool allows the AI to query the current state of the user's session
    to stay synchronized with manual actions taken through the UI.

    Args:
        args: Tool arguments containing optional parameters

    Returns:
        ToolResult with instructions for AI to ask user about current state
    """
    try:
        include_details = args.get('include_details', False)

        logger.info(f"AI querying application state (include_details: {include_details})")

        # Since the backend doesn't have direct access to the frontend state,
        # inform the AI that it should ask the user about their current state
        response_text = """I need to check your current application state to give you accurate information. Let me ask you directly:

Could you please tell me:
1. What page are you currently on? (main catalog, favorites, cart, or messages)
2. Do you currently have any items in your favorites?
3. Do you have any items in your shopping cart?
4. Are you currently viewing a specific product?

This will help me stay synchronized with any changes you've made manually through the interface."""

        return ToolResult(response_text, ToolResultDirection.TO_SERVER)

    except Exception as e:
        logger.error(f"Get application state tool failed: {e}")
        return ToolResult(f"I encountered an error while trying to check the application state: {str(e)}", ToolResultDirection.TO_SERVER)


def attach_rag_tools(
    rtmt: RTMiddleTier,
    credentials: Union[AzureKeyCredential, DefaultAzureCredential],
    search_manager: SearchManager,
    image_service: Optional[Any] = None
) -> None:
    """
    Attach RAG tools to the real-time middleware tier with proper error handling.

    Args:
        rtmt: Real-time middleware tier instance
        credentials: Azure credentials
        search_manager: Search manager instance
        image_service: Image service instance (optional)
    """
    try:
        logger.info("Attaching RAG tools to RTMT")

        # Warm up credentials if needed
        if not isinstance(credentials, AzureKeyCredential):
            try:
                credentials.get_token("https://search.azure.com/.default")
                logger.debug("Azure credentials warmed up successfully")
            except Exception as e:
                logger.warning(f"Failed to warm up credentials: {e}")

        # Attach tools with error handling for each
        tools_to_attach = [
            ("search", _search_tool_schema, lambda args: _search_tool(search_manager, image_service, args)),
            ("get_product_details", _get_product_details_schema, _get_product_details_tool),
            ("add_to_cart", _add_to_cart_schema, _add_to_cart_tool),
            ("manage_wishlist", _manage_wishlist_schema, _manage_wishlist_tool),
            ("navigate_page", _navigate_page_schema, _navigate_page_tool),
            ("get_recommendations", _get_recommendations_schema, _get_recommendations_tool),
            ("update_style_preferences", _update_style_preferences_schema, _update_style_preferences_tool),
            ("virtual_try_on", _virtual_try_on_schema, lambda args: _virtual_try_on_tool(args, image_service)),
            ("get_application_state", _get_application_state_schema, _get_application_state_tool),
        ]

        for tool_name, schema, target_func in tools_to_attach:
            try:
                rtmt.tools[tool_name] = Tool(schema=schema, target=target_func)
                logger.debug(f"Successfully attached tool: {tool_name}")
            except Exception as e:
                logger.error(f"Failed to attach tool {tool_name}: {e}")
                raise

        logger.info(f"Successfully attached {len(tools_to_attach)} RAG tools to RTMT")

    except Exception as e:
        logger.error(f"Failed to attach RAG tools: {e}")
        raise